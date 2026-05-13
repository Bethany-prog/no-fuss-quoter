import streamlit as st
import math
import pandas as pd
from datetime import date
from fpdf import FPDF
import re

# 1. PASSWORD PROTECTION
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        st.title("🔒 Unified Engine Access")
        password = st.text_input("Access Code", type="password")
        if st.button("Unlock"):
            if password == "NoFuss2026":
                st.session_state.password_correct = True
                st.rerun()
        return False
    return True

if not check_password():
    st.stop()

# --- STYLING ---
st.set_page_config(page_title="No Fuss Quote Pro v30.6", layout="wide")
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
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; }
    [data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-weight: bold !important; }
    div.stButton > button:first-child {
        background-color: #3D5AFE;
        color: white;
        border-radius: 10px;
        font-weight: bold;
        height: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ---
STRUCT_LOGIC = {
    3:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    4:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    6:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    9:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    10: {"bay": 5, "s_rate": 23.00, "m_rate": 16.55, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    12: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 1500.00},
    15: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 1500.00},
    20: {"bay": 5, "s_rate": 19.95, "m_rate": 19.95, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 0.00},
}
MARQUEE_UNITS = {
    "3x3 Hi Top": {"rate": 198.45, "lab_p": 0.55, "min": 0.00, "legs": 4, "kg": 50},
    "3x3 Shade": {"rate": 198.45, "lab_p": 0.55, "min": 0.00, "legs": 4, "kg": 50},
    "3x6 Shade": {"rate": 396.90, "lab_p": 0.55, "min": 0.00, "legs": 4, "kg": 80},
    "4.5x4.5 Marquee": {"rate": 446.51, "lab_p": 0.55, "min": 0.00, "legs": 4, "kg": 75}
}
GENERAL_PRODUCTS = {
    "Flooring": {
        "Supa-Trac®": {"rate": 11.55, "block": 25.00, "lab_fix": 4.65, "kg_sqm": 4.5, "unit": "SQM"},
        "I-Trac®": {"rate": 23.40, "block": 46.80, "lab_fix": 4.65, "kg_sqm": 15.0, "unit": "SQM"},
        "Plastorip": {"rate": 14.00, "block": 30.00, "lab_fix": 4.65, "kg_sqm": 4.0, "unit": "SQM"},
        "Bog Mats": {"rate": 35.00, "block": 35.00, "lab_fix": 15.00, "kg": 40.0, "unit": "ea"}
    },
    "Furniture": {
        "Chair": {"rate": 2.50, "lab_p": 0.25, "kg": 5, "unit": "ea"},
        "Trestle Table": {"rate": 13.00, "lab_p": 0.25, "kg": 15, "unit": "ea"}
    },
    "Crowd Control": {
        "MOJO Barrier": {"rate": 70.00, "lab_p": 0.40, "kg": 60, "unit": "ea"}
    }
}

# --- PDF ---
def create_unified_pdf(name, df, subtotal, labour, waiver, cartage, grand, km, weeks, lab_details, total_kg, trucks):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14); pdf.cell(0, 10, "No Fuss Event Hire - Internal Calculation Sheet", ln=True, align="C")
    pdf.set_font("Arial", "", 9); pdf.cell(0, 10, f"Generated: {date.today()} | Payload: {total_kg:,.0f}kg ({trucks} Trucks)", ln=True); pdf.ln(5)
    
    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255)
    pdf.cell(80, 10, " Item", 1, 0, "L", True); pdf.cell(20, 10, " Qty", 1, 0, "C", True)
    pdf.cell(35, 10, " Rate", 1, 0, "C", True); pdf.cell(45, 10, " Total", 1, 1, "R", True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    for _, row in df.iterrows():
        pdf.cell(80, 8, f" {row['Product']}", 1)
        pdf.cell(20, 8, f" {row['Qty']}", 1, 0, "C")
        pdf.cell(35, 8, f" ${row['Unit Rate']:,.2f}", 1, 0, "C")
        pdf.cell(45, 8, f" ${row['Total']:,.2f}", 1, 1, "R")
    
    pdf.ln(10); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, "DETAILED LABOUR BREAKDOWN:", ln=True)
    pdf.set_font("Arial", "", 10)
    for line in lab_details: pdf.cell(0, 6, f"- {line}", ln=True)
    
    pdf.ln(5); pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, f"Base Hire: ${subtotal:,.2f}", ln=True)
    pdf.cell(0, 7, f"Total Labour: ${labour:,.2f}", ln=True)
    pdf.cell(0, 7, f"Damage Waiver (7%): ${waiver:,.2f}", ln=True)
    pdf.cell(0, 7, f"Cartage ({trucks} Trucks): ${cartage:,.2f}", ln=True)
    pdf.ln(5); pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, f"GRAND TOTAL: ${grand:,.2f}", 1, 1, "R")
    return bytes(pdf.output())

# --- APP ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Is_Marquee", "Hire_Math_Str"])

st.title("📦 No Fuss Unified Engine (v30.6)")

c1, c2, c3 = st.columns(3)
start_d = c1.date_input("Start Date", value=date.today())
end_d = c2.date_input("End Date", value=date.today())
km_in = c3.number_input("Distance (KM)", min_value=0.0)
weeks = math.ceil(((end_d - start_d).days) / 7) if (end_d - start_d).days > 0 else 1

col_mq, col_cat = st.columns(2)

