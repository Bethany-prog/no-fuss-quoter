import streamlit as st
import math
import pandas as pd
from datetime import date
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
def create_calculation_pdf(name, df, subtotal, labour, waiver, cartage, grand, km, weeks, start, end, h_maths, l_details, kg, trucks, log_maths, status):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16); pdf.cell(0, 10, f"Louis Quoting Tool - Calculation Analysis", ln=True, align="C")
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 7, f"PROJECT: {name} | STATUS: {status.upper()}", ln=True, align="C")
    pdf.cell(0, 7, f"HIRE PERIOD: {start.strftime('%d/%m/%Y')} to {end.strftime('%d/%m/%Y')} ({weeks} Week(s))", ln=True, align="C"); pdf.ln(5)
    
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " CALCULATIONS (Hire)", 0, 1, "L", True); pdf.set_font("Arial", "", 10)
    for h in h_maths: pdf.cell(0, 7, f" {h}", border="B", ln=True)
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 10, f" TOTAL HIRE CONTRACT: ${subtotal:,.2f}", ln=True, align="R"); pdf.ln(5)
    
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
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Is_Marquee", "Hire_Math_Str"])
if 'status' not in st.session_state:
    st.session_state.status = "Quoted"
if 'active_project' not in st.session_state:
    st.session_state.active_project = "New Project"

# --- SIDEBAR (ARCHIVE MANAGER) ---
st.sidebar.title("📁 Archive Manager")
if st.sidebar.button("➕ START NEW PROJECT"):
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Is_Marquee", "Hire_Math_Str"])
    st.session_state.status = "Quoted"
    st.session_state.active_project = "New Project"
    st.rerun()

st.sidebar.divider()
st.session_state.active_project = st.sidebar.text_input("Project Label", st.session_state.active_project)
if st.sidebar.button("💾 SAVE / UPDATE PROJECT"):
    data = {"status": st.session_state.status, "items": st.session_state.df.to_dict(orient='records'), "proj": st.session_state.active_project}
    with open(f"quotes/{st.session_state.active_project}.json", "w") as f: json.dump(data, f)
    st.sidebar.success(f"Archived: {st.session_state.active_project}")

st.sidebar.divider()
saved_quotes = sorted([f.replace(".json", "") for f in os.listdir("quotes") if f.endswith(".json")])
load_choice = st.sidebar.selectbox("Select Existing Project", ["-- Choose --"] + saved_quotes)

cl, cd = st.sidebar.columns(2)
if cl.button("📂 LOAD") and load_choice != "-- Choose --":
    with open(f"quotes/{load_choice}.json", "r") as f:
        loaded = json.load(f); st.session_state.df = pd.DataFrame(loaded["items"])
        ls = loaded.get("status", "Quoted"); st.session_state.status = ls if ls in STAGES else "Quoted"
        st.session_state.active_project = loaded.get("proj", load_choice); st.rerun()

if cd.button("🗑️ DELETE") and load_choice != "-- Choose --":
    os.remove(f"quotes/{load_choice}.json"); st.rerun()

# --- MAIN UI ---
st.title("📦 Louis Quoting Tool")
st.markdown(f"### 📍 Project: {st.session_state.active_project}")

try: status_index = STAGES.index(st.session_state.status)
except ValueError: status_index = 0

