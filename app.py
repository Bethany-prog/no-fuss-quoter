import streamlit as st
import math
import pandas as pd
from datetime import date
import re
import json
import os

# --- v32.9 LAYOUT RESTORATION & BRANDING ---
if not os.path.exists("quotes"):
    os.makedirs("quotes")

# 1. ACCESS CONTROL
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        st.title("🔒 Unified Engine Access")
        password = st.text_input("Access Code", type="password")
        if st.button("Unlock Engine"):
            if password == "NoFuss2026":
                st.session_state.password_correct = True
                st.rerun()
        return False
    return True

if not check_password():
    st.stop()

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #FFFFFF !important; }
    h3 { color: #FFFFFF !important; border-left: 5px solid #00E676; padding: 10px 15px; background-color: #1A1D2D; border-radius: 0 10px 10px 0; margin-top: 20px; }
    div.stMetric { background-color: #1A1D2D !important; padding: 20px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 16px !important; }
    /* Checklist Box */
    .guardrail-box { background-color: #F8F9FA; padding: 20px; border-radius: 10px; border: 1px solid #D1D3D4; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- MASTER DATA ---
STAGES = ["Quoted", "Accepted", "Paid", "On Hire", "Returned"]
STAGE_COLORS = {"Quoted": "#FF9100", "Accepted": "#00E676", "Paid": "#00B8D4", "On Hire": "#D500F9", "Returned": "#757575"}
CONFIG = {"WEIGHT_UNIT_KG": 30, "WEIGHT_HIRE": 6.60, "WEIGHT_LABOUR": 1.65, "TRUCK_PAYLOAD": 6000, "CARTAGE_RATE": 3.50}

# --- SESSION STATE ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Is_Marquee", "Hire_Math_Str"])
if 'status' not in st.session_state:
    st.session_state.status = "Quoted"
if 'active_project' not in st.session_state:
    st.session_state.active_project = "New Project"

# --- SIDEBAR & ARCHIVE ---
st.sidebar.title("📁 Archive Manager")
st.session_state.active_project = st.sidebar.text_input("Project Label", st.session_state.active_project)
if st.sidebar.button("💾 SAVE PROJECT"):
    data = {"status": st.session_state.status, "items": st.session_state.df.to_dict(orient='records'), "proj": st.session_state.active_project}
    with open(f"quotes/{st.session_state.active_project}.json", "w") as f: json.dump(data, f)
    st.sidebar.success(f"Archived: {st.session_state.active_project}")

saved_quotes = [f.replace(".json", "") for f in os.listdir("quotes") if f.endswith(".json")]
load_choice = st.sidebar.selectbox("Retrieve Project", ["None"] + saved_quotes)
if st.sidebar.button("📂 LOAD") and load_choice != "None":
    with open(f"quotes/{load_choice}.json", "r") as f:
        loaded = json.load(f); st.session_state.df = pd.DataFrame(loaded["items"])
        st.session_state.status = loaded.get("status", "Quoted") if loaded.get("status") in STAGES else "Quoted"
        st.session_state.active_project = loaded.get("proj", load_choice); st.rerun()

# --- UI WORKFLOW ---
st.title("📦 Louis Quoting Tool")
st.markdown(f"### 📍 Project: {st.session_state.active_project}")
st.session_state.status = st.selectbox("Current Workflow Stage", options=STAGES, index=STAGES.index(st.session_state.status))
st.markdown(f"<div style='height: 12px; background-color: {STAGE_COLORS[st.session_state.status]}; border-radius: 6px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# DATE SELECTORS (AUS Format)
c1, c2, c3 = st.columns(3)
start_d = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
end_d = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
km_in = c3.number_input("One-Way KM", min_value=0.0)
weeks = math.ceil(((end_d - start_d).days) / 7) if (end_d - start_d).days > 0 else 1

st.divider()
# ... [Calculator Add Buttons go here - logic locked as per previous instructions] ...

if not st.session_state.df.empty:
    st.data_editor(st.session_state.df[["Qty", "Product", "Unit Rate", "Total"]], use_container_width=True)
    
    h_tot = st.session_state.df["Total"].sum()
    total_kg = st.session_state.df["KG"].sum()
    trucks = math.ceil(total_kg / CONFIG["TRUCK_PAYLOAD"]) if total_kg > 0 else 1
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE", f"${h_tot:,.2f}"); m3.metric("LOAD", f"{total_kg:,.0f}kg"); m4.metric("TRUCKS", f"{trucks}")

    # --- THE CLEAN CHECKLIST ---
    st.markdown("### 🛠️ Checklist")
    st.markdown("<div class='guardrail-box'>", unsafe_allow_html=True)
    
    if st.session_state.status == "Quoted":
        st.checkbox("Email / enquiry printed", value=False)
        st.checkbox("Quote printed and paperclipped to the front", value=False)
    else:
        st.write("No specific office actions for this stage.")
    
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("RESET ENGINE"): 
        st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns)
        st.rerun()
