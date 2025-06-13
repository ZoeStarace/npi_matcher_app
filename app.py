import streamlit as st
import pandas as pd
import requests
from rapidfuzz import fuzz

st.set_page_config(page_title="NPI Matcher", layout="wide")
st.title("🔍 NPI Registry Matcher")

def clean_names(df):
    df['Last Name'] = df['Last Name'].str.strip()
    df['First Name'] = df['First Name'].str.strip()
    m_name_list = []
    for i in range(df.shape[0]):
        if len(df.loc[i, 'First Name'].split()) > 1:
            m_name_list.append(df.loc[i, 'First Name'].split()[1])
            df.loc[i, 'First Name'] = df.loc[i, 'First Name'].split()[0]
        else:
            m_name_list.append("")
    df["Middle Name"] = m_name_list
    return df

def query_npi_api(first, last, state, version=2.1, limit=10):
    base_url = "https://npiregistry.cms.hhs.gov/api/"
    params = {
        "number": "",
        "enumeration_type": "NPI-1",
        "taxonomy_description": "",
        "first_name": first,
        "last_name": last,
        "organization_name": "",
        "address_purpose": "",
        "city": "",
        "state": state,
        "postal_code": "",
        "country_code": "",
        "limit": limit,
        "skip": "",
        "version": version,
        "use_first_name_alias": "False"
    }
    r = requests.get(base_url, params=params)
    return r.json()

def is_fuzzy_match(supplied, candidate, threshold=80):
    return fuzz.partial_ratio(str(supplied).lower(), str(candidate).lower()) >= threshold

def match_provider_v1(row, state, limit, fuzzy_threshold=80):
    first = row['First Name']
    last = row['Last Name']
    middle = row.get('Middle Name', "")
    version = 2.1

    # Try different query strategies
    strategies = [
        {"first": first, "last": last, "state": state, "level": "Level 1"},
        {"first": first, "last": last, "state": "", "level": "Level 2"},
        {"first": "", "last": last, "state": state, "level": "Level 3"},
    ]
    results_json = None
    match_level = "No Match"
    matches = []
    for strat in strategies:
        results_json = query_npi_api(strat["first"], strat["last"], strat["state"], version, limit)
        if results_json.get('result_count', 0) > 0:
            # Fuzzy match on first name if not Level 1
            if strat["level"] == "Level 1":
                matches = results_json['results']
            else:
                matches = [
                    m for m in results_json['results']
                    if is_fuzzy_match(first, m.get("basic", {}).get("first_name", ""), fuzzy_threshold)
                ]
            if matches:
                match_level = strat["level"]
                break

    return match_level, matches

# Upload file
uploaded_file = st.file_uploader("Upload Provider File (CSV or Excel)", type=["csv", "xls", "xlsx"])

# User options
state = st.text_input("Limit search to state (e.g., NY)", max_chars=2)
limit = st.number_input("Max matches per provider", min_value=1, max_value=50, value=10)
fuzzy_threshold = st.slider("Fuzzy match threshold (higher = stricter)", min_value=60, max_value=100, value=80)
match_levels = ["Level 1", "Level 2", "Level 3", "No Match"]
selected_levels = st.multiselect("Select match levels to include", match_levels, default=match_levels[:-1])

if uploaded_file:
    # Read file
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    st.success(f"Uploaded {len(df)} rows successfully!")

    # Clean and split names
    df = clean_names(df)

    if st.button("Run Matching"):
        result_rows = []
        with st.spinner("Matching providers..."):
            for idx, row in df.iterrows():
                match_level, matches = match_provider_v1(row, state, limit, fuzzy_threshold)
                if matches:
                    for m in matches[:3]:  # Limit to 3 results
                        basic = m.get("basic", {})
                        addresses = m.get("addresses", [])
                        taxonomies = m.get("taxonomies", [])
                        result_rows.append({
                            "Original First Name": row["First Name"],
                            "Original Last Name": row["Last Name"],
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
                        "Original First Name": row["First Name"],
                        "Original Last Name": row["Last Name"],
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

        result_df = pd.DataFrame(result_rows)
        # Filter by user-selected match levels
        result_df = result_df[result_df["Match Level"].isin(selected_levels)]

        # Specialty filter
        specialties = sorted(set(result_df["Specialty 1"].dropna().unique()) | set(result_df["Specialty 2"].dropna().unique()))
        specialties = [s for s in specialties if s]
        selected_specialty = st.selectbox("Filter by Specialty (post-hoc)", ["All"] + specialties)
        if selected_specialty != "All":
            result_df = result_df[(result_df["Specialty 1"] == selected_specialty) | (result_df["Specialty 2"] == selected_specialty)]

        st.dataframe(result_df)
        st.download_button("Download Results as CSV", result_df.to_csv(index=False), "npi_results.csv", "text/csv")