st.session_state.status = st.selectbox("Current Workflow Stage", options=STAGES, index=status_index)
st.markdown(f"<div style='height: 12px; background-color: {STAGE_COLORS[st.session_state.status]}; border-radius: 6px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# TOP INPUTS
c1, c2, c3 = st.columns(3)
start_d = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
end_d = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
km_in = c3.number_input("One-Way Distance (KM)", min_value=0.0, value=None, placeholder="Enter KM...")
weeks = math.ceil(((end_d - start_d).days) / 7) if (end_d - start_d).days > 0 else 1

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
    if st.button("Add Marquee"):
        if m_in and m_q:
            nums = re.findall(r'\d+', m_in)
            if len(nums) >= 2:
                span, length = int(nums[0]), int(nums[1])
                new_rows = []
                logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
                sqm = span*length; rate = logic['s_rate'] if (length/logic['bay']) <= 1 else logic['m_rate']
                lab_p = logic['s_lab'] if (length/logic['bay']) <= 1 else logic['m_lab']
                h_val_1wk = sqm * rate * m_q; l_val = h_val_1wk * lab_p 
                new_rows.append({
                    "Qty": m_q, "Product": f"Structure {span}m x {length}m", "Unit Rate": sqm*rate, "Total": 0.0, 
                    "Min_Lab": logic['min_lab'], "Raw_Lab": l_val, "Lab_Math": f"Structure {span}x{length} (Week 1): ${h_val_1wk:,.2f} x {int(lab_p*100)}% = ${l_val:,.2f}", 
                    "KG": (sqm*15)*m_q, "Is_Marquee": True, "Hire_Math_Str": "" 
                })
                legs = ((length/logic['bay'])+1)*2
                if m_sec == "Weights":
                    w_tot = int(legs*6*m_q); w_h = w_tot * CONFIG["WEIGHT_HIRE"]; w_l = w_tot * CONFIG["WEIGHT_LABOUR"]
                    new_rows.append({"Qty": w_tot, "Product": "30kg Weights", "Unit Rate": CONFIG["WEIGHT_HIRE"], "Total": 0.0, "Min_Lab": 0, "Raw_Lab": w_l, "Lab_Math": f"Weights: {w_tot} units x $1.65 = ${w_l:,.2f}", "KG": w_tot*30, "Is_Marquee": True, "Hire_Math_Str": ""})
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True); st.rerun()

with col_cat:
    st.markdown("### 🪵 Flooring & Catalog")
    cat_type = st.radio("Category", ["Flooring", "Accessories"], horizontal=True)
    p_sel = st.selectbox("Product", list(GENERAL_PRODUCTS[cat_type].keys()))
    f_qty = None
    if cat_type == "Flooring":
        data = GENERAL_PRODUCTS["Flooring"][p_sel]
        input_mode = st.radio("Mode", ["SQM", "Sheets"], horizontal=True) if data['w'] > 0 else "SQM"
        if input_mode == "Sheets":
            num_sheets = st.number_input("Number of Sheets", min_value=0, value=None, placeholder="Sheets...")
            if num_sheets:
                sqm_per = data['w'] * data['l']; f_qty = num_sheets * sqm_per; label = f"{p_sel} ({num_sheets} sheets)"
        else:
            req_sqm = st.number_input("Area (SQM)", min_value=0.0, value=None, placeholder="SQM...")
            if req_sqm:
                if data['w'] > 0:
                    sqm_per = data['w'] * data['l']; sheets_needed = math.ceil(req_sqm / sqm_per)
                    f_qty = sheets_needed * sqm_per; label = f"{p_sel} ({sheets_needed} sheets)"
                else: f_qty = req_sqm; label = p_sel
    else:
        f_qty = st.number_input("Quantity", min_value=0.0, value=None, placeholder="Qty...")
        label = p_sel

    if st.button("Add to Quote") and f_qty:
        data = GENERAL_PRODUCTS[cat_type][p_sel]
        f_rate = (data['block']/4) if (weeks >= 4 and 'block' in data) else data['rate']
        h_val_1wk = f_qty * f_rate; l_val = f_qty * data.get('lab_fix', (h_val_1wk * data.get('lab_p', 0)))
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{ 
            "Qty": f_qty, "Product": label, "Unit Rate": f_rate, "Total": 0.0, "Min_Lab": 0, "Raw_Lab": l_val, 
            "Lab_Math": f"{p_sel}: {f_qty:,.2f} x ${data.get('lab_fix', 0)} = ${l_val:,.2f}" if 'lab_fix' in data else f"{p_sel}: ${h_val_1wk:,.2f} x {int(data.get('lab_p',0)*100)}% = ${l_val:,.2f}", 
            "KG": f_qty * data.get('kg_sqm', data.get('kg', 0)), "Is_Marquee": False, "Hire_Math_Str": "" 
        }])], ignore_index=True); st.rerun()

