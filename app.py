import streamlit as st
import pandas as pd
import requests
from rapidfuzz import fuzz
import re
import concurrent.futures
import io

show_stats = False

# -------------------- CONFIG & CONSTANTS --------------------
st.set_page_config(page_title="NPI Matcher", layout="wide", initial_sidebar_state="expanded")
REQUIRED_COLUMNS = {"First Name", "Last Name"}

npi_expected = [
    "1467912576", "1770739559", "1619258381", "1265539993", "1407041312", "1811278195", "1235386517", "1245894286", "1619070836", "1780830158", "1497963599", "1265402374", "1639632656", "1932105541", "1508015082", "1063792828", "1861013005", "1790786432", "1013172279", "1295909786", "1154941409", "1902099963", "1982605614", "1497337794", "1952925224", "1255344644", "1942611546", "1356712657", "1033495130", "1508851759", "1336113414", "1588838809", "1639420995", "1932528874", "1922200427", "1720029770", "1215938766", "1518240720", "1437416807", "1780677708", "1710145008", "1265888242", "1760425243", "1265718118", "1578023727", "1285635912", "1629351838", "1477545085", "1831651827", "1760475875", "1639528375", "1679649933", "1992797500", "1528206166", "1194070904", "1790932119", "1285627216", "1871993642", "1982696506", "1619172871", "1295949279", "1821372004", "1285165597", "1770071136", "1922505866", "1841672110", "1417187345", "1831538149", "1437257797", "1124009832", "1083093942", "1659577799", "1306238100", "1497749808", "1942488358", "1215921606", "1194257535", "1710971049", "1770735607", "1215180922", "1316108871", "1336567494", "1093102451", "1295700920", "1386937696", "1780637421", "1922338276", "1750671228", "1598173684", "1407874563", "1811934987", "1619960630", "1043475080", "1588160709", "1831183227", "1821060146", "1326509969", "1972624120", "1265429922", "1922031962", "1013943547", "1144202979", "1326247453", "1083681852", "1164653010", "1578805552", "1356796312", "1174563969", "1912056623", "1790733186", "1992771596", "1164415188", "1255527008", "1578652392", "1609172360", "1427382399", "1598999484", "1124347612", "1316574817", "1053708073", "1760475792", "1376639088", "1730479510", "1265403208", "1497863195", "1760689590", "1659667772", "1851851307", "1700271699", "1417120031", "1467807776", "1265615918", "1326144650", "1972761591", "1295153138", "1063825792", "1003816604", "1548423809", "1982101614", "1598771529", "1124188925", "1235581174", "1417158072", "1447834601", "1972959831", "1790066454", "1023163771", "1053629956", "1871659136", "1538466438", "1508304155", "1093156028", "1215125588", "1154587566", "1699208454", "1396945903", "1093264822", "1275655565", "1750763504", "1699138974", "1366945180", "1134120967", "1114123742", "1255509006", "1194713347", "1013000629", "1750606711", "1184611840", "1013412808", "1952310468", "1215465109", "1225235385", "1265750343", "1578739611", "1043555352", "1013235340", "1982691648", "1407105158", "1023270253", "1407152341", "1013995620", "1548578594", "1750524625", "1861402851", "1134110125", "1275813651", "1619174240", "1619159852", "1558929877", "1134106107", "1417025321", "1336406644", "1598051484", "1942582705", "1164416897", "1508958299", "1639160187", "1508866096", "1013536606", "1639137029", "1518386994", "1427030691", "1538141726", "1891884946", "1649836925", "1780940049", "1629225651", "1518128594", "1770557860", "1790767762", "1699942441", "1578970414", "1316273493", "1912294448", "1013336551", "1194725168", "1841607744", "1508866187", "1982164935", "1417158023", "1003190711", "1457843716", "1033191226", "1609089457", "1295717486", "1518311307", "1679573646", "1760600431", "1689912669", "1669092672", "1063412013", "1518112788", "1285634345", "1285773200", "1013288273", "1528598224", "1922363670", "1215919030", "1649220740", "1346223591", "1811217714", "1235492703", "1477692929", "1144463597", "1588914600", "1255714978", "1831699842", "1609877331", "1891769774", "1962445684", "1366528739", "1336216613", "1538463799", "1467799163", "1356001010", "1740547637", "1053916353", "1720649395", "1770830432", "1053634139", "1336131952", "1568798932", "1346693546", "1104207893", "1336263672", "1356689657", "1568762516", "1164944294", "1306927314", "1942410444", "1275796195", "1689988297", "1215256789", "1629698717", "1821700436", "1710351150", "1467859512", "1396906624", "1821860883", "1134510258", "1033675863", "1871228023", "1588680623", "1275961260", "1932580081", "1255912523", "1386011385", "1295134013", "1730119439", "1801266994", "1205322369", "1790462216", "1346881836", "1134725575", "1154861060", "1780978197", "1255473666", "1720462369", "1649894338", "1063784908", "1831655026", "1427380138", "1114661832", "1205227352", "1174066989", "1861681926", "1134761679", "1386229557", "1538141494", "1366807109", "1316707979", "1134224470", "1417242413", "1205445384", "1477592863", "1669404216", "1871575019", "1710208814", "1437193521", "1841044278", "1033996194", "1043838246", "1568832665", "1598199176", "1831610369", "1437663424", "1518186840", "1134198880", "1285708222", "1568550531", "1386759512", "1982027538", "1467656496", "1902087208", "1083697254", "1619167822", "1144360884", "1043599236", "1831299957", "1487899241", "1972771681", "1144503053", "1447566617", "1053307512", "1427382399", "1013336551", "1083093942", "1659667772", "1043475080", "1982101614", "1366945180", "1407105158", "1831699842", "1619258381", "1750671228", "1609172360", "1780969790", "1750607602", "1083176788", "1346421963", "1467618678", "1649767559", "1689619710", "1376515155", "1053554121", "1275820755", "1689836207", "1386064806", "1104130947", "1700078649", "1659306322", "1922409994", "1053961292", "1386377265", "1134208879", "1134368608", "1568453546", "1386718567", "1154316131", "1770657330", "1679942841", "1144431396", "1184003147", "1033304589", "1922458249", "1366079717", "1114166220", "1881700177", "1952493538", "1588833081", "1548518350", "1508106758", "1780121855", "1992787972", "1821528167", "1366513749", "1356458277", "1821363334", "1750627683", "1689931719", "1962497115", "1851829485", "1225515448", "1871124487", "1912015397", "1831392034", "1619557584", "1033985338", "1639515497", "1033101951", "1770275562", "1902309164", "1851446116", "1497210272", "1053629808", "1598920530", "1407474604", "1578271474", "1255827929", "1063097814", "1013040690", "1740314533", "1114659851", "1528192804", "1366716094", "1952383069", "1154402139", "1760555312", "1780121855", "1992787972", "1225097793", "1669739884", "1518007368", "1962991851", "1518163039", "1851553259", "1952767535", "1053336727", "1043303274", "1174941967", "1538585716", "1013197300", "1710979174", "1932884939", "1043310634", "1427596337", "1285615120", "1801183215", "1902000730", "1184986051", "1366999153", "1225369218", "1649698259", "1316276827", "1366590192", "1467035998", "1992384218", "1851393771", "1265435655", "1124050497", "1942055918", "1659451128", "1912033424", "1427881531", "1164208385", "1639167679", "1437860566", "1982985610", "1033824222", "1093958613", "1730641606", "1093028102", "1841674926", "1467796268", "1831378413", "1003194689", "1942294335", "1336349984", "1245959253", "1356996813", "1760128805", "1902102387", "1982943957"
]
exclude_npis = {
    "1336349984", "1467796268", "1831378413", "1003194689", "1033985338", "1033824222", "1730641606",
    "1093028102", "1841674926", "1053961292", "1386377265", "1063097814", "1093264822", "1104130947",
    "1154402139", "1639515497", "1649767559", "1659306322", "1821363334", "1831392034", "1851393771",
    "1467035998", "1366590192", "1881700177", "1902102387", "1982943957", "1356996813", "1245959253",
    "1952767535", "1982985610", "1437860566", "1164208385", "1427881531", "1346421963", "1427596337",
    "1578271474", "1851446116"
}
npi_expected = [npi for npi in npi_expected if npi not in exclude_npis]

