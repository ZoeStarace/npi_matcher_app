import streamlit as st
import pandas as pd
import requests
from rapidfuzz import fuzz

# -------------------- CONFIG & CONSTANTS --------------------
st.set_page_config(page_title="NPI Matcher", layout="wide")
REQUIRED_COLUMNS = {"First Name", "Last Name"}

MATCH_STRATEGIES = [
    ("Best: Full first and last name match", "Best"),
    ("Good: Last name match + fuzzy first name", "Good"),
    ("Potential: Last name only match", "Potential"),
    ("Limited Potential: First name only match", "Limited Potential"),
]

def clear_results():
    if 'result_df' in st.session_state:
        del st.session_state['result_df']

def split_first_and_middle(df):
    # Only split if Middle Name is empty and First Name contains a space
    mask = (df["Middle Name"].fillna("") == "") & df["First Name"].astype(str).str.contains(r"\s")
    for idx in df[mask].index:
        parts = str(df.at[idx, "First Name"]).strip().split()
        if len(parts) > 1:
            df.at[idx, "First Name"] = " ".join(parts[:-1])
            df.at[idx, "Middle Name"] = parts[-1]
    return df

# -------------------- SIDEBAR: APP INFO & OPTIONS --------------------
with st.sidebar:
    st.title("NPI Matcher Settings")
    st.markdown("Configure your matching preferences below.")

    US_STATES = [
        "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "IA", "ID", "IL", "IN", "KS", "KY",
        "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH",
        "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY"
    ]
    state = st.multiselect(
        "Limit search to state(s):",
        options=US_STATES,
        default=[],
        key="state",
        on_change=clear_results
    )

    limit = st.number_input("Max matches per provider", min_value=1, max_value=50, value=10, key="limit", on_change=clear_results)
    st.markdown("**Match strictness options:**")
    st.markdown("""
- **Best:** Full first and last name match  
- **Good:** Last name match + fuzzy first name  
- **Potential:** Last name only match  
- **Limited Potential:** First name only match
    """)
    slider_labels = ["Best", "Good", "Potential", "Limited Potential"]
    selected_label = st.select_slider(
        "Slide to adjust match strictness:",
        options=slider_labels,
        value=slider_labels[0],
        help="Left: Only exact matches. Right: More possible matches, but less strict.",
        key="selected_label",
        on_change=clear_results
    )
    st.markdown(f"**Selected:** {selected_label}")
    label_map = {
        "Best": "Best: Full first and last name match",
        "Good": "Good: Last name match + fuzzy first name",
        "Potential": "Potential: Last name only match",
        "Limited Potential": "Limited Potential: First name only match"
    }
    search_type = label_map[selected_label]
    st.markdown("---")
    st.markdown("**Need help?**\n- Download the sample template\n- Ensure your file has the required columns\n- Adjust matching options as needed\n - Click **Run Matching** to start the process\n - Refine results using filters\n\n")

# -------------------- HEADER & INSTRUCTIONS --------------------
st.markdown(
    "<h1 style='text-align: center; color: #4F8BF9;'>🔍 NPI Registry Matcher</h1>",
    unsafe_allow_html=True
)

col1, col2 = st.columns([4, 1])
with col1:
    st.info(
        "**Upload a CSV or Excel file with these columns (case-sensitive):**\n"
        "Last_Name, First_Name, Suffix, Specialty"
    )
with col2:
    sample_data = pd.DataFrame({
        "Last_Name": [],
        "First_Name": [],
        "Suffix": [],
        "Specialty": []
    })
    st.download_button(
        label="📄 Example CSV",
        data=sample_data.to_csv(index=False),
        file_name="sample_provider_file.csv",
        mime="text/csv",
        key="download_sample_csv"
    )

with st.expander("Show detailed instructions"):
    st.markdown("""
    **How to use this app:**
    1. Download the sample template and fill in your provider data.
    2. Upload your completed CSV or Excel file.
    3. Adjust matching options in the sidebar.
    4. Click **Run Matching** to see results.
    5. Use the filters to refine results based on state, specialty, and match level.
    6. Download the results as a CSV file.
    """)

