
import streamlit as st
from datetime import datetime, timedelta
import requests
import pandas as pd

# Mapping for categories to NAICS/PSC codes
CATEGORY_CODE_MAP = {
    "Bottled water": {"NAICS": ["312112"], "PSC": ["8945"]},
    "Office Supplies": {"NAICS": ["339940"], "PSC": ["7510", "7520"]},
    "Stainless Steel Sheets": {"NAICS": ["331110"], "PSC": ["9515"]},
    "Aerospace Metals": {"NAICS": ["336413"], "PSC": ["1560"]},
    "Emergency Kits": {"NAICS": ["339113"], "PSC": ["6545"]},
    "Logistics Services": {"NAICS": ["484110"], "PSC": ["V112", "V119"]},
    "Custom Pallets & Crates": {"NAICS": ["321920"], "PSC": ["8115", "3990"]},
    "Construction Materials": {"NAICS": ["327320", "321999"], "PSC": ["5610", "5615"]},
    "Produce (Fruits & Vegetables)": {"NAICS": ["424480", "311991"], "PSC": ["8915"]},
    "Janitorial Supplies": {"NAICS": ["325612"], "PSC": ["7920", "7930"]}
}

TARGET_AGENCIES = [
    "Defense Commissary Agency",
    "DLA Troop Support",
    "Department of Defense",
    "Department of Agriculture",
    "Department of Veterans Affairs",
    "Department of Homeland Security",
    "Bureau of Prisons",
    "Federal Emergency Management Agency"
]

st.set_page_config(page_title="Gov Contract Scout", layout="wide")

st.title("📦 Government Contract Opportunity Scout")
st.markdown("Use the checkboxes below to find contracts by product type and agency.")

# Select filters
selected_categories = st.multiselect("Select Material Categories:", list(CATEGORY_CODE_MAP.keys()))
selected_agencies = st.multiselect("Select Agencies (optional):", TARGET_AGENCIES, default=TARGET_AGENCIES)

start_date = st.date_input("Start Date", datetime.today() - timedelta(days=30))
end_date = st.date_input("End Date", datetime.today())

limit = st.number_input("Number of results to return:", 10, 100, 50)

# Trigger search
if st.button("🔍 Search Contracts"):
    api_key = st.secrets["SAM_API_KEY"]
    base_url = "https://api.sam.gov/opportunities/v2/search"
    headers = {"accept": "application/json"}

    all_naics = []
    all_psc = []

    for cat in selected_categories:
        codes = CATEGORY_CODE_MAP[cat]
        all_naics.extend(codes["NAICS"])
        all_psc.extend(codes["PSC"])

    params = {
        "api_key": api_key,
        "limit": limit,
        "postedFrom": start_date.strftime("%m/%d/%Y"),
        "postedTo": end_date.strftime("%m/%d/%Y"),
        "naicsCodes": ",".join(all_naics),
        "pscCodes": ",".join(all_psc),
        "agencies": ",".join(selected_agencies)
    }

    response = requests.get(base_url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        results = data.get("opportunities", [])
        if results:
            df = pd.DataFrame([{
                "Title": r.get("title"),
                "ID": r.get("noticeId"),
                "Agency": r.get("department", {}).get("name", ""),
                "Posted": r.get("postedDate"),
                "Deadline": r.get("responseDeadline"),
                "Link": f"https://sam.gov/opp/{r.get('noticeId')}/view"
            } for r in results])
            st.success(f"Found {len(results)} opportunities.")
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"), "contracts.csv", "text/csv")
        else:
            st.warning("No opportunities found for your criteria.")
    else:
        st.error(f"API Error: {response.status_code} - {response.text}")
