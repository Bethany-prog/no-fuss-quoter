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

# --- VISUAL STYLING ---
st.set_page_config(page_title="Louis Quoting Tool", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #FFFFFF !important; }
    h3 { color: #FFFFFF !important; border-left: 5px solid #00E676; padding: 10px 15px; background-color: #1A1D2D; border-radius: 0 10px 10px 0; margin-top: 20px; }
    div.stMetric { background-color: #1A1D2D !important; padding: 20px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 28px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 14px !important; }
    div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; width: 100%; }
    .guardrail-box { background-color: #F8F9FA; padding: 20px; border-radius: 10px; border: 1px solid #D1D3D4; margin-top: 20px; }
    
    /* Control Tower Styling */
    .dashboard-card { background-color: #F1F3F4; padding: 20px; border-radius: 12px; border-top: 5px solid #3D5AFE; margin-bottom: 25px; }
    .urgent-text { color: #D32F2F; font-weight: bold; }
    .warning-text { color: #F57C00; font-weight: bold; }
    
    .summary-text { font-size: 18px !important; font-weight: 600 !important; color: #2c3e50; display: flex; align-items: center; height: 100%; }
    [data-testid="column"] { display: flex; flex-direction: column; justify-content: center; }
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
        "I-Trac®": {"rate": 23.40, "block": 46.80, "lab_fix": 4.65, "kg_sqm": 15.0, "w": 0, "l": 0},
        "Supa-Trac®": {"rate": 11.55, "block": 25.00, "lab_fix": 4.65, "kg_sqm": 4.5, "w": 1.14, "l": 2.75},
        "Plastorip": {"rate": 10.15, "block": 20.30, "lab_fix": 3.05, "kg_sqm": 4.0, "w": 0, "l": 0},
        "Rollout Flooring": {"rate": 7.10, "block": 15.00, "lab_fix": 3.05, "kg_sqm": 3.5, "w": 0, "l": 0}
    },
    "Accessories": {
        "30kg Weights": {"rate": 6.60, "lab_fix": 1.65, "kg": 30.0, "unit": "ea"},
        "I-Trac® Ramps": {"rate": 42.00, "lab_fix": 0, "kg": 10.0, "unit": "ea"},
        "Supa-Trac® Edging": {"rate": 6.70, "lab_fix": 0, "kg": 1.0, "unit": "m"},
        "Plastorip Edging": {"rate": 1.65, "lab_fix": 0, "kg": 0.5, "unit": "ea"},
        "MOJO Barriers": {"rate": 70.00, "lab_p": 0.40, "kg": 60.0, "unit": "ea"},
        "Rollout Flooring - Ramps": {"rate": 6.60, "lab_fix": 0, "kg": 2.0, "unit": "ea"},
        "Rollout Flooring - joiners": {"rate": 6.60, "lab_fix": 0, "kg": 0.1, "unit": "ea"}
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
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Is_Marquee", "Hire_Math_Str", "Discount"])
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
                    followup_list.append({"Project": p_data.get("proj", "Unknown"), "Start Date": sd.strftime('%d/%m/%Y'), "Days Left": diff, "Priority": "🚨 URGENT" if diff <= 14 else "⚠️ WARNING"})
    except: continue

# --- SIDEBAR (ARCHIVE ONLY) ---
st.sidebar.title("📁 Archive Manager")
if st.sidebar.button("➕ START NEW PROJECT"):
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Is_Marquee", "Hire_Math_Str", "Discount"])
    st.session_state.status = "Quoted"; st.session_state.active_project = "New Project"; st.session_state.km = 0.0; st.rerun()

st.sidebar.divider()
st.session_state.active_project = st.sidebar.text_input("Project Label", st.session_state.active_project)
if st.sidebar.button("💾 SAVE / UPDATE PROJECT"):
    data = {"status": st.session_state.status, "items": st.session_state.df.to_dict(orient='records'), "proj": st.session_state.active_project, "start_date": str(st.session_state.start_d), "end_date": str(st.session_state.end_d), "km": st.session_state.km}
    with open(f"quotes/{st.session_state.active_project}.json", "w") as f: json.dump(data, f)
    st.sidebar.success(f"Archived: {st.session_state.active_project}")

st.sidebar.divider()
saved_quotes = sorted([f.replace(".json", "") for f in os.listdir("quotes") if f.endswith(".json")])
load_choice = st.sidebar.selectbox("Load Project", ["-- Choose --"] + saved_quotes)
cl, cd = st.sidebar.columns(2)
if cl.button("📂 LOAD") and load_choice != "-- Choose --":
    with open(f"quotes/{load_choice}.json", "r") as f:
        loaded = json.load(f); st.session_state.df = pd.DataFrame(loaded["items"])
        if "Discount" not in st.session_state.df.columns: st.session_state.df["Discount"] = 0.0
        st.session_state.status = loaded.get("status", "Quoted"); st.session_state.active_project = loaded.get("proj", load_choice)
        if "start_date" in loaded: st.session_state.start_d = datetime.strptime(loaded["start_date"], '%Y-%m-%d').date()
        if "end_date" in loaded: st.session_state.end_d = datetime.strptime(loaded["end_date"], '%Y-%m-%d').date()
        if "km" in loaded: st.session_state.km = float(loaded["km"])
        st.rerun()
if cd.button("🗑️ DELETE") and load_choice != "-- Choose --":
    os.remove(f"quotes/{load_choice}.json"); st.rerun()

# --- MAIN UI ---
st.title("📦 Louis Quoting Tool")

# --- CONTROL TOWER DASHBOARD ---
if followup_list:
    with st.container():
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.markdown("### 📡 Follow-up Control Tower")
        st.markdown("The following jobs are still in **Quoted** stage and starting soon:")
        df_follow = pd.DataFrame(followup_list)
        st.table(df_follow)
        
        # Hit List Export
        csv = df_follow.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DOWNLOAD FOLLOW-UP HIT LIST (CSV)", csv, "FollowUp_HitList.csv", "text/csv")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown(f"### 📍 Active Project: {st.session_state.active_project}")

try: status_index = STAGES.index(st.session_state.status)
except ValueError: status_index = 0
st.session_state.status = st.selectbox("Workflow Stage", options=STAGES, index=status_index)
st.markdown(f"<div style='height: 12px; background-color: {STAGE_COLORS[st.session_state.status]}; border-radius: 6px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
st.session_state.start_d = c1.date_input("Hire Start", value=st.session_state.start_d, format="DD/MM/YYYY")
st.session_state.end_d = c2.date_input("Hire End", value=st.session_state.end_d, format="DD/MM/YYYY")
st.session_state.km = c3.number_input("One-Way Distance (KM)", min_value=0.0, value=st.session_state.km if st.session_state.km > 0 else None, placeholder="Enter KM...")

total_days = (st.session_state.end_d - st.session_state.start_d).days
weeks = math.ceil(total_days / 7) if total_days > 0 else 1
if total_days >= 0:
    st.markdown(f"**⏱️ Total Duration:** {total_days // 7} Week(s), {total_days % 7} Day(s)")

st.markdown("#### 💳 Billing Options")
b_col1, b_col2 = st.columns(2)
cartage_mode = b_col1.segmented_control("Cartage Billing", ["Charge", "Free"], default="Charge")
labour_mode = b_col2.segmented_control("Labour Billing", ["Separate Line Item", "Include in Hire cost", "Free"], default="Separate Line Item")

st.divider(); col_mq, col_cat = st.columns(2)

with col_mq:
    st.markdown("### ⚡ Marquee & Structure")
    m_in = st.text_input("Size (e.g. 10x15)", placeholder="e.g. 10x15")
    m_q = st.number_input("Quantity", min_value=1, value=None, placeholder="Qty...", key="mq")
    m_sec = st.radio("Securing", ["Weights", "Pegging"], horizontal=True)
    if st.button("Add Marquee") and m_in and m_q:
        nums = re.findall(r'\d+', m_in)
        if len(nums) >= 2:
            span, length = int(nums[0]), int(nums[1])
            logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
            sqm = span*length; rate = logic['s_rate'] if (length/logic['bay']) <= 1 else logic['m_rate']
            lab_p = logic['s_lab'] if (length/logic['bay']) <= 1 else logic['m_lab']
            h1 = sqm * rate * m_q; l1 = h1 * lab_p 
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
                "Qty": m_q, "Product": f"Structure {span}m x {length}m", "Unit Rate": sqm*rate, "Total": 0.0, 
                "Min_Lab": logic['min_lab'], "Raw_Lab": l1, "Lab_Math": f"{span}x{length} (Wk1): ${h1:,.2f} x {int(lab_p*100)}% = ${l1:,.2f}", 
                "KG": (sqm*15)*m_q, "Is_Marquee": True, "Hire_Math_Str": "", "Discount": 0.0
            }])], ignore_index=True)
            if m_sec == "Weights":
                legs = ((length/logic['bay'])+1)*2; w_tot = int(legs*6*m_q); w_l = w_tot * 1.65
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
                    "Qty": w_tot, "Product": "30kg Weights", "Unit Rate": 6.60, "Total": 0.0, "Min_Lab": 0, "Raw_Lab": w_l, "Lab_Math": f"Weights: {w_tot} x $1.65 = ${w_l:,.2f}", "KG": w_tot*30, "Is_Marquee": True, "Discount": 0.0
                }])], ignore_index=True)
            st.rerun()

