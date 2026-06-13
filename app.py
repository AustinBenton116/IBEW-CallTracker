import streamlit as st
import json
import os
import scraper
from datetime import datetime

# TRIGGER: This ensures the data exists when the app launches
if not os.path.exists("jobs_data.json"):
    scraper.run_scraper()

st.set_page_config(page_title="IBEW Job Tracker", layout="centered")
st.title("⚡ IBEW Job Calls")

# Generate the dynamic launcher timestamp live
timestamp = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
st.write(f"⏱️ **Data Last Updated:** {timestamp}")
st.divider()

try:
    with open("jobs_data.json", "r") as f:
        data = json.load(f)
        all_locals = data.get("locals", [])
except Exception:
    st.error("No valid data storage found. Run scraper.py first.")
    all_locals = []

# ==========================================
# SEARCH, FILTER & SORT CONTROLS
# ==========================================
st.write("### 🔍 Search & Filter Locals")

# Row 1: Search text input and "Has Work" toggle checkbox
col_search, col_check = st.columns([3, 1])
with col_search:
    search_query = st.text_input("Search by Local name or State (e.g., 'Local 13' or 'IL')", "").strip().upper()
with col_check:
    st.write("##") # Form vertical balancing block
    filter_has_work = st.checkbox("Has Work Only", value=False)

# Row 2: Universal Sorting Control Dropdown
sort_option = st.selectbox(
    "Sort rows by:",
    options=["Default List Order", "State (A-Z)", "Wage Scale (Highest First)", "Amount of Calls (Highest First)"]
)

st.divider()

# --- Process Filters ---
filtered_locals = []
for local in all_locals:
    name_upper = local["union_name"].upper()
    state_upper = local["state"].upper()
    
    # 1. Evaluate Search Terms
    if search_query and (search_query not in name_upper and search_query not in state_upper):
        continue
        
    # 2. Evaluate Work Status Condition Checkbox
    if filter_has_work and not local["has_work"]:
        continue
        
    filtered_locals.append(local)

# --- Process Sorting Requests ---
if sort_option == "State (A-Z)":
    filtered_locals = sorted(filtered_locals, key=lambda x: x["state"])
elif sort_option == "Wage Scale (Highest First)":
    filtered_locals = sorted(filtered_locals, key=lambda x: x["highest_wage"], reverse=True)
elif sort_option == "Amount of Calls (Highest First)":
    filtered_locals = sorted(filtered_locals, key=lambda x: x["call_count"], reverse=True)


# --- Render Filtered & Sorted Display ---
if not filtered_locals:
    st.info("No matching locals found based on your current search filters.")
else:
    for local in filtered_locals:
        if local["union_name"] != "Unknown Local":
            st.subheader(local["union_name"])
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.caption("**Wage Scale(s)**")
                st.text(local["wage_scale_display"])
            
            with col2:
                st.caption("**Job Calls Status**")
                st.write(local["status_info"])
            
            st.divider()