# -------------------- FILE VALIDATION --------------------
def validate_file(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return None, "Unsupported file format. Please upload CSV or Excel."
        # Standardize column names
        df.columns = df.columns.str.strip()
        rename_map = {
            "First_Name": "First Name",
            "Last_Name": "Last Name",
            "Suffix": "Suffix",
            "Specialty": "Specialty"
        }
        df = df.rename(columns=rename_map)
        if "Middle Name" not in df.columns:
            df["Middle Name"] = ""
        return df, None
    except Exception as e:
        return None, f"Error reading file: {str(e)}"

# -------------------- NPI API & MATCHING HELPERS --------------------
def query_npi_api(first, last, state, version=2.1, limit=1000, max_results=500):
    all_results = []
    skip = 0
    while len(all_results) < max_results:
        params = {
            "first_name": first,
            "last_name": last,
            "state": state,
            "limit": min(limit, max_results - len(all_results)),
            "skip": skip,
            "version": version,
            "enumeration_type": "NPI-1",
        }
        r = requests.get("https://npiregistry.cms.hhs.gov/api/", params=params)
        data = r.json()
        results = data.get('results', [])
        if not results:
            break
        all_results.extend(results)
        if len(results) < limit:
            break
        skip += limit
    return {"results": all_results, "result_count": len(all_results)}

def is_fuzzy_match(supplied, candidate, threshold=70):
    return fuzz.partial_ratio(str(supplied).lower(), str(candidate).lower()) >= threshold

def match_provider(row, state, limit):
    first = row['First Name']
    last = row['Last Name']
    middle = row.get('Middle Name', "")
    fuzzy_threshold = 70 

    selected_idx = next(i for i, (label, _) in enumerate(MATCH_STRATEGIES) if label == search_type)
    all_matches = []
    seen_npis = set()  # To avoid duplicate NPIs

    for i, (label, match_level) in enumerate(MATCH_STRATEGIES):
        if i > selected_idx or len(all_matches) >= limit:
            break
        if label == "Best: Full first and last name match":
            results_json = query_npi_api(first, last, state)
            matches = results_json.get('results', []) if results_json.get('result_count', 0) > 0 else []
            matches = [
                m for m in matches
                if m.get("basic", {}).get("first_name", "").strip().lower() == first.strip().lower()
                and m.get("basic", {}).get("last_name", "").strip().lower() == last.strip().lower()
                and (
                    not middle.strip()  # No middle name provided, accept match
                    or (
                        m.get("basic", {}).get("middle_name", "").strip()
                        and m.get("basic", {}).get("middle_name", "").strip()[0].lower() == middle.strip()[0].lower()
                    )
                )
            ]
        elif label == "Good: Last name match + fuzzy first name":
            results_json = query_npi_api("", last, state)
            matches = results_json.get('results', []) if results_json.get('result_count', 0) > 0 else []
            matches = [
                m for m in matches
                if is_fuzzy_match(first, m.get("basic", {}).get("first_name", ""), fuzzy_threshold)
            ]
        elif label == "Potential: Last name only match":
            results_json = query_npi_api("", last, state)
            matches = results_json.get('results', []) if results_json.get('result_count', 0) > 0 else []
        elif label == "Limited Potential: First name only match":
            results_json = query_npi_api(first, "", state)
            matches = results_json.get('results', []) if results_json.get('result_count', 0) > 0 else []
        else:
            matches = []

        for m in matches:
            npi = m.get("number")
            if npi not in seen_npis:
                all_matches.append((match_level, m))
                seen_npis.add(npi)
            if len(all_matches) >= limit:
                break
    return all_matches

def try_both_split_and_unsplit(row, state, limit):
    # Try matching as-is
    matches = match_provider(row, state, limit)
    if matches:
        return matches, row

    # Try splitting last word as middle name if possible
    parts = str(row['First Name']).strip().split()
    if (row.get("Middle Name", "") == "") and len(parts) > 1:
        row2 = row.copy()
        row2['First Name'] = " ".join(parts[:-1])
        row2['Middle Name'] = parts[-1]
        matches = match_provider(row2, state, limit)
        if matches:
            return matches, row2
    return [], row

# -------------------- FILE UPLOAD & MATCHING --------------------
uploaded_file = st.file_uploader("Upload Provider File (CSV or Excel)", type=["csv", "xls", "xlsx"])

if uploaded_file:
    df, error = validate_file(uploaded_file)
    if error:
        st.error(error)
    else:
        st.success(f"Uploaded {len(df)} rows successfully!")
        df = split_first_and_middle(df)
        df["First Name"] = df["First Name"].fillna("").astype(str)
        df["Last Name"] = df["Last Name"].fillna("").astype(str)
        df["Middle Name"] = df["Middle Name"].fillna("").astype(str)
        df["Suffix"] = df["Suffix"].fillna("").astype(str)
        df["Specialty"] = df["Specialty"].fillna("").astype(str)
        if st.button("Click to Run Matching"):
            result_rows = []
            with st.spinner("🔎 Matching providers, please wait..."):
                for _, row in df.iterrows():
                    matches, row_for_results = try_both_split_and_unsplit(row, state, limit)
                    if matches:
                        for idx, (match_level, m) in enumerate(matches, start=1):
                            basic = m.get("basic", {})
                            taxonomies = m.get("taxonomies", [])
                            addresses = m.get("addresses", [])
                            result_rows.append({
                                "First_Name_Supplied": row_for_results.get("First Name", ""),
                                "Last_Name_Supplied": row_for_results.get("Last Name", ""),
                                "FIRST_LAST": f"{row_for_results.get('First Name', '')} {row_for_results.get('Last Name', '')}".strip(),
                                "Middle_Name_Supplied": row_for_results.get("Middle Name", ""),
                                "Specialty_Supplied": row_for_results.get("Specialty", ""), 
                                "Match_Level": match_level,
                                "Result_Count": len(matches),
                                "Result": f"{idx}",
                                "NPI": m.get("number", ""),
                                "First_Name": basic.get("first_name", ""),
                                "Last_Name": basic.get("last_name", ""),
                                "Middle_Name": basic.get("middle_name", ""),
                                "Creditials": basic.get("credential", ""),
                                "Specialty_1": taxonomies[0].get("desc", "") if len(taxonomies) > 0 else "",
                                "Specialty_2": taxonomies[1].get("desc", "") if len(taxonomies) > 1 else "",
                                "Address_1": addresses[0]["address_1"] if len(addresses) > 0 else "",
                                "City_1": addresses[0]["city"] if len(addresses) > 0 else "",
                                "State_1": addresses[0]["state"] if len(addresses) > 0 else "",
                                "Address_2": addresses[1]["address_1"] if len(addresses) > 1 else "",
                                "City_2": addresses[1]["city"] if len(addresses) > 1 else "",
                                "State_2": addresses[1]["state"] if len(addresses) > 1 else "",
                                "Address_3": addresses[2]["address_1"] if len(addresses) > 2 else "",
                                "City_3": addresses[2]["city"] if len(addresses) > 2 else "",
                                "State_3": addresses[2]["state"] if len(addresses) > 2 else "",
                                "Suffix": row_for_results.get("Suffix", ""),
                                "Address Match": "",
                            })
                    else:
                        result_rows.append({
                            "First_Name_Supplied": row.get("First Name", ""),
                            "Last_Name_Supplied": row.get("Last Name", ""),
                            "FIRST_LAST": f"{row.get('First Name', '')} {row.get('Last Name', '')}".strip(),
                            "Middle_Name_Supplied": row.get("Middle Name", ""),
                            "Specialty_Supplied": row.get("Specialty", ""), 
                            "Match_Level": "No Match",
                            "Result_Count": 0,
                            "Result": "No Match",
                            "NPI": "",
                            "First_Name": "",
                            "Last_Name": "",
                            "Middle_Name": "",
                            "Creditials": "",
                            "Specialty_1": "",
                            "Specialty_2": "",
                            "Address_1": "",
                            "City_1": "",
                            "State_1": "",
                            "Address_2": "",
                            "City_2": "",
                            "State_2": "",
                            "Address_3": "",
                            "City_3": "",
                            "State_3": "",
                            "Specialty_Supplied": row.get("Specialty", ""),
                            "Suffix": row.get("Suffix", ""),
                            "Address Match": "",
                        })
            desired_columns = [
                "First_Name_Supplied", "Last_Name_Supplied", "FIRST_LAST", "Middle_Name_Supplied", "Specialty_Supplied",
                "Match_Level", "Result_Count", "Result", "NPI",
                "First_Name", "Last_Name", "Middle_Name", "Creditials",
                "Specialty_1", "Specialty_2",
                "Address_1", "City_1", "State_1",
                "Address_2", "City_2", "State_2",
                "Address_3", "City_3", "State_3",
                "Specialty", "Suffix", "Address Match"
            ]
            result_df = pd.DataFrame(result_rows, columns=desired_columns)
            st.session_state['result_df'] = result_df  # <-- Store in session_state

# --- Results Filtering & Display (always visible if results exist) ---
result_df = st.session_state.get('result_df')
if result_df is not None and not result_df.empty:
    st.success("Matching complete! Preview the results below. Use the filters to refine these results.")

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        all_states = pd.concat([
            result_df["State_1"].dropna(),
            result_df["State_2"].dropna(),
            result_df["State_3"].dropna()
        ]).unique()
        state_filter = st.multiselect(
            "Filter by State",
            options=sorted([s for s in all_states if s]),
            default=[]
        )
    with filter_col2:
        all_specialties = pd.concat([
            result_df["Specialty_1"].dropna(),
            result_df["Specialty_2"].dropna()
        ]).unique()
        specialty_filter = st.multiselect(
            "Filter by Specialty",
            options=sorted([s for s in all_specialties if s]),
            default=[]
        )
    with filter_col3:
        match_level_filter = st.multiselect(
            "Filter by Match Level",
            options=sorted(result_df["Match_Level"].dropna().unique()),
            default=[]
        )

    filtered_df = result_df.copy()
    if state_filter:
        filtered_df = filtered_df[
            filtered_df["State_1"].isin(state_filter) |
            filtered_df["State_2"].isin(state_filter) |
            filtered_df["State_3"].isin(state_filter)
        ]
    if specialty_filter:
        filtered_df = filtered_df[
            filtered_df["Specialty_1"].isin(specialty_filter) | filtered_df["Specialty_2"].isin(specialty_filter)
        ]
    if match_level_filter:
        filtered_df = filtered_df[filtered_df["Match_Level"].isin(match_level_filter)]

    st.dataframe(filtered_df, use_container_width=True)
    st.download_button("Download Results as CSV", filtered_df.to_csv(index=False), "npi_results.csv", "text/csv")
else:
    st.warning("Please upload a provider file to get started.")