with col_cat:
    st.markdown("### 🪵 Flooring & Catalog")
    cat_type = st.radio("Category", ["Flooring", "Accessories"], horizontal=True)
    p_sel = st.selectbox("Product", list(GENERAL_PRODUCTS[cat_type].keys()))
    f_qty = st.number_input("Quantity / SQM", min_value=0.0, value=None, placeholder="Enter amount...")
    if st.button("Add to Quote") and f_qty:
        data = GENERAL_PRODUCTS[cat_type][p_sel]
        f_rate = (data['block']/4) if (weeks >= 4 and 'block' in data) else data['rate']
        h1 = f_qty * f_rate; l1 = f_qty * data.get('lab_fix', (h1 * data.get('lab_p', 0)))
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{ 
            "Qty": f_qty, "Product": p_sel, "Unit Rate": f_rate, "Total": 0.0, "Min_Lab": 0, "Raw_Lab": l1, 
            "Lab_Math": f"{p_sel}: {f_qty:,.2f} x ${data.get('lab_fix', 0)} = ${l1:,.2f}" if 'lab_fix' in data else f"{p_sel}: ${h1:,.2f} x {int(data.get('lab_p',0)*100)}% = ${l1:,.2f}", 
            "KG": f_qty * data.get('kg_sqm', data.get('kg', 0)), "Is_Marquee": False, "Hire_Math_Str": "", "Discount": 0.0 
        }])], ignore_index=True); st.rerun()

