import streamlit as st
import math
import pandas as pd
from datetime import date
from fpdf import FPDF
import re
import json
import os

# --- v31.2 CONFIG & DIRECTORIES ---
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

# --- v29.0 VISUAL STYLING ---
st.markdown("""
    <style>
    .main { background-color: #FFFFFF !important; }
    h3 { 
        color: #FFFFFF !important; 
        border-left: 5px solid #00E676; 
        padding: 10px 15px; 
        background-color: #1A1D2D; 
        border-radius: 0 10px 10px 0; 
        margin-top: 20px; 
    }
    div.stMetric {
        background-color: #1A1D2D !important;
        padding: 20px !important;
        border-radius: 12px !important;
        border: 2px solid #3D5AFE !important;
    }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 16px !important; }
    div.stButton > button:first-child {
        background-color: #3D5AFE;
        color: white;
        border-radius: 10px;
        height: 50px;
        font-weight: bold;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- MASTER DATA ---
CONFIG = {"WEIGHT_UNIT_KG": 30, "WEIGHT_HIRE": 6.60, "WEIGHT_LABOUR": 1.65, "TRUCK_PAYLOAD": 6000, "CARTAGE_RATE": 3.50}

STRUCT_LOGIC = {
    4:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    6:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    9:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    10: {"bay": 5, "s_rate": 23.00, "m_rate": 16.55, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    12: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 1500.00},
    15: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 1500.00},
    20: {"bay": 5, "s_rate": 19.95, "m_rate": 19.95, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 0.00},
}

MARQUEE_UNITS = {
    "3m x 3m Hi Top": {"rate": 198.45, "lab": 0.55, "min": 350.0, "legs": 4, "kg": 50},
    "3m x 3m Shade": {"rate": 198.45, "lab": 0.55, "min": 350.0, "legs": 4, "kg": 50},
    "3m x 6m Shade": {"rate": 396.90, "lab": 0.55, "min": 350.0, "legs": 6, "kg": 80}
}

GENERAL_PRODUCTS = {
    "Flooring": {
        "Supa-Trac®": {"rate": 11.55, "block": 25.00, "lab_fix": 4.65, "kg_sqm": 4.5, "unit": "SQM"},
        "I-Trac®": {"rate": 23.40, "block": 46.80, "lab_fix": 4.65, "kg_sqm": 15.0, "unit": "SQM"},
        "Plastorip": {"rate": 14.00, "block": 30.00, "lab_fix": 4.65, "kg_sqm": 4.0, "unit": "SQM"}
    }
}

STAGES = ["Email", "Quoted", "Accepted", "Paid", "On Hire", "Returned"]
STAGE_COLORS = {"Email": "#3D5AFE", "Quoted": "#FF9100", "Accepted": "#00E676", "Paid": "#00B8D4", "On Hire": "#D500F9", "Returned": "#757575"}

# --- PDF ENGINE (REBUILT FOR REQUESTED FORMAT) ---
def create_calculation_pdf(name, df, subtotal, labour, waiver, cartage, grand, km, weeks, start, end, h_maths, l_details, kg, trucks, status):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"No Fuss Event Hire - Calculation Analysis", ln=True, align="C")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, f"PROJECT: {name} | STATUS: {status.upper()}", ln=True, align="C")
    pdf.cell(0, 7, f"HIRE PERIOD: {start} to {end} ({weeks} Week(s))", ln=True, align="C")
    pdf.ln(5)

    # 1. HIRE CALCULATIONS
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " CALCULATIONS (Hire)", 0, 1, "L", True)
    pdf.set_font("Arial", "", 10)
    for h in h_maths:
        pdf.cell(0, 7, f" {h}", border="B", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, f" TOTAL HIRE: ${subtotal:,.2f}", ln=True, align="R")
    pdf.ln(5)

    # 2. LABOUR CALCULATIONS
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " LABOUR", 0, 1, "L", True)
    pdf.set_font("Arial", "", 10)
    for l in l_details:
        pdf.cell(0, 7, f" {l}", border="B", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, f" TOTAL LABOUR: ${labour:,.2f}", ln=True, align="R")
    pdf.ln(5)

    # 3. DAMAGE WAIVER
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " DAMAGE WAIVER", 0, 1, "L", True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f" Calculation: ${subtotal:,.2f} (Hire Total) x 7% Damage Waiver", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, f" WAIVER TOTAL: ${waiver:,.2f}", ln=True, align="R")
    pdf.ln(5)

    # 4. CARTAGE
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " CARTAGE", 0, 1, "L", True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f" Calculation: {trucks} Truck(s) x {km}km x 4 trips x ${CONFIG['CARTAGE_RATE']}/km", ln=True)
    pdf.cell(0, 8, f" Total Payload Weight: {kg:,.0f}kg", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, f" CARTAGE TOTAL: ${cartage:,.2f}", ln=True, align="R")
    
    # Grand Total
    pdf.ln(10)
    pdf.set_fill_color(26, 29, 45)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 15, f" GRAND TOTAL (EX GST): ${grand:,.2f} ", 0, 1, "R", True)
    
    return bytes(pdf.output())

# --- APP LOGIC (Rest of script stays same for Save/Load/Calculator) ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Is_Marquee", "Hire_Math_Str"])
if 'status' not in st.session_state:
    st.session_state.status = "Email"
if 'active_project' not in st.session_state:
    st.session_state.active_project = "New Project"

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
        loaded = json.load(f)
        st.session_state.df = pd.DataFrame(loaded["items"])
        st.session_state.status = loaded.get("status", "Email") if loaded.get("status") in STAGES else "Email"
        st.session_state.active_project = loaded.get("proj", load_choice)
        st.rerun()

st.title("📦 No Fuss Unified Engine (v31.2)")
st.markdown(f"### 📍 Workflow Selection: {st.session_state.active_project}")
st.session_state.status = st.selectbox("Current Stage", options=STAGES, index=STAGES.index(st.session_state.status))
st.markdown(f"<div style='height: 12px; background-color: {STAGE_COLORS[st.session_state.status]}; border-radius: 6px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
start_d = c1.date_input("Hire Start", value=date.today())
end_d = c2.date_input("Hire End", value=date.today())
km_in = c3.number_input("One-Way Distance (KM)", min_value=0.0)
weeks = math.ceil(((end_d - start_d).days) / 7) if (end_d - start_d).days > 0 else 1

st.divider(); col_mq, col_cat = st.columns(2)
with col_mq:
    st.markdown("### ⚡ Marquee & Structure")
    m_in = st.text_input("Size (e.g. 10x15)")
    m_q = st.number_input("Quantity", min_value=1, key="mq")
    m_sec = st.radio("Securing", ["Weights", "Pegging"], horizontal=True)
    if st.button("Add Marquee Item"):
        nums = re.findall(r'\d+', m_in)
        if len(nums) >= 2:
            span, length = int(nums[0]), int(nums[1])
            new_rows = []
            if span == 3 and (length == 3 or length == 6):
                key = "3m x 3m Hi Top" if length == 3 else "3m x 6m Shade"
                data = MARQUEE_UNITS[key]
                h_val = data['rate'] * m_q; l_val = h_val * data['lab']
                new_rows.append({"Qty": m_q, "Product": key, "Unit Rate": data['rate'], "Total": 0.0, "Min_Lab": data['min'], "Raw_Lab": l_val, "Lab_Math": f"{key}: ${h_val:,.2f} x 55% = ${l_val:,.2f}", "KG": data['kg']*m_q, "Is_Marquee": True, "Hire_Math_Str": f"{m_q} - {key} x ${data['rate']:,.2f} = ${h_val:,.2f}"})
                legs = 4
            else:
                logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
                bays = math.ceil(length/logic['bay']); sqm = span*length
                rate = logic['s_rate'] if bays == 1 else logic['m_rate']
                lab_p = logic['s_lab'] if bays == 1 else logic['m_lab']
                h_val = sqm * rate * m_q; l_val = h_val * lab_p
                new_rows.append({"Qty": m_q, "Product": f"Structure {span}m x {length}m", "Unit Rate": sqm*rate, "Total": 0.0, "Min_Lab": logic['min_lab'], "Raw_Lab": l_val, "Lab_Math": f"Structure {span}x{length}: ${h_val:,.2f} x {int(lab_p*100)}% = ${l_val:,.2f}", "KG": (sqm*15)*m_q, "Is_Marquee": True, "Hire_Math_Str": f"{m_q} - Structure {span}m x {length}m ({sqm}sqm x ${rate:,.2f}) = ${h_val:,.2f}" })
                legs = ((length/logic['bay'])+1)*2
            if m_sec == "Weights":
                w_tot = int(legs*6*m_q)
                w_h = w_tot * CONFIG["WEIGHT_HIRE"]
                w_l = w_tot * CONFIG["WEIGHT_LABOUR"]
                new_rows.append({"Qty": w_tot, "Product": "30kg Weights", "Unit Rate": CONFIG["WEIGHT_HIRE"], "Total": 0.0, "Min_Lab": 0, "Raw_Lab": w_l, "Lab_Math": f"Weights: {w_tot} units x $1.65 = ${w_l:,.2f}", "KG": w_tot*30, "Is_Marquee": True, "Hire_Math_Str": f"{w_tot} - Weights x $6.60 = ${w_h:,.2f}"})
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True); st.rerun()

with col_cat:
    st.markdown("### 🪵 Product Catalog")
    p_sel = st.selectbox("Product", list(GENERAL_PRODUCTS["Flooring"].keys()))
    f_qty = st.number_input("Amount (Qty/SQM)", min_value=0.0)
    if st.button("Add Product"):
        data = GENERAL_PRODUCTS["Flooring"][p_sel]
        f_rate = (data['block']/4) if (weeks >= 4 and 'block' in data) else data['rate']
        h_val = f_qty * f_rate; l_val = f_qty * data['lab_fix']
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
            "Qty": f_qty, "Product": p_sel, "Unit Rate": f_rate, "Total": 0.0, "Min_Lab": 0, "Raw_Lab": l_val, "Lab_Math": f"{p_sel}: {f_qty}sqm x ${data['lab_fix']} = ${l_val:,.2f}", "KG": f_qty * data.get('kg', data.get('kg_sqm', 0)), "Is_Marquee": False, "Hire_Math_Str": f"{f_qty} - {p_sel} x ${f_rate:,.2f} = ${h_val:,.2f}"
        }])], ignore_index=True); st.rerun()

if not st.session_state.df.empty:
    st.divider(); st.data_editor(st.session_state.df[["Qty", "Product", "Unit Rate", "Total"]], use_container_width=True)
    h_tot, raw_l_sum, max_min_l, total_kg = 0.0, 0.0, 0.0, 0.0
    h_math, l_math = [], []
    for idx, row in st.session_state.df.iterrows():
        line_h = row["Qty"] * row["Unit Rate"] * (weeks if row["Is_Marquee"] and "Weight" not in row["Product"] else 1)
        h_tot += line_h; raw_l_sum += row["Raw_Lab"]; max_min_l = max(max_min_l, row["Min_Lab"])
        total_kg += row["KG"]; st.session_state.df.at[idx, "Total"] = line_h
        if row["Lab_Math"]: l_math.append(row["Lab_Math"])
        if row["Hire_Math_Str"]: h_math.append(row["Hire_Math_Str"])
    
    trucks = math.ceil(total_kg / CONFIG["TRUCK_PAYLOAD"]) if total_kg > 0 else 1
    final_lab = max(max_min_l, raw_l_sum); waiver = h_tot * 0.07; cartage = trucks * km_in * 4 * CONFIG["CARTAGE_RATE"]; grand = h_tot + final_lab + waiver + cartage
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE", f"${h_tot:,.2f}"); m2.metric("LABOUR", f"${final_lab:,.2f}"); m3.metric("LOAD", f"{total_kg:,.0f}kg"); m4.metric("TRUCKS", f"{trucks}")
    
    pdf_b = create_calculation_pdf(st.session_state.active_project, st.session_state.df, h_tot, final_lab, waiver, cartage, grand, km_in, weeks, start_d, end_d, h_math, l_math, total_kg, trucks, st.session_state.status)
    st.download_button(f"📥 DOWNLOAD {st.session_state.status.upper()} PDF", pdf_b, file_name=f"{st.session_state.active_project}_Analysis.pdf")
    if st.button("RESET ENGINE"): st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.session_state.status = "Email"; st.session_state.active_project = "New Project"; st.rerun()
