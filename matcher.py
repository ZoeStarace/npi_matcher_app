import requests
from fuzzywuzzy import fuzz

BASE_URL = "https://npiregistry.cms.hhs.gov/api/"

def call_npi_api(first_name, last_name, state=None, limit=10):
    params = {
        "version": "2.1",
        "first_name": first_name,
        "last_name": last_name,
        "state": state,
        "limit": limit
    }
    response = requests.get(BASE_URL, params=params)
    return response.json() if response.status_code == 200 else None

def match_provider(row, state=None, limit=10):
    # Step 1: Try full match
    result = call_npi_api(row["First Name"], row["Last Name"], state, limit)
    if result and "results" in result:
        return "Full Match", result["results"]

    # Step 2: Try fuzzy first name
    result = call_npi_api("", row["Last Name"], state, limit)
    if result and "results" in result:
        for r in result["results"]:
            if "basic" in r and fuzz.partial_ratio(row["First Name"].lower(), r["basic"].get("first_name", "").lower()) > 85:
                return "Fuzzy First Name", [r]

    # Step 3: Last name only
    if result and "results" in result:
        return "Last Name Only", result["results"]

    # Step 4: First name only
    result = call_npi_api(row["First Name"], "", state, limit)
    if result and "results" in result:
        return "First Name Only", result["results"]

    return "No Match", []