if not st.session_state.df.empty:
    st.divider(); st.subheader("Quote Summary")
    hc1, hc2, hc3, hc4, hc5, hc6 = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
    hc2.write("**Item Description**"); hc3.write("**Qty**"); hc4.write("**Rate**"); hc5.write("**Disc %**"); hc6.write("**Total**")
    
    h_tot_c = 0.0; h_tot_wk1_gear = 0.0; raw_l = 0.0; max_min_l = 0.0; total_kg = 0.0; ph_maths = []; pl_maths = []

    for idx, row in st.session_state.df.iterrows():
        qty = row["Qty"]; brate = row["Unit Rate"]; gear_wk1 = qty * brate
        raw_l += row["Raw_Lab"]; max_min_l = max(max_min_l, row["Min_Lab"]); total_kg += row["KG"]
        c1, c2, c3, c4, c5, c6 = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
        if c1.button("🗑️", key=f"del_{idx}"): st.session_state.df = st.session_state.df.drop(idx); st.rerun()
        disc = c5.number_input("", 0.0, 100.0, float(row.get("Discount", 0)), 1.0, f"disc_{idx}", label_visibility="collapsed")
        st.session_state.df.at[idx, "Discount"] = disc
        dm = (1 - (disc / 100)); h_tot_wk1_gear += gear_wk1

        wk1_t = (gear_wk1 + row["Raw_Lab"]) * dm if labour_mode == "Include in Hire cost" else gear_wk1 * dm
        h_tot_c += wk1_t; ph_maths.append(f"{row['Product']} Wk 1: ${wk1_t:,.2f}" + (f" (Incl {disc}% Disc)" if disc > 0 else ""))
        if row["Lab_Math"]: pl_maths.append(row["Lab_Math"])
        c2.markdown(f"<div class='summary-text'>{row['Product']} - Week 1</div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='summary-text'>{qty:,.2f}</div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='summary-text'>${wk1_t/qty:,.2f}</div>", unsafe_allow_html=True)
        c6.markdown(f"<div class='summary-text'>${wk1_t:,.2f}</div>", unsafe_allow_html=True)

        if weeks > 1:
            ex = weeks - 1
            rec_r = brate * 0.5 if row["Is_Marquee"] and "Weight" not in row["Product"] else brate
            rec_t = qty * rec_r * ex * dm; h_tot_c += rec_t; ph_maths.append(f"{row['Product']} Recurring: ${rec_t:,.2f}")
            c1b, c2b, c3b, c4b, c5b, c6b = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
            c2b.markdown(f"<div class='summary-text' style='color:#7f8c8d; font-size:16px !important;'>└ Recurring Hire</div>", unsafe_allow_html=True)
            c3b.markdown(f"<div class='summary-text' style='color:#7f8c8d; font-size:16px !important;'>{qty:,.2f}</div>", unsafe_allow_html=True)
            c4b.markdown(f"<div class='summary-text' style='color:#7f8c8d; font-size:16px !important;'>${rec_r * dm:,.2f}</div>", unsafe_allow_html=True)
            c6b.markdown(f"<div class='summary-text' style='color:#7f8c8d; font-size:16px !important;'>${rec_t:,.2f}</div>", unsafe_allow_html=True)

    trucks = math.ceil(total_kg / 6000) if total_kg > 0 else 1
    flab = max(max_min_l, raw_l); waiver = h_tot_wk1_gear * 0.07; dist = st.session_state.km
    cartage = trucks * dist * 4 * 3.50 if cartage_mode == "Charge" else 0
    d_lab = flab if labour_mode == "Separate Line Item" else 0
    l_maths = [f"Damage Waiver: ${h_tot_wk1_gear:,.2f} x 7% = ${waiver:,.2f}", f"Cartage: {trucks} Trucks x {dist}km x 4 trips x $3.50 = ${cartage:,.2f}"]

    st.markdown("---")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("HIRE", f"${h_tot_c:,.2f}"); m2.metric("LABOUR", f"${d_lab:,.2f}"); m3.metric("WAIVER", f"${waiver:,.2f}"); m4.metric("CARTAGE", f"${cartage:,.2f}"); m5.metric("LOAD", f"{total_kg:,.0f}kg"); m6.metric("TRUCKS", f"{trucks}")
    
    st.markdown("### 🛠️ Checklist")
    st.markdown("<div class='guardrail-box'>", unsafe_allow_html=True)
    if st.session_state.status == "Quoted":
        st.checkbox("Email / enquiry printed"); st.checkbox("Quote printed and paperclipped to the front")
    else: st.write("No specific office actions required.")
    st.markdown("</div>", unsafe_allow_html=True)

    pdf_b = create_calculation_pdf(st.session_state.active_project, h_tot_c, d_lab, waiver, cartage, h_tot_c+d_lab+waiver+cartage, weeks, st.session_state.start_d, st.session_state.end_d, ph_maths, pl_maths, l_maths, st.session_state.status)
    st.download_button(f"📥 DOWNLOAD {st.session_state.status.upper()} PDF", pdf_b, file_name=f"{st.session_state.active_project}_Analysis.pdf")