MATCH_STRATEGIES = [
    ("Best: Full first and last name match", "Best"),
    ("Good: Last name match + fuzzy first name", "Good"),
    ("Potential: Last name only match", "Potential"),
    ("Limited Potential: First name only match", "Limited Potential"),
]

def clear_results():
    if 'result_df' in st.session_state:
        del st.session_state['result_df']

#not used
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

    limit = st.number_input("Max matches per provider", min_value=1, max_value=50, value=5, key="limit", on_change=clear_results)
    #st.markdown("**Match strictness options:**")
    #st.markdown("""
#- **Best:** Full first and last name match  
#- **Good:** Last name match + fuzzy first name  
#- **Potential:** Last name only match  
#- **Limited Potential:** First name only match
 #   """)
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

    with st.expander("ℹ️ What do the match levels mean?"):
        st.markdown("""
**Match Level Explanations:**

- **Best:**  
  Requires an exact match on both first and last name (case-insensitive, ignores extra spaces). Attempts to strip out middle name from first name. Also checks former names (aliases/other names) for an exact match. Attempts to match specialty. NY is prioritized.

- **Good:**  
  Last name must match exactly. First name is matched fuzzily (allows for typos or nicknames) or by former name. Specialty is matched fuzzily. NY matches are sorted to the top.

- **Potential:**  
  Only the last name must match exactly. First name is ignored. Specialty is matched fuzzily if provided. NY matches are sorted to the top.

- **Limited Potential:**  
  Only the first name must match exactly. Last name is ignored. Specialty is matched fuzzily if provided. NY matches are sorted to the top.
""")
# -------------------- HEADER & INSTRUCTIONS --------------------
st.markdown(
    "<h1 style='text-align: center; color: #4F8BF9;'>🔍 NPI Registry Matcher</h1>",
    unsafe_allow_html=True
)