if not st.session_state.df.empty:
    st.divider(); st.subheader("Quote Summary")
    h_c1, h_c2, h_c3, h_c4, h_c5 = st.columns([0.5, 1, 3, 1.5, 1.5])
    h_c2.write("**Qty**"); h_c3.write("**Product**"); h_c4.write("**Rate**"); h_c5.write("**Total**")
    
    h_tot_contract = 0.0
    h_tot_week1 = 0.0
    raw_l_sum = 0.0
    max_min_l = 0.0
    total_kg = 0.0
    
    for idx, row in st.session_state.df.iterrows():
        base_hire_wk1 = row["Qty"] * row["Unit Rate"]
        h_tot_week1 += base_hire_wk1
        
        # Scaling Multiplier Logic
        if row["Is_Marquee"] and "Weight" not in row["Product"]:
            # Marquee Rule: 100% Wk 1, 50% Subsequent
            extra_weeks = max(0, weeks - 1)
            line_h = base_hire_wk1 + (extra_weeks * base_hire_wk1 * 0.5)
            math_str = f"{row['Product']} (x{row['Qty']}): Wk 1 @ 100% (${base_hire_wk1:,.2f}) + {extra_weeks} Wks @ 50% (${base_hire_wk1*0.5:,.2f}/wk) = ${line_h:,.2f}"
        elif any(f in row["Product"] for f in ["I-Trac", "Supa-Trac", "Plastorip", "Rollout", "MOJO"]):
            # Flooring/Barrier Rule: Weeks * Rate
            line_h = base_hire_wk1 * weeks
            math_str = f"{row['Product']} (x{row['Qty']:,.2f}): ${row['Unit Rate']:,.2f}/wk x {weeks} weeks = ${line_h:,.2f}"
        else:
            # Accessories are usually flat
            line_h = base_hire_wk1
            math_str = f"{row['Product']} (x{row['Qty']:,.2f}): ${row['Unit Rate']:,.2f} flat rate = ${line_h:,.2f}"
        
        st.session_state.df.at[idx, "Total"] = line_h
        st.session_state.df.at[idx, "Hire_Math_Str"] = math_str
        h_tot_contract += line_h
        raw_l_sum += row["Raw_Lab"]
        max_min_l = max(max_min_l, row["Min_Lab"])
        total_kg += row["KG"]
        
        c1, c2, c3, c4, c5 = st.columns([0.5, 1, 3, 1.5, 1.5])
        if c1.button("🗑️", key=f"del_{idx}"): st.session_state.df = st.session_state.df.drop(idx); st.rerun()
        c2.write(f"{row['Qty']:,.2f}"); c3.write(row['Product']); c4.write(f"${row['Unit Rate']:,.2f}"); c5.write(f"${line_h:,.2f}")
    
    trucks = math.ceil(total_kg / CONFIG["TRUCK_PAYLOAD"]) if total_kg > 0 else 1
    final_lab = max(max_min_l, raw_l_sum)
    waiver = h_tot_week1 * 0.07 
    dist = km_in if km_in else 0
    cartage = trucks * dist * 4 * CONFIG["CARTAGE_RATE"]
    
    log_maths = []
    log_maths.append(f"Damage Waiver (Week 1 Hire Only): ${h_tot_week1:,.2f} x 7% = ${waiver:,.2f}")
    log_maths.append(f"Cartage: {trucks} Trucks x {dist}km x 4 trips x ${CONFIG['CARTAGE_RATE']} = ${cartage:,.2f}")

    if cartage_mode == "Free": cartage = 0; log_maths[-1] = "Cartage: FREE"
    if labour_mode == "Free": final_lab = 0
    elif labour_mode == "Include in Hire cost": h_tot_contract += final_lab; final_lab = 0
    
    grand = h_tot_contract + final_lab + waiver + cartage
    
    st.markdown("---")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("HIRE", f"${h_tot_contract:,.2f}"); m2.metric("LABOUR", f"${final_lab:,.2f}"); m3.metric("WAIVER", f"${waiver:,.2f}"); m4.metric("CARTAGE", f"${cartage:,.2f}"); m5.metric("LOAD", f"{total_kg:,.0f}kg"); m6.metric("TRUCKS", f"{trucks}")
    
    st.markdown("### 🛠️ Checklist")
    st.markdown("<div class='guardrail-box'>", unsafe_allow_html=True)
    if st.session_state.status == "Quoted":
        st.checkbox("Email / enquiry printed"); st.checkbox("Quote printed and paperclipped to the front")
    else: st.write("No specific office actions required.")
    st.markdown("</div>", unsafe_allow_html=True)

    h_math_final = st.session_state.df["Hire_Math_Str"].tolist()
    l_math_final = st.session_state.df["Lab_Math"].tolist()
    
    pdf_b = create_calculation_pdf(st.session_state.active_project, st.session_state.df, h_tot_contract, final_lab, waiver, cartage, grand, km_in if km_in else 0, weeks, start_d, end_d, h_math_final, l_math_final, total_kg, trucks, log_maths, st.session_state.status)
    st.download_button(f"📥 DOWNLOAD {st.session_state.status.upper()} PDF", pdf_b, file_name=f"{st.session_state.active_project}_Analysis.pdf")
