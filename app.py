import streamlit as st
import json, os, scraper, pytz
from datetime import datetime, timedelta

# TRIGGER: Force update if file is missing OR older than 1 hour
DATA_FILE = "jobs_data.json"
if os.path.exists(DATA_FILE):
    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(DATA_FILE))
    if file_age > timedelta(hours=1):
        os.remove(DATA_FILE)
        scraper.run_scraper()
else:
    scraper.run_scraper()

st.set_page_config(page_title="IBEW Job Tracker", layout="centered")
st.title("⚡IBEW Calls⚡")

user_tz_str = st.context.timezone 
if user_tz_str:
    now = datetime.now(pytz.utc).astimezone(pytz.timezone(user_tz_str))
    timestamp = now.strftime("%A, %B %d, %Y at %I:%M %p %Z")
else:
    timestamp = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p (UTC)")

st.write(f"⏱️ **Data Last Updated:** {timestamp}")
st.write("**Created by:** Austin Benton LU177")
st.divider()

try:
    with open("jobs_data.json", "r") as f:
        all_locals = json.load(f).get("locals", [])
except:
    st.error("No valid data storage found.")
    all_locals = []

st.write("### 🔍 Search & Filter Locals")
col_search, col_check = st.columns([3, 1])
with col_search:
    search_query = st.text_input("Search by Local or State/City", "").strip().upper()
with col_check:
    st.write("##")
    filter_has_work = st.checkbox("Has Work", value=False)

sort_option = st.selectbox("Sort by:", ["Local # (Lowest First)", "State (A-Z)", "Wage Scale (Highest First)", "# of Calls (Highest First)"])
st.divider()

filtered_locals = [l for l in all_locals if (not search_query or search_query in l["union_name"].upper() or search_query in l["state"].upper()) and (not filter_has_work or l["has_work"])]

if sort_option == "State (A-Z)": filtered_locals.sort(key=lambda x: x["state"])
elif sort_option == "Wage Scale (Highest First)": filtered_locals.sort(key=lambda x: x["highest_wage"], reverse=True)
elif sort_option == "# of Calls (Highest First)": filtered_locals.sort(key=lambda x: x["call_count"], reverse=True)

if not filtered_locals: st.info("No matching locals found.")
else:
    for local in filtered_locals:
        if local["union_name"] != "Unknown Local":
            if local.get("link"): st.subheader(f"[{local['union_name']}]({local['link']})")
            else: st.subheader(local['union_name'])
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.caption("**Wage Scale(s)**")
                st.text(local["wage_scale_display"])
            with c2:
                st.caption("**Job Calls Status**")
                st.write(local["status_info"])
            st.divider()