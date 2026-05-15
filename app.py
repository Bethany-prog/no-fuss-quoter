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

# --- VISUAL STYLING (v35.3 - HIGH VISIBILITY INTERACTIVE) ---
st.markdown("""
    <style>
    /* Professional Headers */
    h1 { color: #3D5AFE !important; font-size: 45px !important; font-weight: 800 !important; }
    h3 { color: #FFFFFF !important; border-left: 8px solid #00E676; padding: 10px 20px; background-color: #1A1D2D; border-radius: 0 10px 10px 0; }
    
    /* Metrics Branding */
    div.stMetric { 
        background-color: #1A1D2D !important; 
        padding: 25px !important; 
        border-radius: 15px !important; 
        border: 2px solid #3D5AFE !important;
    }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 38px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-size: 16px !important; font-weight: bold !important; }
    
    /* Control Tower Interactive Cards */
    .urgent-row { background-color: #FFEBEE; border-left: 10px solid #D32F2F; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; }
    .warning-row { background-color: #FFF3E0; border-left: 10px solid #F57C00; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; }
    .card-text { color: #1A1D2D; font-size: 18px; font-weight: 700; }
    .card-subtext { color: #455A64; font-size: 14px; font-weight: 500; }
    
    /* Summary Text Size */
    .summary-text { font-size: 18px !important; font-weight: 600 !important; color: #2c3e50; display: flex; align-items: center; height: 100%; }
    .rec-text { color: #7f8c8d; font-size: 16px !important; }
    
    /* Grand Total Big Finish */
    .grand-total-box { 
        background-color: #1A1D2D; color: #00E676; padding: 30px; border-radius: 15px; 
        text-align: right; font-size: 40px !important; font-weight: 900; margin-top: 20px;
        border: 4px solid #00E676;
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

# --- PDF ENGINE ---
def create_calculation_pdf(name, subtotal, labour, waiver, cartage, grand, weeks, start, end, h_maths, l_details, log_maths, status):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16); pdf.cell(0, 10, f"Louis Quoting Tool - Calculation Analysis", ln=True, align="C")
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 7, f"PROJECT: {name} | STATUS: {status.upper()}", ln=True, align="C")
    pdf.cell(0, 7, f"HIRE PERIOD: {start.strftime('%d/%m/%Y')} to {end.strftime('%d/%m/%Y')} ({weeks} Week(s))", ln=True, align="C"); pdf.ln(5)
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " CALCULATIONS (Hire)", 0, 1, "L", True); pdf.set_font("Arial", "", 10)
    for h in h_maths: pdf.cell(0, 7, f" {h}", border="B", ln=True)
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 10, f" TOTAL HIRE CONTRACT: ${subtotal:,.2f}", ln=True, align="R"); pdf.ln(5)
    if labour > 0:
        pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, " LABOUR (Week 1 Only)", 0, 1, "L", True); pdf.set_font("Arial", "", 10)
        for l in l_details: pdf.cell(0, 7, f" {l}", border="B", ln=True)
        pdf.set_font("Arial", "B", 10); pdf.cell(0, 10, f" TOTAL LABOUR POOL: ${labour:,.2f}", ln=True, align="R"); pdf.ln(5)
    pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, " LOGISTICS & WAIVER", 0, 1, "L", True); pdf.set_font("Arial", "", 10)
    for m in log_maths: pdf.cell(0, 7, f" {m}", border="B", ln=True)
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 10, f" LOGISTICS SUBTOTAL: ${waiver + cartage:,.2f}", ln=True, align="R")
    pdf.ln(10); pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 15, f" GRAND TOTAL (EX GST): ${grand:,.2f} ", 0, 1, "R", True)
    return bytes(pdf.output())

# --- SESSION STATE ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Is_Marquee", "Discount"])
if 'status' not in st.session_state: st.session_state.status = "Quoted"
if 'active_project' not in st.session_state: st.session_state.active_project = "New Project"
if 'start_d' not in st.session_state: st.session_state.start_d = date.today()
if 'end_d' not in st.session_state: st.session_state.end_d = date.today()
if 'km' not in st.session_state: st.session_state.km = 0.0

# --- CORE LOAD LOGIC ---
def load_project_file(filename):
    with open(f"quotes/{filename}", "r") as f:
        loaded = json.load(f)
        st.session_state.df = pd.DataFrame(loaded["items"])
        if "Discount" not in st.session_state.df.columns: st.session_state.df["Discount"] = 0.0
        st.session_state.status = loaded.get("status", "Quoted")
        st.session_state.active_project = loaded.get("proj", filename.replace(".json", ""))
        if "start_date" in loaded: st.session_state.start_d = datetime.strptime(loaded["start_date"], '%Y-%m-%d').date()
        if "end_date" in loaded: st.session_state.end_d = datetime.strptime(loaded["end_date"], '%Y-%m-%d').date()
        st.session_state.km = float(loaded.get("km", 0.0))

# --- SCAN ARCHIVE FOR DASHBOARD ---
quoted_files = [f for f in os.listdir("quotes") if f.endswith(".json")]
followup_list = []
for f_name in quoted_files:
    try:
        with open(f"quotes/{f_name}", "r") as f:
            p = json.load(f)
            if p.get("status") == "Quoted" and "start_date" in p:
                sd = datetime.strptime(p["start_date"], '%Y-%m-%d').date()
                diff = (sd - date.today()).days
                if 0 <= diff <= 28:
                    followup_list.append({"Proj": p.get("proj", "Unknown"), "Date": sd.strftime('%d/%m/%Y'), "Days": diff, "File": f_name})
    except: continue

# --- SIDEBAR ---
st.sidebar.title("📁 Archive Manager")
if st.sidebar.button("➕ START NEW"):
    st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.session_state.status = "Quoted"; st.session_state.km = 0.0; st.rerun()

st.sidebar.divider()
st.session_state.active_project = st.sidebar.text_input("Project Label", st.session_state.active_project)
if st.sidebar.button("💾 SAVE PROJECT"):
    data = {"status": st.session_state.status, "items": st.session_state.df.to_dict(orient='records'), "proj": st.session_state.active_project, "start_date": str(st.session_state.start_d), "end_date": str(st.session_state.end_d), "km": st.session_state.km}
    with open(f"quotes/{st.session_state.active_project}.json", "w") as f: json.dump(data, f)
    st.sidebar.success("Saved!")

saved_quotes = sorted([f.replace(".json", "") for f in os.listdir("quotes") if f.endswith(".json")])
load_choice = st.sidebar.selectbox("Retrieval", ["-- Choose --"] + saved_quotes)
cl, cd = st.sidebar.columns(2)
if cl.button("📂 LOAD") and load_choice != "-- Choose --":
    load_project_file(f"{load_choice}.json"); st.rerun()
if cd.button("🗑️ DELETE") and load_choice != "-- Choose --":
    os.remove(f"quotes/{load_choice}.json"); st.rerun()

# --- MAIN UI ---
st.title("⚡ Louis Quoting Tool")

# --- INTERACTIVE CONTROL TOWER ---
if followup_list:
    st.markdown("### 📡 Follow-up Control Tower")
    for item in followup_list:
        card_class = "urgent-row" if item['Days'] <= 14 else "warning-row"
        col_text, col_btn = st.columns([4, 1])
        with col_text:
            st.markdown(f"""
                <div class='{card_class}'>
                    <div>
                        <span class='card-text'>{item['Proj']}</span><br>
                        <span class='card-subtext'>Starts in {item['Days']} days ({item['Date']})</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        with col_btn:
            if st.button("📂 EDIT", key=f"fup_{item['File']}"):
                load_project_file(item['File']); st.rerun()
    st.divider()

st.markdown(f"### 📍 Active: {st.session_state.active_project}")
try: s_idx = STAGES.index(st.session_state.status)
except: s_idx = 0
st.session_state.status = st.selectbox("Stage", options=STAGES, index=s_idx)
st.markdown(f"<div style='height: 12px; background-color: {STAGE_COLORS[st.session_state.status]}; border-radius: 6px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
st.session_state.start_d = c1.date_input("Start", value=st.session_state.start_d)
st.session_state.end_d = c2.date_input("End", value=st.session_state.end_d)
k_val = st.session_state.km if (st.session_state.km and st.session_state.km > 0) else None
st.session_state.km = c3.number_input("One-Way KM", min_value=0.0, value=k_val, placeholder="Enter KM...")

diff = (st.session_state.end_d - st.session_state.start_d).days
weeks = math.ceil(diff / 7) if diff > 0 else 1
st.markdown(f"**⏱️ Duration:** {diff // 7} Weeks, {diff % 7} Days")

st.markdown("#### 💳 Billing Setup")
b1, b2 = st.columns(2)
cartage_mode = b1.segmented_control("Cartage", ["Charge", "Free"], default="Charge")
labour_mode = b2.segmented_control("Labour", ["Separate", "Include in Hire", "Free"], default="Separate")

st.divider(); col1, col2 = st.columns(2)

with col1:
    st.markdown("### ⚡ Structures")
    m_in = st.text_input("Size (10x15)")
    m_q = st.number_input("Qty", min_value=1, value=None)
    m_sec = st.radio("Securing", ["Weights", "Pegging"], horizontal=True)
    if st.button("Add Structure") and m_in and m_q:
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

with col2:
    st.markdown("### 🪵 Flooring/Catalog")
    p_sel = st.selectbox("Select Product", list(GENERAL_PRODUCTS["Flooring"].keys()) + list(GENERAL_PRODUCTS["Accessories"].keys()))
    f_qty = st.number_input("Amount/SQM", min_value=0.0, value=None)
    if st.button("Add Product") and f_qty:
        data = {**GENERAL_PRODUCTS["Flooring"], **GENERAL_PRODUCTS["Accessories"]}[p_sel]
        f_rate = (data['block']/4) if (weeks >= 4 and 'block' in data) else data.get('rate', 70)
        h1 = f_qty * f_rate; l1 = f_qty * data.get('lab_fix', (h1 * data.get('lab_p', 0)))
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
            "Qty": f_qty, "Product": p_sel, "Unit Rate": f_rate, "Total": 0.0, "Min_Lab": 0, "Raw_Lab": l1, "Lab_Math": f"Lab: ${l1:,.2f}", "KG": f_qty * data.get('kg_sqm', data.get('kg', 0)), "Is_Marquee": False, "Discount": 0.0
        }])], ignore_index=True); st.rerun()