col1, col2 = st.columns([4, 1])
with col1:
    st.info(
        "**Upload a CSV file with these columns (case-sensitive):**\n"
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
2. Upload your completed CSV file.  
3. Choose your matching options in the sidebar (state, strictness, max matches).  
4. Click "Run Matching" to start.  
5. Review and filter your results.  
6. Download your results as Excel.
    """)
# -------------------- FILE VALIDATION --------------------
def validate_file(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return None, "Unsupported file format. Please upload CSV."
        # Standardize column names
        df.columns = df.columns.str.strip()
        rename_map = {
            "First_Name": "First Name",
            "Last_Name": "Last Name",
            "Suffix": "Suffix",
            "Specialty": "Specialty"
        }
        df = df.rename(columns=rename_map)
        #if "Middle Name" not in df.columns:
        df["Middle Name"] = ""
        return df, None
    except Exception as e:
        return None, f"Error reading file: {str(e)}"
    
def clean_specialty(s):
    # Remove everything after a slash or comma (including the slash/comma)
    if pd.isna(s):
        return ""
    return re.split(r"[/,]", str(s))[0].strip()

# -------------------- NPI API & MATCHING HELPERS --------------------
@st.cache_data(show_spinner=False, ttl=86400)  # 86400 seconds = 24 hours
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

def match_provider(row, state, limit, search_type):
    first = row['First Name']
    last = row['Last Name']
    specialty = row.get('Specialty', "")
    fuzzy_threshold = 10 
    specialty_fuzzy_threshold = 80  
    seen_npis = set()  # To avoid duplicate NPIs

    # Split state string into a list if needed
    states = [s.strip() for s in state.split(",") if s.strip()] if state else [""]

    selected_idx = [i for i, (label, _) in enumerate(MATCH_STRATEGIES) if label == search_type][0]

    for i, (label, match_level) in enumerate(MATCH_STRATEGIES):
        if i > selected_idx:
            break

        matches = []
        scored_matches = []
        if label == "Best: Full first and last name match":
            # Aggregate results from all selected states
            # --- First, run as-is ---
            all_results = []
            for s in states:
                results_json = query_npi_api(first, last, s)
                all_results.extend(results_json.get('results', []) if results_json.get('result_count', 0) > 0 else [])
            matches = all_results
            #print(f"All candidate matches for {first} {last}: {[m.get('number') for m in matches]}")
            matches_with_specialty = [
                m for m in matches
                if (
                    (
                        m.get("basic", {}).get("first_name", "").strip().lower() == first.strip().lower()
                        and m.get("basic", {}).get("last_name", "").strip().lower() == last.strip().lower()
                    )
                    or matches_former_name(first, last, m.get("other_names", []))
                )
                and (
                    (not specialty) or
                    any(
                        clean_specialty(specialty).lower() in clean_specialty(t.get("desc", "")).lower()
                        for t in m.get("taxonomies", [])
                    )
                )
            ]
            #print(f"After filtering for exact name: {[m.get('number') for m in matches_with_specialty]}")
            if matches_with_specialty:
                matches = matches_with_specialty
                match_level = "Best"
                specialty_matched = True
            else:
                # --- Second, try splitting middle name from first name if possible ---
                parts = str(first).strip().split()
                if (row.get("Middle Name", "") == "") and len(parts) > 1:
                    first_split = " ".join(parts[:-1])
                    middle_split = parts[-1]
                    all_results_split = []
                    for s in states:
                        results_json = query_npi_api(first_split, last, s)
                        all_results_split.extend(results_json.get('results', []) if results_json.get('result_count', 0) > 0 else [])
                    matches_split = all_results_split
                    matches_with_specialty_split = [
                        m for m in matches_split
                        if (
                            (
                                m.get("basic", {}).get("first_name", "").strip().lower() == first_split.strip().lower()
                                and m.get("basic", {}).get("last_name", "").strip().lower() == last.strip().lower()
                            )
                            or matches_former_name(first_split, last, m.get("other_names", []))
                        )
                        and (
                            (not specialty) or
                            any(
                                clean_specialty(specialty).lower() in clean_specialty(t.get("desc", "")).lower()
                                for t in m.get("taxonomies", [])
                            )
                        )
                    ]
                    #print(f"After splitting first name and filtering: {[m.get('number') for m in matches_with_specialty_split]}")
                    if matches_with_specialty_split:
                        matches = matches_with_specialty_split
                        match_level = "Best"
                        specialty_matched = True
                    else:
                        specialty_matched = False
                else:
                    specialty_matched = False
            # Try both matches and matches_split for name-only match if specialty_matched is False
            if specialty_matched == False:
                def get_matches_name_only(matches_list, first_val, last_val):
                    return sorted(
                        [
                            m for m in matches_list
                            if (
                                m.get("basic", {}).get("first_name", "").strip().lower() == first_val.strip().lower()
                                and m.get("basic", {}).get("last_name", "").strip().lower() == last_val.strip().lower()
                            )
                            or matches_former_name(first_val, last_val, m.get("other_names", []))
                        ],
                        key=lambda m: max(
                            [
                                fuzz.token_sort_ratio(specialty, t.get("desc", ""))
                                for t in m.get("taxonomies", [])
                            ] if specialty else [0]
                        ),
                        reverse=True
                    )

                matches_name_only = get_matches_name_only(matches, first, last)
                matches_name_only_split = []
                if 'matches_split' in locals():
                    matches_name_only_split = get_matches_name_only(matches_split, first_split, last)

                # Prefer matches_name_only if found, else try matches_name_only_split
                if matches_name_only:
                    matches = matches_name_only
                    match_level = "Best"
                    specialty_matched = False
                elif matches_name_only_split:
                    matches = matches_name_only_split
                    match_level = "Best"
                    specialty_matched = False
                else:
                    matches = []
                    match_level = None
                    specialty_matched = False
            scored_matches = [(match_level, m, 100, 100, specialty_matched) for m in matches]  # 100 = perfect match
        else:
            # For fuzzy strategies, aggregate results from all selected states
            all_results = []
            for s in states:
                if label == "Good: Last name match + fuzzy first name":
                    results_json = query_npi_api("", last, s)
                elif label == "Potential: Last name only match":
                    results_json = query_npi_api("", last, s)
                elif label == "Limited Potential: First name only match":
                    results_json = query_npi_api(first, "", s)
                else:
                    results_json = None
                if results_json and results_json.get('result_count', 0) > 0:
                    all_results.extend(results_json.get('results', []))
            matches = all_results

            for m in matches:
                npi = m.get("number")
                if npi in seen_npis:
                    continue
                # Fuzzy score for name
                if label == "Good: Last name match + fuzzy first name":
                    # Add former name logic here!
                    first_name_fuzzy = fuzz.token_sort_ratio(first, m.get("basic", {}).get("first_name", "")) >= fuzzy_threshold
                    former_name_match = matches_former_name(first, last, m.get("other_names", []))
                    last_name_match = m.get("basic", {}).get("last_name", "").strip().lower() == last.strip().lower()
                    if not (last_name_match and (first_name_fuzzy or former_name_match)):
                        continue
                    name_score = fuzz.token_sort_ratio(first, m.get("basic", {}).get("first_name", ""))
                    if name_score < fuzzy_threshold:
                        continue  # Skip if below threshold
                elif label == "Limited Potential: First name only match":
                    name_score = fuzz.token_sort_ratio(last, m.get("basic", {}).get("last_name", ""))
                    if name_score < fuzzy_threshold:
                        continue  # Skip if below threshold
                else:
                    name_score = 0
                # Fuzzy score for specialty (max score among all taxonomies)
                specialty_scores = [
                    fuzz.token_sort_ratio(specialty, t.get("desc", ""))
                    for t in m.get("taxonomies", [])
                ] if specialty else [0]
                specialty_score = max(specialty_scores) if specialty_scores else 0
                specialty_matched = specialty_score >= specialty_fuzzy_threshold if specialty else False
                scored_matches.append((match_level, m, name_score, specialty_score, specialty_matched))

            # Sort by average of name and specialty score, descending
            scored_matches.sort(key=lambda x: ((x[2] + x[3]) / 2), reverse=True)

        # Now apply the limit and build all_matches
        all_matches = []
        for match_level, m, name_score, specialty_score, specialty_matched in scored_matches:
            npi = m.get("number")
            if npi not in seen_npis:
                m["_name_score"] = name_score
                m["_specialty_score"] = specialty_score
                all_matches.append((match_level, m, specialty_matched))
                seen_npis.add(npi)
        # --- NY prioritization: sort NY matches to the top before slicing to limit ---
        def is_ny(match_tuple):
            m = match_tuple[1]
            addresses = m.get("addresses", [])
            return any(addr.get("state") == "NY" for addr in addresses)
        all_matches = sorted(all_matches, key=lambda x: not is_ny(x))
        all_matches = all_matches[:limit]
        if all_matches:
            return all_matches, all_matches[0][2]  # Return the specialty_matched of the top result

    return [], False  # No matches found, specialty_matched is False

def try_new_match(row, state, limit, search_type):
    matches, specialty_matched = match_provider(row, state, limit, search_type)
    if matches:
        return matches, row, specialty_matched
    return [], row, False

def try_both_split_and_unsplit(row, state, limit, search_type):
    matches, specialty_matched = match_provider(row, state, limit, search_type)
    if matches:
        return matches, row, specialty_matched

    # Try splitting last word as middle name if possible
    parts = str(row['First Name']).strip().split()
    if debug:
        print(f"Parts after split: {parts}")
    if (row.get("Middle Name", "") == "") and len(parts) > 1:
        row2 = row.copy()
        row2['First Name'] = " ".join(parts[:-1])
        row2['Middle Name'] = parts[-1]
        matches, specialty_matched = match_provider(row2, state, limit, search_type)
        if matches:
            return matches, row2, specialty_matched
    return [], row, False

def matches_former_name(first, last, other_names):
    """
    Checks if (first, last) matches any former name, with or without a middle name in 'first'.
    """
    first = first.strip().lower()
    last = last.strip().lower()
    # Check as-is
    for name in other_names or []:
        fn = (name.get("first_name", "") or "").strip().lower()
        ln = (name.get("last_name", "") or "").strip().lower()
        if fn == first and ln == last:
            return True
    # If first name contains a space, try stripping the last part (middle name)
    parts = first.split()
    if len(parts) > 1:
        first_no_middle = " ".join(parts[:-1])
        for name in other_names or []:
            fn = (name.get("first_name", "") or "").strip().lower()
            ln = (name.get("last_name", "") or "").strip().lower()
            if fn == first_no_middle and ln == last:
                return True
    return False

def get_strategy_state_passes(user_states):
    """
    Returns a list of state groups for matching passes.
    - If user_states is empty or contains NY, first pass is NY, second pass is all other states.
    - If user_states is only NY, only NY is checked.
    - If user_states does not contain NY, only those states are checked.
    """
    us_states = [
        "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "IA", "ID", "IL", "IN", "KS", "KY",
        "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH",
        "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY"
    ]
    user_states = [s.strip() for s in user_states if s.strip()]
    if not user_states:
        # No filter: NY first, then all others
        return [["NY"], [s for s in us_states if s != "NY"]]
    elif user_states == ["NY"]:
        # Only NY selected
        return [["NY"]]
    elif "NY" in user_states:
        # NY in filter: NY first, then others in filter (excluding NY)
        return [["NY"], [s for s in user_states if s != "NY"]]
    else:
        # NY not in filter: just use their filter
        return [user_states]


# -------------------- FILE UPLOAD & MATCHING --------------------
debug = False

uploaded_file = st.file_uploader("Upload Provider File (CSV)", type=["csv"])

if uploaded_file:
    df, error = validate_file(uploaded_file)
    if error:
        st.error(error)
    else:
        if debug:
            df = df[df["Last Name"].str.strip().str.lower() == "sandler"]  # use this to debug

        st.success(f"Uploaded {len(df)} rows successfully!")
        #df = split_first_and_middle(df)

        df["First Name"] = df["First Name"].fillna("").astype(str)
        df["Last Name"] = df["Last Name"].fillna("").astype(str)
        df["Middle Name"] = df["Middle Name"].fillna("").astype(str)
        df["Suffix"] = df["Suffix"].fillna("").astype(str)
        df["Specialty"] = df["Specialty"].fillna("").astype(str)
        def process_row(row):
            result_rows = []
            found_match = False

            if search_type == "Best: Full first and last name match":
                # NY-first logic as before
                state_passes = get_strategy_state_passes(state if isinstance(state, list) else [state])
                for state_group in state_passes:
                    matches, row_for_results, specialty_matched = try_new_match(
                        row, ",".join(state_group), limit, search_type
                    )
                    if matches:
                        found_match = True
                        for idx, (match_level, m, specialty_matched) in enumerate(matches, start=1):
                            basic = m.get("basic", {})
                            taxonomies = m.get("taxonomies", [])
                            addresses = m.get("addresses", [])
                            result_rows.append({
                                "First_Name_Supplied": row_for_results.get("First Name", ""),
                                "Last_Name_Supplied": row_for_results.get("Last Name", ""),
                                "FIRST_LAST": f"{row_for_results.get('First Name', '')} {row_for_results.get('Last Name', '')}".strip(),
                                #"Middle_Name_Supplied": row_for_results.get("Middle Name", ""),
                                "Specialty_Supplied": row_for_results.get("Specialty", ""), 
                                "Match_Level": match_level,
                                "Specialty_Matched": specialty_matched,
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
                                #"Address Match": "",
                            })
                        break  # Stop after first successful state group
            else:
                # For fuzzy strategies: search all selected states at once, then sort NY to top
                states_to_use = state if isinstance(state, list) else [state]
                matches, row_for_results, specialty_matched = try_new_match(
                    row, ",".join(states_to_use), limit*3, search_type  # get more than limit to allow NY sorting
                )
                if matches:
                    # Sort NY matches to the top
                    def is_ny(m):
                        # m can be a tuple (match_level, m, specialty_matched) or just a dict
                        match_obj = m[1] if isinstance(m, tuple) else m
                        addresses = match_obj.get("addresses", [])
                        return any(addr.get("state") == "NY" for addr in addresses)
                    matches = sorted(matches, key=lambda m: not is_ny(m))
                    matches = matches[:limit]  # Apply limit after sorting NY to top

                    found_match = True
                    for idx, (match_level, m, specialty_matched) in enumerate(matches[:limit], start=1):
                        basic = m.get("basic", {})
                        taxonomies = m.get("taxonomies", [])
                        addresses = m.get("addresses", [])
                        result_rows.append({
                            "First_Name_Supplied": row_for_results.get("First Name", ""),
                            "Last_Name_Supplied": row_for_results.get("Last Name", ""),
                            "FIRST_LAST": f"{row_for_results.get('First Name', '')} {row_for_results.get('Last Name', '')}".strip(),
                            #"Middle_Name_Supplied": row_for_results.get("Middle Name", ""),
                            "Specialty_Supplied": row_for_results.get("Specialty", ""), 
                            "Match_Level": match_level,
                            "Specialty_Matched": specialty_matched,
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
                            #"Address Match": "",
                        })

            if not found_match:
                result_rows.append({
                    "First_Name_Supplied": row.get("First Name", ""),
                    "Last_Name_Supplied": row.get("Last Name", ""),
                    "FIRST_LAST": f"{row.get('First Name', '')} {row.get('Last Name', '')}".strip(),
                    #"Middle_Name_Supplied": row.get("Middle Name", ""),
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
            return result_rows

        # In your "Click to Run Matching" button:
        if st.button("Click to Run Matching"):
            result_rows = []
            with st.spinner("🔎 Matching providers, please wait..."):
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                    results = list(executor.map(process_row, [row for _, row in df.iterrows()]))
                # Flatten the list of lists
                for rows in results:
                    result_rows.extend(rows)
            desired_columns = [
                "First_Name_Supplied", "Last_Name_Supplied", "FIRST_LAST", "Specialty_Supplied",
                "Match_Level", "Result_Count", "Result", "NPI",
                "First_Name", "Last_Name", "Middle_Name", "Creditials",
                "Specialty_1", "Specialty_2",
                "Address_1", "City_1", "State_1",
                "Address_2", "City_2", "State_2",
                "Address_3", "City_3", "State_3",
            ]
            result_df = pd.DataFrame(result_rows, columns=desired_columns)

            if show_stats:
                expected_set = set(npi_expected)
                result_df["NPI_in_Expected"] = result_df["NPI"].astype(str).apply(lambda npi: npi in expected_set)
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

    # --- Excel download button ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Results')
    output.seek(0)
    st.download_button(
        label="Download Results as Excel",
        data=output,
        file_name="npi_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("Please upload a provider file to get started.")
    # Don't run NPI comparison if no results

if show_stats and result_df is not None and not result_df.empty:
    result_npis = set(result_df["NPI"].dropna().astype(str))
    expected_npis = set(npi_expected)

    # Calculate counts
    in_both = result_npis & expected_npis
    expected_not_found = expected_npis - result_npis
    found_not_expected = result_npis - expected_npis

    st.markdown(f"### NPI Comparison")
    st.write(f"**Total in your results:** {len(result_npis)}")
    st.write(f"**Total in expected list:** {len(expected_npis)}")
    st.write(f"**Count found in both:** {len(in_both)}")
    st.write(f"**Count in expected but NOT in your results:** {len(expected_not_found)}")
    st.write(f"**Count in your results but NOT in expected:** {len(found_not_expected)}")

    # Optionally, show the lists
    with st.expander("NPIs in expected but NOT in your results"):
        st.write(sorted(expected_not_found))
    with st.expander("NPIs in your results but NOT in expected"):
        st.write(sorted(found_not_expected))

    # Print missing NPIs to terminal for debugging
    if expected_not_found:
        print("NPIs in expected but NOT in your results:")
        for npi in sorted(expected_not_found):
            print(npi)