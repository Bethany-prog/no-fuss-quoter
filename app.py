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

# --- VISUAL STYLING (v36.0 - THE PRECISION GRID) ---
st.markdown("""
    <style>
    /* Main Layout */
    .main { background-color: #F8F9FA !important; }
    h1 { color: #1A1D2D !important; font-weight: 800; }
    
    /* Metrics */
    div.stMetric { 
        background-color: #1A1D2D !important; 
        padding: 20px !important; 
        border-radius: 12px !important; 
        border: 2px solid #3D5AFE !important;
    }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; }

    /* THE GRID SYSTEM */
    .grid-container {
        display: grid;
        grid-template-columns: 50px 3fr 100px 120px 100px 120px;
        align-items: center;
        background-color: white;
        border-bottom: 1px solid #E0E0E0;
        padding: 10px 0;
    }
    .grid-header {
        font-weight: 800;
        text-transform: uppercase;
        font-size: 13px;
        color: #5F6368;
        border-bottom: 2px solid #1A1D2D;
        padding-bottom: 8px;
        margin-bottom: 10px;
    }
    .cell-text {
        font-size: 16px;
        font-weight: 600;
        color: #202124;
    }
    .cell-subtext {
        font-size: 14px;
        color: #70757A;
        padding-left: 20px;
    }
    
    /* Precision Input Styling */
    input.disc-input {
        width: 60px;
        border: 1px solid #DADCE0;
        border-radius: 4px;
        padding: 5px;
        text-align: center;
        font-weight: bold;
    }

    /* Action Buttons */
    .trash-btn {
        background: none;
        border: none;
        color: #D93025;
        cursor: pointer;
        font-size: 18px;
    }
    
    .grand-total-banner {
        background: #1A1D2D;
        color: #00E676;
        padding: 25px;
        border-radius: 10px;
        font-size: 36px;
        font-weight: 900;
        text-align: right;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- MASTER DATA ---
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

def load_project_file(filename):
    with open(f"quotes/{filename}", "r") as f:
        l = json.load(f)
        st.session_state.df = pd.DataFrame(l["items"])
        if "Discount" not in st.session_state.df.columns: st.session_state.df["Discount"] = 0.0
        st.session_state.status, st.session_state.active_project = l.get("status", "Quoted"), l.get("proj", "New")
        st.session_state.start_d = datetime.strptime(l["start_date"], '%Y-%m-%d').date()
        st.session_state.end_d = datetime.strptime(l["end_date"], '%Y-%m-%d').date()
        st.session_state.km = float(l.get("km", 0.0))

# --- MAIN UI ---
st.title("📦 NO FUSS QUOTING ENGINE")

# --- CONTROL TOWER (SIMPLIFIED) ---
quoted_files = [f for f in os.listdir("quotes") if f.endswith(".json")]
for fn in quoted_files:
    try:
        with open(f"quotes/{fn}", "r") as f:
            p = json.load(f)
            if p.get("status") == "Quoted":
                sd = datetime.strptime(p["start_date"], '%Y-%m-%d').date()
                diff = (sd - date.today()).days
                if 0 <= diff <= 28:
                    col_t, col_b = st.columns([5, 1])
                    card = "urgent-row" if diff <= 14 else "warning-row"
                    col_t.warning(f"**{p.get('proj')}** starts in {diff} days ({sd.strftime('%d/%m/%Y')})")
                    if col_b.button("📂 EDIT", key=f"fup_{fn}"):
                        load_project_file(fn); st.rerun()
    except: continue

st.sidebar.title("📁 ARCHIVE")
if st.sidebar.button("➕ START NEW"):
    st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.rerun()
st.session_state.active_project = st.sidebar.text_input("Project Label", st.session_state.active_project)
if st.sidebar.button("💾 SAVE PROJECT"):
    data = {"status": st.session_state.status, "items": st.session_state.df.to_dict(orient='records'), "proj": st.session_state.active_project, "start_date": str(st.session_state.start_d), "end_date": str(st.session_state.end_d), "km": st.session_state.km}
    with open(f"quotes/{st.session_state.active_project}.json", "w") as f: json.dump(data, f)
    st.sidebar.success("Saved!")

# --- WORKSPACE ---
st.markdown(f"### 📍 Active: {st.session_state.active_project}")
st.session_state.status = st.selectbox("Workflow Stage", options=STAGES, index=STAGES.index(st.session_state.status) if st.session_state.status in STAGES else 0)

c1, c2, c3 = st.columns(3)
st.session_state.start_d = c1.date_input("Start Date", value=st.session_state.start_d)
st.session_state.end_d = c2.date_input("End Date", value=st.session_state.end_d)
st.session_state.km = c3.number_input("One-Way KM", value=st.session_state.km if st.session_state.km > 0 else None, placeholder="KM...")

diff = (st.session_state.end_d - st.session_state.start_d).days
weeks = math.ceil(diff / 7) if diff > 0 else 1
st.info(f"**Duration:** {diff // 7} Weeks, {diff % 7} Days")

st.markdown("#### 💳 Billing Logic")
b1, b2 = st.columns(2)
cartage_mode = b1.segmented_control("Cartage", ["Charge", "Free"], default="Charge")
labour_mode = b2.segmented_control("Labour", ["Separate", "Include in Hire", "Free"], default="Separate")

st.divider(); col1, col2 = st.columns(2)

with col1:
    st.markdown("### ⚡ Structures")
    m_in = st.text_input("Size (e.g. 10x15)")
    m_q = st.number_input("Qty", min_value=1, value=None)
    if st.button("Add Marquee") and m_in and m_q:
        nums = re.findall(r'\d+', m_in)
        if len(nums) >= 2:
            span, length = int(nums[0]), int(nums[1])
            logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
            sqm = span*length; rate = logic['s_rate'] if (length/logic['bay']) <= 1 else logic['m_rate']
            l1 = sqm * rate * m_q * logic['s_lab']
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"Qty": m_q, "Product": f"Structure {span}m x {length}m", "Unit Rate": sqm*rate, "Min_Lab": logic['min_lab'], "Raw_Lab": l1, "KG": (sqm*15)*m_q, "Is_Marquee": True, "Discount": 0.0}])], ignore_index=True); st.rerun()

with col2:
    st.markdown("### 🪵 Flooring & Accessories")
    p_sel = st.selectbox("Product", list(GENERAL_PRODUCTS["Flooring"].keys()) + list(GENERAL_PRODUCTS["Accessories"].keys()))
    f_qty = st.number_input("Amount", min_value=0.0, value=None)
    if st.button("Add Item") and f_qty:
        data = {**GENERAL_PRODUCTS["Flooring"], **GENERAL_PRODUCTS["Accessories"]}[p_sel]
        f_rate = (data['block']/4) if (weeks >= 4 and 'block' in data) else data.get('rate', 70)
        l1 = f_qty * data.get('lab_fix', (f_qty * f_rate * data.get('lab_p', 0)))
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"Qty": f_qty, "Product": p_sel, "Unit Rate": f_rate, "Min_Lab": 0, "Raw_Lab": l1, "KG": f_qty * data.get('kg_sqm', data.get('kg', 0)), "Is_Marquee": False, "Discount": 0.0}])], ignore_index=True); st.rerun()

# --- THE PRECISION SUMMARY GRID ---
if not st.session_state.df.empty:
    st.divider(); st.subheader("📝 QUOTE SUMMARY")
    
    # Headers
    st.markdown("""
        <div class="grid-container grid-header">
            <div></div><div>ITEM DESCRIPTION</div><div>QTY</div><div>RATE</div><div>DISC %</div><div>TOTAL</div>
        </div>
    """, unsafe_allow_html=True)
    
    h_tot_c, h_wk1_gear, total_kg, raw_l = 0.0, 0.0, 0.0, 0.0
    
    for idx, row in st.session_state.df.iterrows():
        qty, brate, dm = row["Qty"], row["Unit Rate"], (1 - (row["Discount"]/100))
        total_kg += row["KG"]; h_wk1_gear += (qty * brate)
        
        # UI Alignment Grid
        col0, col1, col2, col3, col4, col5 = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
        
        if col0.button("🗑️", key=f"del_{idx}"):
            st.session_state.df.drop(idx, inplace=True); st.rerun()
            
        # Wk 1 Line
        wk1_t = (qty * brate + row["Raw_Lab"]) * dm if labour_mode == "Include in Hire" else (qty * brate) * dm
        h_tot_c += wk1_t
        
        col1.markdown(f"<div class='summary-text'>{row['Product']} - Wk 1</div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='summary-text'>{qty:,.0f}</div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='summary-text'>${wk1_t/qty:,.2f}</div>", unsafe_allow_html=True)
        st.session_state.df.at[idx, "Discount"] = col4.number_input("", 0.0, 100.0, float(row["Discount"]), 1.0, key=f"d_{idx}", label_visibility="collapsed")
        col5.markdown(f"<div class='summary-text'>${wk1_t:,.2f}</div>", unsafe_allow_html=True)

        if weeks > 1:
            r_rate = brate * 0.5 if row["Is_Marquee"] and "Weight" not in row["Product"] else brate
            r_tot = qty * r_rate * (weeks-1) * dm; h_tot_c += r_tot
            
            b0, b1, b2, b3, b4, b5 = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
            b1.markdown(f"<div class='cell-subtext'>└ Recurring Hire (x{weeks-1} wks)</div>", unsafe_allow_html=True)
            b2.markdown(f"<div class='cell-subtext'>{qty:,.0f}</div>", unsafe_allow_html=True)
            b3.markdown(f"<div class='cell-subtext'>${r_rate*dm:,.2f}</div>", unsafe_allow_html=True)
            b5.markdown(f"<div class='cell-subtext'>${r_tot:,.2f}</div>", unsafe_allow_html=True)

    # FINAL TOTALS
    trks = math.ceil(total_kg / 6000) if total_kg > 0 else 1
    wav = h_wk1_gear * 0.07; crt = trks * st.session_state.km * 4 * 3.50 if cartage_mode == "Charge" else 0
    lab = max(st.session_state.df["Min_Lab"].max(), st.session_state.df["Raw_Lab"].sum()) if labour_mode == "Separate" else 0
    
    st.divider()
    m = st.columns(6)
    m[0].metric("HIRE", f"${h_tot_c:,.2f}"); m[1].metric("LABOUR", f"${lab:,.2f}"); m[2].metric("WAIVER", f"${wav:,.2f}")
    m[3].metric("CARTAGE", f"${crt:,.2f}"); m[4].metric("WEIGHT", f"{total_kg:,.0f}kg"); m[5].metric("TRUCKS", f"{trks}")
    
    st.markdown(f"<div class='grand-total-banner'>GRAND TOTAL: ${h_tot_c + lab + wav + crt:,.2f}</div>", unsafe_allow_html=True)