# --- SUMMARY ---
if not st.session_state.df.empty:
    st.divider(); st.subheader("📋 Quote Summary")
    hc = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
    cols = ["", "ITEM", "QTY", "RATE", "DISC%", "TOTAL"]
    for i, col in enumerate(hc): col.write(f"**{cols[i]}**")
    
    h_tot_contract = 0.0; h_wk1_gear = 0.0; total_kg = 0.0
    
    for idx, row in st.session_state.df.iterrows():
        qty, brate, dm = row["Qty"], row["Unit Rate"], (1 - (row["Discount"]/100))
        total_kg += row["KG"]; h_wk1_gear += (qty * brate)
        c = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
        if c[0].button("🗑️", key=f"del_{idx}"): st.session_state.df.drop(idx, inplace=True); st.rerun()
        
        # Wk 1
        wk1_t = (qty * brate + row["Raw_Lab"]) * dm if labour_mode == "Include in Hire" else (qty * brate) * dm
        h_tot_contract += wk1_t
        c[1].markdown(f"<div class='summary-text'>{row['Product']} - Wk 1</div>", unsafe_allow_html=True)
        c[2].write(f"{qty:,.0f}")
        c[3].write(f"${wk1_t/qty:,.2f}")
        row["Discount"] = c[4].number_input("", 0.0, 100.0, float(row["Discount"]), 1.0, key=f"d_{idx}", label_visibility="collapsed")
        c[5].write(f"${wk1_t:,.2f}")

        if weeks > 1:
            r_rate = brate * 0.5 if row["Is_Marquee"] and "Weight" not in row["Product"] else brate
            r_tot = qty * r_rate * (weeks-1) * dm; h_tot_contract += r_tot
            cb = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
            cb[1].markdown(f"<div class='summary-text rec-text'>└ Recurring Hire</div>", unsafe_allow_html=True)
            cb[2].markdown(f"<div class='rec-text'>{qty:,.0f}</div>", unsafe_allow_html=True)
            cb[3].markdown(f"<div class='rec-text'>${r_rate*dm:,.2f}</div>", unsafe_allow_html=True)
            cb[5].markdown(f"<div class='rec-text'>${r_tot:,.2f}</div>", unsafe_allow_html=True)

    # METRICS
    st.divider()
    trks = math.ceil(total_kg / 6000) if total_kg > 0 else 1
    wav = h_wk1_gear * 0.07; crt = trks * st.session_state.km * 4 * 3.50 if cartage_mode == "Charge" else 0
    lab = max(st.session_state.df["Min_Lab"].max(), st.session_state.df["Raw_Lab"].sum()) if labour_mode == "Separate" else 0
    
    m = st.columns(6)
    m[0].metric("HIRE", f"${h_tot_contract:,.2f}"); m[1].metric("LABOUR", f"${lab:,.2f}"); m[2].metric("WAIVER", f"${wav:,.2f}")
    m[3].metric("CARTAGE", f"${crt:,.2f}"); m[4].metric("WEIGHT", f"{total_kg:,.0f}kg"); m[5].metric("TRUCKS", f"{trks}")
    
    gt = h_tot_contract + lab + wav + crt
    st.markdown(f"<div class='grand_total_box'>GRAND TOTAL: ${gt:,.2f}</div>", unsafe_allow_html=True)
