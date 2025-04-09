
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Contract Replay Tester", layout="wide")
st.title("🧪 Contract Replay Tester")
st.markdown("Select a known past contract to simulate a real-time SAM.gov query and verify if the tool would surface it.")

# Load the uploaded CSV of historical contracts
@st.cache_data
def load_data():
    return pd.read_csv("government_contracts_2025-04-05.csv")

df = load_data()

# Show user a dropdown of past contracts to test
contract_titles = df["title"].tolist()
selected_title = st.selectbox("Select a Past Contract to Test:", contract_titles)

# Retrieve selected contract data
contract = df[df["title"] == selected_title].iloc[0]
st.write("**Agency:**", contract["agency"])
st.write("**Award Date:**", contract["award_date"])
st.write("**Contractor:**", contract["contractor"])
st.write("**Category:**", contract["category"])
st.write("**Description:**", contract["description"])

# Use award_date +/- 15 days as query range
start_dt = datetime.strptime(contract["award_date"], "%m/%d/%Y") - timedelta(days=15)
end_dt = datetime.strptime(contract["award_date"], "%m/%d/%Y") + timedelta(days=15)

# Extract keywords from description (basic split and filtering)
keywords = " ".join(contract["description"].split()[:6])  # simple keyword seed
agency = contract["agency"]

# User launches replay test
if st.button("🔍 Run Test Query on SAM.gov"):
    api_key = st.secrets["SAM_API_KEY"]
    base_url = "https://api.sam.gov/opportunities/v2/search"
    headers = {"accept": "application/json"}

    params = {
        "api_key": api_key,
        "postedFrom": start_dt.strftime("%m/%d/%Y"),
        "postedTo": end_dt.strftime("%m/%d/%Y"),
        "keywords": keywords,
        "agencies": agency,
        "limit": 50
    }

    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get("opportunities", [])
        if results:
            st.success(f"Found {len(results)} opportunities matching the test criteria.")
            for r in results:
                st.markdown(f"**{r.get('title')}**  
"
                            f"Agency: {r.get('department', {}).get('name', '')}  
"
                            f"Posted: {r.get('postedDate')}  
"
                            f"Deadline: {r.get('responseDeadline')}  
"
                            f"[View on SAM.gov](https://sam.gov/opp/{r.get('noticeId')}/view)")
        else:
            st.warning("No opportunities found for this contract scenario.")
    else:
        st.error(f"API Error {response.status_code}: {response.text}")