with col_mq:
    st.markdown("### ⚡ Add Marquees")
    m_in = st.text_input("Size (e.g. 4x12)")
    m_q = st.number_input("Unit Quantity", min_value=1, key="mq")
    m_sec = st.radio("Securing", ["Weights", "Pegging"])
    if st.button("Add Marquee"):
        nums = re.findall(r'\d+', m_in)
        if len(nums) >= 2:
            span, length = int(nums[0]), int(nums[1])
            new_rows = []
            if span == 3 and (length == 3 or length == 6):
                key = "3x3 Hi Top" if length == 3 else "3x6 Shade"
                data = MARQUEE_UNITS[key]
                h_val = data['rate'] * m_q; l_val = h_val * data['lab_p']
                new_rows.append({"Qty": m_q, "Product": key, "Unit Rate": data['rate'], "Total": 0.0, "Min_Lab": data['min'], "Raw_Lab": l_val, "Lab_Math": f"{key}: ${h_val:,.2f} x 55% = ${l_val:,.2f}", "KG": data['kg']*m_q, "Is_Marquee": True, "Hire_Math_Str": f"{m_q} - {key} x ${data['rate']:,.2f} = ${h_val:,.2f}"})
                legs = 4
            else:
                logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
                bays = math.ceil(length/logic['bay']); sqm = span*length
                rate = logic['s_rate'] if bays == 1 else logic['m_rate']
                lab_p = logic['s_lab'] if bays == 1 else logic['m_lab']
                h_val = sqm * rate * m_q; l_val = h_val * lab_p
                new_rows.append({"Qty": m_q, "Product": f"Structure {span}x{length}", "Unit Rate": sqm*rate, "Total": 0.0, "Min_Lab": logic['min_lab'], "Raw_Lab": l_val, "Lab_Math": f"Structure {span}x{length}: ${h_val:,.2f} x {int(lab_p*100)}% = ${l_val:,.2f}", "KG": (sqm*2.5)*m_q, "Is_Marquee": True, "Hire_Math_Str": f"{m_q} - Structure {span}x{length} ({sqm}sqm x ${rate:,.2f}) = ${h_val:,.2f}" })
                legs = ((length/logic['bay'])+1)*2
            if m_sec == "Weights":
                w_tot = int(legs*6*m_q); w_h = w_tot*6.60; w_l = w_h*0.25
                new_rows.append({"Qty": w_tot, "Product": "30kg Weights", "Unit Rate": 6.60, "Total": 0.0, "Min_Lab": 0, "Raw_Lab": w_l, "Lab_Math": f"Weights: ${w_h:,.2f} x 25% = ${w_l:,.2f}", "KG": w_tot*30, "Is_Marquee": True, "Hire_Math_Str": f"{w_tot} - Weights x $6.60 = ${w_h:,.2f}"})
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True); st.rerun()

with col_cat:
    st.markdown("### 🪵 Catalog")
    c_sel = st.selectbox("Category", list(GENERAL_PRODUCTS.keys()))
    p_sel = st.selectbox("Product", list(GENERAL_PRODUCTS[c_sel].keys()))
    f_qty = st.number_input("Amount", min_value=0.0)
    if st.button("Add Product"):
        data = GENERAL_PRODUCTS[c_sel][p_sel]
        f_rate = (data['block']/4) if (weeks >= 4 and 'block' in data) else data['rate']
        h_val = f_qty * f_rate
        l_val = (f_qty * data['lab_fix']) if 'lab_fix' in data else (h_val * data.get('lab_p', 0))
        lab_str = f"{p_sel} Lab: {f_qty} x ${data['lab_fix']:,.2f} = ${l_val:,.2f}" if 'lab_fix' in data else f"{p_sel} Lab: ${h_val:,.2f} x {int(data.get('lab_p',0)*100)}% = ${l_val:,.2f}"
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
            "Qty": f_qty, "Product": p_sel, "Unit Rate": f_rate, "Total": 0.0, "Min_Lab": 0, "Raw_Lab": l_val, "Lab_Math": lab_str if l_val > 0 else "", 
            "KG": f_qty * data.get('kg', data.get('kg_sqm', 0)), "Is_Marquee": False, "Hire_Math_Str": f"{f_qty} - {p_sel} x ${f_rate:,.2f} = ${h_val:,.2f}"
        }])], ignore_index=True); st.rerun()

if not st.session_state.df.empty:
    st.divider()
    st.data_editor(st.session_state.df[["Qty", "Product", "Unit Rate", "Total"]], use_container_width=True)
    h_tot, raw_lab_sum, max_min_lab, total_kg = 0.0, 0.0, 0.0, 0.0
    details = []
    for idx, row in st.session_state.df.iterrows():
        line_h = row["Qty"] * row["Unit Rate"] * (weeks if row["Is_Marquee"] and "Weights" not in row["Product"] else 1)
        h_tot += line_h; raw_lab_sum += row["Raw_Lab"]; max_min_lab = max(max_min_lab, row["Min_Lab"])
        total_kg += row["KG"]; st.session_state.df.at[idx, "Total"] = line_h
        if row["Lab_Math"]: details.append(row["Lab_Math"])

    trucks = math.ceil(total_kg / 6000) if total_kg > 0 else 1
    final_lab = max(max_min_lab, raw_lab_sum)
    waiver = h_tot * 0.07; cartage = trucks * km_in * 4 * 3.50; grand = h_tot + final_lab + waiver + cartage
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE", f"${h_tot:,.2f}"); m2.metric("LABOUR", f"${final_lab:,.2f}"); m3.metric("WAIVER", f"${waiver:,.2f}"); m4.metric("CARTAGE", f"${cartage:,.2f}")
    
    fn = st.text_input("Project Name:")
    pdf_b = create_unified_pdf(fn, st.session_state.df, h_tot, final_lab, waiver, cartage, grand, km_in, weeks, details, total_kg, trucks)
    st.download_button("📥 DOWNLOAD PDF", pdf_b, file_name=f"{fn}_Analysis.pdf")
    if st.button("RESET"): st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.rerun()
