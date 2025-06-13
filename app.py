import streamlit as st
import pandas as pd
from utils import validate_file
from matcher import match_provider

st.set_page_config(page_title="NPI Matcher", layout="wide")

st.title("🔍 NPI Registry Matcher")

# Upload file
uploaded_file = st.file_uploader("Upload Provider File (CSV or Excel)", type=["csv", "xls", "xlsx"])

# User options
state = st.text_input("Limit search to state (e.g., NY)", max_chars=2)
limit = st.number_input("Max matches per provider", min_value=1, max_value=50, value=10)

if uploaded_file:
    df, error = validate_file(uploaded_file)
    
    if error:
        st.error(error)
    else:
        st.success(f"Uploaded {len(df)} rows successfully!")

        if st.button("Run Matching"):
            result_rows = []
            with st.spinner("Matching providers..."):
                for idx, row in df.iterrows():
                    match_level, matches = match_provider(row, state, limit)
                    if matches:
                        for m in matches[:3]:  # Limit to 3 results
                            basic = m["basic"]
                            addresses = m.get("addresses", [])
                            result_rows.append({
                                "Original First Name": row["First Name"],
                                "Original Last Name": row["Last Name"],
                                "Match Level": match_level,
                                "NPI": m.get("number", ""),
                                "Matched First Name": basic.get("first_name", ""),
                                "Matched Last Name": basic.get("last_name", ""),
                                "Specialty 1": m.get("taxonomies", [{}])[0].get("desc", ""),
                                "Address 1": addresses[0]["address_1"] if addresses else ""
                            })
                    else:
                        result_rows.append({
                            "Original First Name": row["First Name"],
                            "Original Last Name": row["Last Name"],
                            "Match Level": "No Match",
                            "NPI": "",
                            "Matched First Name": "",
                            "Matched Last Name": "",
                            "Specialty 1": "",
                            "Address 1": ""
                        })

            result_df = pd.DataFrame(result_rows)
            st.dataframe(result_df)
            st.download_button("Download Results as CSV", result_df.to_csv(index=False), "npi_results.csv", "text/csv")