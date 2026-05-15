import streamlit as st
import math
import pandas as pd
from datetime import date, datetime
from fpdf import FPDF
import re
import json
import os

# --- DIRECTORIES ---
if not os.path.exists("quotes"):
    os.makedirs("quotes")

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

# --- VISUAL STYLING (v36.2 - STABLE & POLISHED) ---
st.set_page_config(page_title="Louis Quoting Tool", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #F4F7F9 !important; }
    h1 { color: #1A1D2D !important; font-size: 48px !important; font-weight: 900 !important; margin-bottom: 0px; }
    h3 { color: #FFFFFF !important; border-left: 10px solid #00E676; padding: 15px; background-color: #1A1D2D; border-radius: 0 10px 10px 0; font-size: 22px !important; }
    
    div.stMetric { 
        background-color: #FFFFFF !important; 
        padding: 25px !important; 
        border-radius: 15px !important; 
        border: 3px solid #3D5AFE !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="stMetricValue"] { color: #3D5AFE !important; font-size: 34px !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] p { color: #5F6368 !important; font-weight: 700 !important; text-transform: uppercase; }

    .item-text { font-size: 19px !important; font-weight: 600 !important; color: #202124; }
    .item-sub { font-size: 16px !important; color: #70757A; font-style: italic; }
    
    .gt-banner {
        background: #1A1D2D; color: #00E676; padding: 35px; border-radius: 20px;
        text-align: right; font-size: 44px !important; font-weight: 900;
        margin-top: 30px; border: 5px solid #00E676;
    }
    </style>
    """, unsafe_allow_html=True)

# --- MASTER DATA ---
CONFIG = {"W_KG": 30, "W_H": 6.60, "W_L": 1.65, "PAYLOAD": 6000, "KM_RATE": 3.50}
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
        "I-Trac®": {"rate": 23.40, "block": 46.80, "lab_fix": 4.65, "kg": 15.0},
        "Supa-Trac®": {"rate": 11.55, "block": 25.00, "lab_fix": 4.65, "kg": 4.5},
        "Plastorip": {"rate": 10.15, "block": 20.30, "lab_fix": 3.05, "kg": 4.0},
        "Rollout": {"rate": 7.10, "block": 15.00, "lab_fix": 3.05, "kg": 3.5}
    },
    "Accessories": {
        "Weights": {"rate": 6.60, "lab_fix": 1.65, "kg": 30.0},
        "I-Trac Ramps": {"rate": 42.00, "lab_fix": 0, "kg": 10.0},
        "Barrier": {"rate": 70.00, "lab_p": 0.40, "kg": 60.0}
    }
}
STAGES = ["Quoted", "Accepted", "Paid", "On Hire", "Returned"]

# --- SESSION STATE ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount"])
if 'status' not in st.session_state: st.session_state.status = "Quoted"
if 'proj' not in st.session_state: st.session_state.proj = "New Project"
if 'km' not in st.session_state: st.session_state.km = 0.0
if 'start_d' not in st.session_state: st.session_state.start_d = date.today()
if 'end_d' not in st.session_state: st.session_state.end_d = date.today()

# --- SAFE LOAD FUNC ---
def load_project_safe(fname):
    try:
        with open(f"quotes/{fname}", "r") as f:
            d = json.load(f)
            st.session_state.df = pd.DataFrame(d["items"])
            if "Discount" not in st.session_state.df.columns: st.session_state.df["Discount"] = 0.0
            st.session_state.status = d.get("status", "Quoted")
            st.session_state.proj = d.get("proj", fname.replace(".json", ""))
            
            # Safe Date Parsing
            try: st.session_state.start_d = datetime.strptime(d.get("start_date"), '%Y-%m-%d').date()
            except: st.session_state.start_d = date.today()
            try: st.session_state.end_d = datetime.strptime(d.get("end_date"), '%Y-%m-%d').date()
            except: st.session_state.end_d = date.today()
            
            # Safe KM Parsing (The Crash Fix)
            km_raw = d.get("km", 0.0)
            st.session_state.km = float(km_raw) if km_raw is not None else 0.0
    except Exception as e:
        st.error(f"Error loading file: {e}")

# --- MAIN UI ---
st.title("📦 NO FUSS QUOTER")

# --- CONTROL TOWER ---
quoted_files = [f for f in os.listdir("quotes") if f.endswith(".json")]
followups = []
for fn in quoted_files:
    try:
        with open(f"quotes/{fn}", "r") as f:
            p = json.load(f)
            if p.get("status") == "Quoted" and p.get("start_date"):
                sd = datetime.strptime(p["start_date"], '%Y-%m-%d').date()
                diff = (sd - date.today()).days
                if 0 <= diff <= 28: followups.append({"name": p.get("proj", "Unknown"), "days": diff, "file": fn})
    except: continue

if followups:
    st.markdown("### 📡 ACTIVE FOLLOW-UPS")
    for f in followups:
        cl, cr = st.columns([5, 1])
        cl.warning(f"**{f['name']}** starts in {f['days']} days.")
        if cr.button("📂 LOAD", key=f"edit_{f['file']}"):
            load_project_safe(f['file']); st.rerun()

# --- SIDEBAR ---
st.sidebar.title("📁 ARCHIVE")
if st.sidebar.button("➕ START NEW"):
    st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.session_state.km = 0.0; st.rerun()
st.session_state.proj = st.sidebar.text_input("Project Label", st.session_state.proj)
if st.sidebar.button("💾 SAVE PROJECT"):
    data = {"status": st.session_state.status, "items": st.session_state.df.to_dict(orient='records'), "proj": st.session_state.proj, "start_date": str(st.session_state.start_d), "end_date": str(st.session_state.end_d), "km": st.session_state.km}
    with open(f"quotes/{st.session_state.proj}.json", "w") as f: json.dump(data, f)
    st.sidebar.success("Saved!")

# --- WORKSPACE ---
st.markdown(f"### 📍 Project: {st.session_state.proj}")
st.session_state.status = st.selectbox("Stage", STAGES, index=STAGES.index(st.session_state.status) if st.session_state.status in STAGES else 0)

c1, c2, c3 = st.columns(3)
st.session_state.start_d = c1.date_input("Start", value=st.session_state.start_d)
st.session_state.end_d = c2.date_input("End", value=st.session_state.end_d)

k_val = st.session_state.km if (st.session_state.km and st.session_state.km > 0) else None
st.session_state.km = c3.number_input("One-Way KM", value=k_val, placeholder="KM...")

diff = (st.session_state.end_d - st.session_state.start_d).days
weeks = math.ceil(diff / 7) if diff > 0 else 1
st.info(f"**Duration:** {diff // 7} Weeks, {diff % 7} Days")

st.markdown("#### 💳 BILLING SETTINGS")
b1, b2 = st.columns(2)
cartage_mode = b1.segmented_control("Cartage", ["Charge", "Free"], default="Charge")
labour_mode = b2.segmented_control("Labour", ["Separate", "Included", "Free"], default="Separate")

st.divider(); col1, col2 = st.columns(2)

with col1:
    st.markdown("### ⚡ STRUCTURES")
    m_in = st.text_input("Size (10x15)")
    m_q = st.number_input("Qty", min_value=1, value=None)
    if st.button("Add Marquee") and m_in and m_q:
        nums = re.findall(r'\d+', m_in)
        if len(nums) >= 2:
            span, length = int(nums[0]), int(nums[1])
            logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
            sqm = span*length; rate = logic['s_rate'] if (length/logic['bay']) <= 1 else logic['m_rate']
            l1 = sqm * rate * m_q * logic['s_lab']
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"Qty": m_q, "Product": f"Structure {span}x{length}m", "Unit Rate": sqm*rate, "Min_Lab": logic['min_lab'], "Raw_Lab": l1, "KG": (sqm*15)*m_q, "Is_Marquee": True, "Discount": 0.0}])], ignore_index=True); st.rerun()

with col2:
    st.markdown("### 🪵 FLOORING / ACCS")
    p_sel = st.selectbox("Product", list(GENERAL_PRODUCTS["Flooring"].keys()) + list(GENERAL_PRODUCTS["Accessories"].keys()))
    f_qty = st.number_input("Amount", min_value=0.0, value=None)
    if st.button("Add Item") and f_qty:
        data = {**GENERAL_PRODUCTS["Flooring"], **GENERAL_PRODUCTS["Accessories"]}[p_sel]
        f_rate = (data['block']/4) if (weeks >= 4 and 'block' in data) else data.get('rate', 70)
        l1 = f_qty * data.get('lab_fix', (f_qty * f_rate * data.get('lab_p', 0)))
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"Qty": f_qty, "Product": p_sel, "Unit Rate": f_rate, "Min_Lab": 0, "Raw_Lab": l1, "KG": f_qty * data.get('kg', 0), "Is_Marquee": False, "Discount": 0.0}])], ignore_index=True); st.rerun()

# --- SUMMARY ---
if not st.session_state.df.empty:
    st.divider(); st.subheader("📝 QUOTE SUMMARY")
    st.markdown("<div style='font-weight: 800; border-bottom: 2px solid #1A1D2D; padding-bottom: 10px;'>DESCRIPTION | QTY | RATE | DISC % | TOTAL</div>", unsafe_allow_html=True)
    
    h_tot_c, h_wk1_gear, total_kg = 0.0, 0.0, 0.0
    
    for idx, row in st.session_state.df.iterrows():
        qty, brate, dm = row["Qty"], row["Unit Rate"], (1 - (row["Discount"]/100))
        total_kg += row["KG"]; h_wk1_gear += (qty * brate)
        
        c0, c1, c2, c3, c4, c5 = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
        if c0.button("🗑️", key=f"del_{idx}"): st.session_state.df.drop(idx, inplace=True); st.rerun()
        
        wk1_t = (qty * brate + row["Raw_Lab"]) * dm if labour_mode == "Included" else (qty * brate) * dm
        h_tot_c += wk1_t
        
        c1.markdown(f"<div class='item-text'>{row['Product']} - Wk 1</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='item-text'>{qty:,.0f}</div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='item-text'>${wk1_t/qty:,.2f}</div>", unsafe_allow_html=True)
        st.session_state.df.at[idx, "Discount"] = c4.number_input("", 0.0, 100.0, float(row["Discount"]), 1.0, key=f"d_{idx}", label_visibility="collapsed")
        c5.markdown(f"<div class='item-text'>${wk1_t:,.2f}</div>", unsafe_allow_html=True)

        if weeks > 1:
            r_rate = brate * 0.5 if row["Is_Marquee"] else brate
            r_tot = qty * r_rate * (weeks-1) * dm; h_tot_c += r_tot
            b0, b1, b2, b3, b4, b5 = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
            b1.markdown(f"<div class='item-sub'>└ Recurring (x{weeks-1} wks)</div>", unsafe_allow_html=True)
            b2.markdown(f"<div class='item-sub'>{qty:,.0f}</div>", unsafe_allow_html=True)
            b3.markdown(f"<div class='item-sub'>${r_rate*dm:,.2f}</div>", unsafe_allow_html=True)
            b5.markdown(f"<div class='item-sub'>${r_tot:,.2f}</div>", unsafe_allow_html=True)

    trks = math.ceil(total_kg / 6000) if total_kg > 0 else 1
    wav = h_wk1_gear * 0.07; crt = trks * (st.session_state.km if st.session_state.km else 0) * 4 * 3.50 if cartage_mode == "Charge" else 0
    lab = max(st.session_state.df["Min_Lab"].max(), st.session_state.df["Raw_Lab"].sum()) if labour_mode == "Separate" else 0
    
    st.divider()
    m = st.columns(6)
    m[0].metric("HIRE", f"${h_tot_c:,.2f}"); m[1].metric("LABOUR", f"${lab:,.2f}"); m[2].metric("WAIVER", f"${wav:,.2f}")
    m[3].metric("CARTAGE", f"${crt:,.2f}"); m[4].metric("WEIGHT", f"{total_kg:,.0f}kg"); m[5].metric("TRUCKS", f"{trks}")
    
    st.markdown(f"<div class='gt-banner'>GRAND TOTAL: ${h_tot_c + lab + wav + crt:,.2f}</div>", unsafe_allow_html=True)
