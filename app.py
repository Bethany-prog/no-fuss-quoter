import streamlit as st
import math
import pandas as pd
from datetime import date, datetime
from fpdf import FPDF
import re
import json
import os
import urllib.parse

# --- DIRECTORIES ---
if not os.listdir(".") or "quotes" not in os.listdir("."):
    if not os.path.exists("quotes"): os.makedirs("quotes")

# 1. ACCESS CONTROL
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        st.title("🔒 Louis Quoting Tool Access")
        password = st.text_input("Access Code", type="password")
        if st.button("Unlock Engine"):
            if password == "NoFuss2026":
                st.session_state.password_correct = True
                st.rerun()
        return False
    return True

if not check_password():
    st.stop()

# --- VISUAL STYLING (THE BIG & BRIGHT UPDATE) ---
st.set_page_config(page_title="Louis Quoting Tool", layout="wide")
st.markdown("""
    <style>
    /* Background and Global */
    .main { background-color: #0E1117 !important; }
    
    /* Big Bright Headers */
    h1 { color: #00E676 !important; font-size: 50px !important; font-weight: 800 !important; text-transform: uppercase; letter-spacing: 2px; }
    h3 { color: #FFFFFF !important; border-left: 8px solid #3D5AFE; padding: 15px 20px; background-color: #1A1D2D; border-radius: 0 15px 15px 0; margin-top: 30px; font-size: 24px !important; }
    
    /* Giant Glowing Metrics */
    div.stMetric { 
        background-color: #1A1D2D !important; 
        padding: 30px !important; 
        border-radius: 20px !important; 
        border: 3px solid #3D5AFE !important;
        box-shadow: 0 10px 20px rgba(61, 90, 254, 0.3) !important;
    }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 42px !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 18px !important; text-transform: uppercase; }
    
    /* Control Tower Alerts */
    .urgent-card { 
        background-color: #2D1A1A; border-left: 10px solid #FF1744; padding: 20px; border-radius: 15px; margin-bottom: 15px;
        box-shadow: 0 5px 15px rgba(255, 23, 68, 0.2);
    }
    .warning-card { 
        background-color: #2D251A; border-left: 10px solid #FF9100; padding: 20px; border-radius: 15px; margin-bottom: 15px;
        box-shadow: 0 5px 15px rgba(255, 145, 0, 0.2);
    }

    /* Buttons */
    div.stButton > button { 
        background: linear-gradient(45deg, #3D5AFE, #00B0FF) !important; 
        color: white !important; border-radius: 12px !important; height: 60px !important; font-size: 20px !important; font-weight: bold !important; 
        border: none !important; transition: 0.3s !important;
    }
    div.stButton > button:hover { transform: scale(1.02) !important; box-shadow: 0 5px 15px rgba(61, 90, 254, 0.5) !important; }

    /* Summary Table Text */
    .summary-text { font-size: 22px !important; font-weight: 700 !important; color: #FFFFFF !important; display: flex; align-items: center; height: 100%; }
    .recurring-text { font-size: 18px !important; color: #90A4AE !important; font-style: italic; }
    
    /* Input Boxes */
    div[data-baseweb="input"] { background-color: #1A1D2D !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LOCKED MASTER DATA ---
CONFIG = {"WEIGHT_UNIT_KG": 30, "WEIGHT_HIRE": 6.60, "WEIGHT_LABOUR": 1.65, "TRUCK_PAYLOAD": 6000, "CARTAGE_RATE": 3.50}

STRUCT_LOGIC = {
    3:  {"bay": 3, "s_rate": 22.05, "m_rate": 22.05, "s_lab": 0.55, "m_lab": 0.55, "min_lab": 350.00},
    4:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 350.00},
    6:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 350.00},
    9:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 350.00},
    10: {"bay": 5, "s_rate": 23.00, "m_rate": 16.55, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 650.00},
    12: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 1500.00},
    15: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 1500.00},
    20: {"bay": 5, "s_rate": 19.95, "m_rate": 19.95, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 0.00},
}

GENERAL_PRODUCTS = {
    "Flooring": {
        "I-Trac®": {"rate": 23.40, "block": 46.80, "lab_fix": 4.65, "kg_sqm": 15.0},
        "Supa-Trac®": {"rate": 11.55, "block": 25.00, "lab_fix": 4.65, "kg_sqm": 4.5},
        "Plastorip": {"rate": 10.15, "block": 20.30, "lab_fix": 3.05, "kg_sqm": 4.0},
        "Rollout Flooring": {"rate": 7.10, "block": 15.00, "lab_fix": 3.05, "kg_sqm": 3.5}
    },
    "Accessories": {
        "30kg Weights": {"rate": 6.60, "lab_fix": 1.65, "kg": 30.0},
        "I-Trac® Ramps": {"rate": 42.00, "lab_fix": 0, "kg": 10.0},
        "Supa-Trac® Edging": {"rate": 6.70, "lab_fix": 0, "kg": 1.0},
        "Plastorip Edging": {"rate": 1.65, "lab_fix": 0, "kg": 0.5},
        "MOJO Barriers": {"rate": 70.00, "lab_p": 0.40, "kg": 60.0},
        "Rollout Flooring - Ramps": {"rate": 6.60, "lab_fix": 0, "kg": 2.0},
        "Rollout Flooring - joiners": {"rate": 6.60, "lab_fix": 0, "kg": 0.1}
    }
}

STAGES = ["Quoted", "Accepted", "Paid", "On Hire", "Returned"]
STAGE_COLORS = {"Quoted": "#FF9100", "Accepted": "#00E676", "Paid": "#00B8D4", "On Hire": "#D500F9", "Returned": "#757575"}

# --- SESSION STATE ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Is_Marquee", "Discount"])
if 'status' not in st.session_state: st.session_state.status = "Quoted"
if 'active_project' not in st.session_state: st.session_state.active_project = "New Project"
if 'start_d' not in st.session_state: st.session_state.start_d = date.today()
if 'end_d' not in st.session_state: st.session_state.end_d = date.today()
if 'km' not in st.session_state: st.session_state.km = 0.0

# --- SCAN ARCHIVE FOR DASHBOARD ---
quoted_files = [f for f in os.listdir("quotes") if f.endswith(".json")]
followup_list = []
for f_name in quoted_files:
    try:
        with open(f"quotes/{f_name}", "r") as f:
            p_data = json.load(f)
            if p_data.get("status") == "Quoted" and "start_date" in p_data:
                sd = datetime.strptime(p_data["start_date"], '%Y-%m-%d').date()
                diff = (sd - date.today()).days
                if 0 <= diff <= 28:
                    followup_list.append({"Project": p_data.get("proj", "Unknown"), "Start Date": sd.strftime('%d/%m/%Y'), "Days Left": diff, "Status": "🚨 URGENT" if diff <= 14 else "⚠️ WARNING"})
    except: continue

# --- SIDEBAR ---
st.sidebar.title("📁 ARCHIVE SYSTEM")
if st.sidebar.button("➕ NEW PROJECT"):
    st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.session_state.status = "Quoted"; st.session_state.km = 0.0; st.rerun()

st.sidebar.divider()
st.session_state.active_project = st.sidebar.text_input("Project Label", st.session_state.active_project)
if st.sidebar.button("💾 SAVE PROJECT"):
    data = {"status": st.session_state.status, "items": st.session_state.df.to_dict(orient='records'), "proj": st.session_state.active_project, "start_date": str(st.session_state.start_d), "end_date": str(st.session_state.end_d), "km": st.session_state.km}
    with open(f"quotes/{st.session_state.active_project}.json", "w") as f: json.dump(data, f)
    st.sidebar.success("Saved!")

saved_quotes = sorted([f.replace(".json", "") for f in os.listdir("quotes") if f.endswith(".json")])
load_choice = st.sidebar.selectbox("Load Project", ["-- Select --"] + saved_quotes)
cl, cd = st.sidebar.columns(2)
if cl.button("📂 LOAD") and load_choice != "-- Select --":
    with open(f"quotes/{load_choice}.json", "r") as f:
        loaded = json.load(f); st.session_state.df = pd.DataFrame(loaded["items"]); st.session_state.status = loaded.get("status", "Quoted"); st.session_state.active_project = loaded.get("proj", load_choice)
        if "start_date" in loaded: st.session_state.start_d = datetime.strptime(loaded["start_date"], '%Y-%m-%d').date()
        if "end_date" in loaded: st.session_state.end_d = datetime.strptime(loaded["end_date"], '%Y-%m-%d').date()
        if "km" in loaded: st.session_state.km = float(loaded["km"])
        st.rerun()
if cd.button("🗑️ DELETE"): os.remove(f"quotes/{load_choice}.json"); st.rerun()

# --- MAIN UI ---
st.title("⚡ NO FUSS QUOTER")

# --- CONTROL TOWER ---
if followup_list:
    st.markdown("### 📡 FOLLOW-UP CONTROL TOWER")
    for item in followup_list:
        card_class = "urgent-card" if "🚨" in item['Status'] else "warning-card"
        st.markdown(f"""
            <div class="{card_class}">
                <span style="font-size: 20px;">{item['Status']} | <strong>{item['Project']}</strong></span><br>
                Starts: {item['Start Date']} ({item['Days Left']} days remaining)
            </div>
        """, unsafe_allow_html=True)
    st.divider()

# --- INPUT SECTION ---
st.markdown(f"### 📍 Project: {st.session_state.active_project}")
try: s_idx = STAGES.index(st.session_state.status)
except: s_idx = 0
st.session_state.status = st.selectbox("Stage", options=STAGES, index=s_idx)
st.markdown(f"<div style='height: 15px; background-color: {STAGE_COLORS[st.session_state.status]}; border-radius: 10px; margin-bottom: 30px;'></div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
st.session_state.start_d = c1.date_input("Hire Start", value=st.session_state.start_d)
st.session_state.end_d = c2.date_input("Hire End", value=st.session_state.end_d)
st.session_state.km = c3.number_input("KM (One-Way)", min_value=0.0, value=st.session_state.km if st.session_state.km > 0 else None, placeholder="KM...")

diff = (st.session_state.end_d - st.session_state.start_d).days
weeks = math.ceil(diff / 7) if diff > 0 else 1
st.markdown(f"## ⏱️ DURATION: {diff // 7} Weeks, {diff % 7} Days")

st.markdown("#### 💳 BILLING")
b1, b2 = st.columns(2)
cartage_mode = b1.segmented_control("Cartage", ["Charge", "Free"], default="Charge")
labour_mode = b2.segmented_control("Labour", ["Separate", "Include in Hire", "Free"], default="Separate")

st.divider(); col_mq, col_cat = st.columns(2)

# --- ADDING ITEMS ---
with col_mq:
    st.markdown("### ⚡ STRUCTURES")
    m_in = st.text_input("Size (10x15)")
    m_q = st.number_input("Qty", min_value=1, value=None, key="mq")
    m_sec = st.radio("Securing", ["Weights", "Pegging"], horizontal=True)
    if st.button("ADD MARQUEE") and m_in and m_q:
        nums = re.findall(r'\d+', m_in)
        if len(nums) >= 2:
            span, length = int(nums[0]), int(nums[1])
            logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
            sqm = span*length; rate = logic['s_rate'] if (length/logic['bay']) <= 1 else logic['m_rate']
            h1 = sqm * rate * m_q; l1 = h1 * logic['s_lab']
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
                "Qty": m_q, "Product": f"Structure {span}m x {length}m", "Unit Rate": sqm*rate, "Total": 0.0, "Min_Lab": logic['min_lab'], "Raw_Lab": l1, "Lab_Math": f"Labour: ${l1:,.2f}", "KG": (sqm*15)*m_q, "Is_Marquee": True, "Discount": 0.0
            }])], ignore_index=True)
            if m_sec == "Weights":
                w_tot = int((((length/logic['bay'])+1)*2)*6*m_q)
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
                    "Qty": w_tot, "Product": "30kg Weights", "Unit Rate": 6.60, "Total": 0.0, "Min_Lab": 0, "Raw_Lab": w_tot*1.65, "Lab_Math": "Weights Lab", "KG": w_tot*30, "Is_Marquee": True, "Discount": 0.0
                }])], ignore_index=True)
            st.rerun()

with col_cat:
    st.markdown("### 🪵 FLOORING")
    p_sel = st.selectbox("Product", list(GENERAL_PRODUCTS["Flooring"].keys()) + list(GENERAL_PRODUCTS["Accessories"].keys()))
    f_qty = st.number_input("Amount", min_value=0.0, value=None)
    if st.button("ADD TO QUOTE") and f_qty:
        data = {**GENERAL_PRODUCTS["Flooring"], **GENERAL_PRODUCTS["Accessories"]}[p_sel]
        f_rate = (data['block']/4) if (weeks >= 4 and 'block' in data) else data.get('rate', data.get('rate', 70))
        h1 = f_qty * f_rate; l1 = f_qty * data.get('lab_fix', (h1 * data.get('lab_p', 0)))
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
            "Qty": f_qty, "Product": p_sel, "Unit Rate": f_rate, "Total": 0.0, "Min_Lab": 0, "Raw_Lab": l1, "Lab_Math": f"Lab: ${l1:,.2f}", "KG": f_qty * data.get('kg_sqm', data.get('kg', 0)), "Is_Marquee": False, "Discount": 0.0
        }])], ignore_index=True); st.rerun()

# --- QUOTE SUMMARY ---
if not st.session_state.df.empty:
    st.divider(); st.markdown("### 📝 QUOTE SUMMARY")
    hc = st.columns([0.5, 3, 0.8, 1.2, 1, 1.2])
    cols = ["", "ITEM", "QTY", "RATE", "DISC%", "TOTAL"]
    for i, col in enumerate(hc): col.write(f"**{cols[i]}**")
    
    h_tot_c = 0.0; h_wk1_gear = 0.0; total_kg = 0.0; ph_maths = []; pl_maths = []
    
    for idx, row in st.session_state.df.iterrows():
        qty, brate, dm = row["Qty"], row["Unit Rate"], (1 - (row["Discount"]/100))
        total_kg += row["KG"]; h_wk1_gear += (qty * brate)
        
        c = st.columns([0.5, 3, 0.8, 1.2, 1, 1.2])
        if c[0].button("🗑️", key=f"del_{idx}"): st.session_state.df.drop(idx, inplace=True); st.rerun()
        
        # Week 1
        wk1_t = (qty * brate + row["Raw_Lab"]) * dm if labour_mode == "Include in Hire" else (qty * brate) * dm
        h_tot_c += wk1_t; ph_maths.append(f"{row['Product']} Wk1: ${wk1_t:,.2f}")
        c[1].markdown(f"<div class='summary-text'>{row['Product']} - WK 1</div>", unsafe_allow_html=True)
        c[2].markdown(f"<div class='summary-text'>{qty:,.0f}</div>", unsafe_allow_html=True)
        c[3].markdown(f"<div class='summary-text'>${wk1_t/qty:,.2f}</div>", unsafe_allow_html=True)
        row["Discount"] = c[4].number_input("", 0.0, 100.0, float(row["Discount"]), 1.0, key=f"d_{idx}", label_visibility="collapsed")
        c[5].markdown(f"<div class='summary-text'>${wk1_t:,.2f}</div>", unsafe_allow_html=True)

        if weeks > 1:
            r_rate = brate * 0.5 if row["Is_Marquee"] and "Weight" not in row["Product"] else brate
            r_tot = qty * r_rate * (weeks-1) * dm; h_tot_c += r_tot; ph_maths.append(f"Recurring: ${r_tot:,.2f}")
            cb = st.columns([0.5, 3, 0.8, 1.2, 1, 1.2])
            cb[1].markdown(f"<div class='summary-text recurring-text'>└ RECURRING HIRE (Wks 2-{weeks})</div>", unsafe_allow_html=True)
            cb[2].markdown(f"<div class='summary-text recurring-text'>{qty:,.0f}</div>", unsafe_allow_html=True)
            cb[3].markdown(f"<div class='summary-text recurring-text'>${r_rate*dm:,.2f}</div>", unsafe_allow_html=True)
            cb[5].markdown(f"<div class='summary-text recurring-text'>${r_tot:,.2f}</div>", unsafe_allow_html=True)

    # --- FINAL METRICS ---
    trucks = math.ceil(total_kg / 6000) if total_kg > 0 else 1
    waiver = h_wk1_gear * 0.07; cartage = trucks * st.session_state.km * 4 * 3.50 if cartage_mode == "Charge" else 0
    d_lab = max(st.session_state.df["Min_Lab"].max(), st.session_state.df["Raw_Lab"].sum()) if labour_mode == "Separate" else 0
    
    st.divider()
    m = st.columns(6)
    m[0].metric("HIRE", f"${h_tot_c:,.2f}"); m[1].metric("LABOUR", f"${d_lab:,.2f}"); m[2].metric("WAIVER", f"${waiver:,.2f}")
    m[3].metric("CARTAGE", f"${cartage:,.2f}"); m[4].metric("WEIGHT", f"{total_kg:,.0f}kg"); m[5].metric("TRUCKS", f"{trucks}")
    
    grand = h_tot_c + d_lab + waiver + cartage
    st.markdown(f"<h1>GRAND TOTAL: ${grand:,.2f}</h1>", unsafe_allow_html=True)
