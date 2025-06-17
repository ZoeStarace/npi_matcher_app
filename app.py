import streamlit as st
import pandas as pd
import requests
from rapidfuzz import fuzz

# -------------------- CONFIG & CONSTANTS --------------------
st.set_page_config(page_title="NPI Matcher", layout="wide")
REQUIRED_COLUMNS = {"First Name", "Last Name", "Specialty", "Hospital"}

# -------------------- SIDEBAR: APP INFO & OPTIONS --------------------
with st.sidebar:
    st.title("NPI Matcher Settings")
    st.markdown("Configure your matching preferences below.")
    state = st.text_input("Limit search to state (e.g., NY)", max_chars=2)
    limit = st.number_input("Max matches per provider", min_value=1, max_value=50, value=10)
    fuzzy_threshold = st.slider("Fuzzy match threshold", min_value=60, max_value=100, value=80, help="Higher = stricter match")
    st.markdown("---")
    st.markdown("**Need help?**\n- Download the sample template\n- Ensure your file has the required columns\n- Adjust matching options as needed")

# -------------------- HEADER & INSTRUCTIONS --------------------
st.markdown(
    "<h1 style='text-align: center; color: #4F8BF9;'>🔍 NPI Registry Matcher</h1>",
    unsafe_allow_html=True
)

st.info(
    "Upload a CSV or Excel file with these columns (case-sensitive):\n\n"
    "- First Name\n- Last Name\n- Middle Name (optional)\n- Specialty\n- Hospital\n\n"
    "Example header: `First Name,Last Name,Middle Name,Specialty,Hospital`"
)

with st.expander("Show detailed instructions"):
    st.markdown("""
    **How to use this app:**
    1. Download the sample template and fill in your provider data.
    2. Upload your completed CSV or Excel file.
    3. Adjust matching options in the sidebar.
    4. Click **Run Matching** to see results.
    """)

# -------------------- DOWNLOAD SAMPLE TEMPLATE --------------------
sample_data = pd.DataFrame({
    "First Name": [],
    "Last Name": [],
    "Middle Name": [],
    "Specialty": [],
    "Hospital": []
})
st.download_button(
    label="⬇️ Download Sample CSV Template",
    data=sample_data.to_csv(index=False),
    file_name="sample_provider_file.csv",
    mime="text/csv"
)

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
def query_npi_api(first, last, state, version=2.1, limit=10):
    params = {
        "first_name": first,
        "last_name": last,
        "state": state,
        "limit": limit,
        "version": version,
        "enumeration_type": "NPI-1",
    }
    r = requests.get("https://npiregistry.cms.hhs.gov/api/", params=params)
    return r.json()

def is_fuzzy_match(supplied, candidate, threshold=80):
    return fuzz.partial_ratio(str(supplied).lower(), str(candidate).lower()) >= threshold

def filter_results_by_state(matches, state):
    if not state:
        return matches
    filtered = []
    for m in matches:
        for addr in m.get("addresses", []):
            if addr.get("state", "").strip().upper() == state.strip().upper():
                filtered.append(m)
                break
    return filtered

def match_provider(row, state, limit, fuzzy_threshold=80):
    first = row['First Name']
    last = row['Last Name']
    strategies = [
        {"first": first, "last": last, "state": state, "level": "Full"},
        {"first": first, "last": last, "state": "", "level": "Fuzzy"},
        {"first": "", "last": last, "state": state, "level": "Last Name Only"},
    ]
    for strat in strategies:
        results_json = query_npi_api(strat["first"], strat["last"], strat["state"], limit=limit)
        matches = results_json.get('results', []) if results_json.get('result_count', 0) > 0 else []
        if strat["level"] == "Full":
            matches = filter_results_by_state(matches, state)
        elif strat["level"] == "Fuzzy":
            matches = [
                m for m in filter_results_by_state(matches, state)
                if is_fuzzy_match(first, m.get("basic", {}).get("first_name", ""), fuzzy_threshold)
            ]
        if matches:
            return strat["level"], matches
    return "No Match", []

# -------------------- FILE UPLOAD & MATCHING --------------------
uploaded_file = st.file_uploader("Upload Provider File (CSV or Excel)", type=["csv", "xls", "xlsx"])

if uploaded_file:
    df, error = validate_file(uploaded_file)
    if error:
        st.error(error)
    else:
        st.success(f"Uploaded {len(df)} rows successfully!")

        if st.button("🚦 Run Matching"):
            result_rows = []
            with st.spinner("🔎 Matching providers, please wait..."):
                for _, row in df.iterrows():
                    match_level, matches = match_provider(row, state, limit, fuzzy_threshold)
                    if matches:
                        m = matches[0]
                        basic = m.get("basic", {})
                        taxonomies = m.get("taxonomies", [])
                        addresses = m.get("addresses", [])
                        matched_hospital = m.get("organization_name", "")
                        result_rows.append({
                            "Original First Name": row.get("First Name", ""),
                            "Original Last Name": row.get("Last Name", ""),
                            "Original Middle Name": row.get("Middle Name", ""),
                            "Original Specialty": row.get("Specialty", ""),
                            "Original Hospital": row.get("Hospital", ""),
                            "Match Level": match_level,
                            "NPI": m.get("number", ""),
                            "Matched First Name": basic.get("first_name", ""),
                            "Matched Last Name": basic.get("last_name", ""),
                            "Matched Middle Name": basic.get("middle_name", ""),
                            "Matched Specialty 1": taxonomies[0].get("desc", "") if len(taxonomies) > 0 else "",
                            "Matched Specialty 2": taxonomies[1].get("desc", "") if len(taxonomies) > 1 else "",
                            "Matched Hospital": matched_hospital,
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
                            "Original Specialty": row.get("Specialty", ""),
                            "Original Hospital": row.get("Hospital", ""),
                            "Match Level": "No Match",
                            "NPI": "",
                            "Matched First Name": "",
                            "Matched Last Name": "",
                            "Matched Middle Name": "",
                            "Matched Specialty 1": "",
                            "Matched Specialty 2": "",
                            "Matched Hospital": "",
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
                "Original First Name", "Original Last Name", "Original Middle Name", "Original Specialty", "Original Hospital",
                "Match Level", "NPI",
                "Matched First Name", "Matched Last Name", "Matched Middle Name",
                "Matched Specialty 1", "Matched Specialty 2", "Matched Hospital",
                "Address 1", "City 1", "State 1",
                "Address 2", "City 2", "State 2",
                "Address 3", "City 3", "State 3"
            ])
            st.success("✅ Matching complete! Preview your results below.")
            st.dataframe(result_df, use_container_width=True)
            st.download_button("💾 Download Results as CSV", result_df.to_csv(index=False), "npi_results.csv", "text/csv")
        else:
            st.info("Ready to match! Click **Run Matching** to begin.")
else:
    st.warning("Please upload a provider file to get started.")