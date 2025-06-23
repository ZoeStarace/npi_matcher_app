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

# -------------------- SIDEBAR: APP INFO & OPTIONS --------------------
with st.sidebar:
    st.title("NPI Matcher Settings")
    st.markdown("Configure your matching preferences below.")
    state = st.text_input("Limit search to state (e.g., NY)", max_chars=2, key="state", on_change=clear_results)
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
        "First Name, Last Name, Middle Name (optional)"
    )
with col2:
    sample_data = pd.DataFrame({
        "First Name": [],
        "Last Name": [],
        "Middle Name": []
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
        if not REQUIRED_COLUMNS.issubset(df.columns):
            missing = REQUIRED_COLUMNS - set(df.columns)
            return None, f"Missing required columns: {', '.join(missing)}"
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
        print(f"Fetched {len(results)} results (skip={skip}, limit={limit})")
        # Debug print for each result's first name, last name, and state
        for r in results:
            print(r.get('basic', {}).get('first_name'), r.get('basic', {}).get('last_name'), end=' ')
            # Try to print the first address's state if available
            addresses = r.get('addresses', [])
            state_val = addresses[0].get('state') if addresses else None
            print(state_val)
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

# -------------------- FILE UPLOAD & MATCHING --------------------
uploaded_file = st.file_uploader("Upload Provider File (CSV or Excel)", type=["csv", "xls", "xlsx"])

if uploaded_file:
    df, error = validate_file(uploaded_file)
    if error:
        st.error(error)
    else:
        st.success(f"Uploaded {len(df)} rows successfully!")

        if st.button("Click to Run Matching"):
            result_rows = []
            with st.spinner("🔎 Matching providers, please wait..."):
                for _, row in df.iterrows():
                    matches = match_provider(row, state, limit)
                    if matches:
                        for match_level, m in matches:
                            basic = m.get("basic", {})
                            taxonomies = m.get("taxonomies", [])
                            addresses = m.get("addresses", [])
                            result_rows.append({
                                "Original First Name": row.get("First Name", ""),
                                "Original Last Name": row.get("Last Name", ""),
                                "Original Middle Name": row.get("Middle Name", ""),
                                "Match Level": match_level,
                                "NPI": m.get("number", ""),
                                "Matched First Name": basic.get("first_name", ""),
                                "Matched Last Name": basic.get("last_name", ""),
                                "Matched Middle Name": basic.get("middle_name", ""),
                                "Specialty 1": taxonomies[0].get("desc", "") if len(taxonomies) > 0 else "",
                                "Specialty 2": taxonomies[1].get("desc", "") if len(taxonomies) > 1 else "",
                                "Address 1": addresses[0]["address_1"] if len(addresses) > 0 else "",
                                "City 1": addresses[0]["city"] if len(addresses) > 0 else "",
                                "State 1": addresses[0]["state"] if len(addresses) > 0 else "",
                                "Address 2": addresses[1]["address_1"] if len(addresses) > 1 else "",
                                "City 2": addresses[1]["city"] if len(addresses) > 1 else "",
                                "State 2": addresses[1]["state"] if len(addresses) > 1 else "",
                                "Address 3": addresses[2]["address_1"] if len(addresses) > 2 else "",
                                "City 3": addresses[2]["city"] if len(addresses) > 2 else "",
                                "State 3": addresses[2]["state"] if len(addresses) > 2 else "",
                            })
                    else:
                        result_rows.append({
                            "Original First Name": row.get("First Name", ""),
                            "Original Last Name": row.get("Last Name", ""),
                            "Original Middle Name": row.get("Middle Name", ""),
                            "Match Level": "No Match",
                            "NPI": "",
                            "Matched First Name": "",
                            "Matched Last Name": "",
                            "Matched Middle Name": "",
                            "Specialty 1": "",
                            "Specialty 2": "",
                            "Address 1": "",
                            "City 1": "",
                            "State 1": "",
                            "Address 2": "",
                            "City 2": "",
                            "State 2": "",
                            "Address 3": "",
                            "City 3": "",
                            "State 3": "",
                        })
            result_df = pd.DataFrame(result_rows, columns=[
                "Original First Name", "Original Last Name", "Original Middle Name", 
                "Match Level", "NPI",
                "Matched First Name", "Matched Last Name", "Matched Middle Name",
                "Specialty 1", "Specialty 2",
                "Address 1", "City 1", "State 1",
                "Address 2", "City 2", "State 2",
                "Address 3", "City 3", "State 3"
            ])
            st.session_state['result_df'] = result_df  # <-- Store in session_state

# --- Results Filtering & Display (always visible if results exist) ---
result_df = st.session_state.get('result_df')
if result_df is not None and not result_df.empty:
    st.success("Matching complete! Preview the results below. Use the filters to refine these results.")

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        all_states = pd.concat([
            result_df["State 1"].dropna(),
            result_df["State 2"].dropna(),
            result_df["State 3"].dropna()
        ]).unique()
        state_filter = st.multiselect(
            "Filter by State",
            options=sorted(all_states),
            default=[]
        )
    with filter_col2:
        all_specialties = pd.concat([
            result_df["Specialty 1"].dropna(),
            result_df["Specialty 2"].dropna()
        ]).unique()
        specialty_filter = st.multiselect(
            "Filter by Specialty",
            options=sorted(all_specialties),
            default=[]
        )
    with filter_col3:
        match_level_filter = st.multiselect(
            "Filter by Match Level",
            options=sorted(result_df["Match Level"].dropna().unique()),
            default=[]
        )

    filtered_df = result_df.copy()
    if state_filter:
        filtered_df = filtered_df[
            filtered_df["State 1"].isin(state_filter) |
            filtered_df["State 2"].isin(state_filter) |
            filtered_df["State 3"].isin(state_filter)
        ]
    if specialty_filter:
        filtered_df = filtered_df[
            filtered_df["Specialty 1"].isin(specialty_filter) | filtered_df["Specialty 2"].isin(specialty_filter)
        ]
    if match_level_filter:
        filtered_df = filtered_df[filtered_df["Match Level"].isin(match_level_filter)]

    st.dataframe(filtered_df, use_container_width=True)
    st.download_button("Download Results as CSV", filtered_df.to_csv(index=False), "npi_results.csv", "text/csv")
else:
    st.warning("Please upload a provider file to get started.")
