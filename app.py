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
        st.title("🔒 Dual-Engine Access")
        password = st.text_input("Access Code", type="password")
        if st.button("Unlock"):
            if password == "NoFuss2026":
                st.session_state.password_correct = True
                st.rerun()
        return False
    return True

if not check_password():
    st.stop()

# --- ENGINE A: v29.3 DATA (Marquees/Structures) ---
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
    "3x3 Hi Top": {"rate": 198.45, "lab": 0.55, "min": 350.0, "legs": 4, "kg": 50},
    "3x3 Shade": {"rate": 198.45, "lab": 0.55, "min": 350.0, "legs": 4, "kg": 50},
    "3x6 Shade": {"rate": 396.90, "lab": 0.55, "min": 350.0, "legs": 6, "kg": 80}
}

# --- ENGINE B: v27.1 DATA (Flooring Block Logic) ---
FLOORING_LOGIC = {
    "Supa-Trac®": {"rate": 11.55, "block": 25.00, "lab": 0.40, "kg": 4.5},
    "I-Trac®": {"rate": 23.40, "block": 46.80, "lab": 0.40, "kg": 15.0}
}

# --- PDF ENGINE (Unified) ---
def create_unified_pdf(name, df, subtotal, labour, waiver, cartage, grand, km, weeks, lab_details, total_kg, trucks):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14); pdf.cell(0, 10, "No Fuss Event Hire - Combined Quote Analysis", ln=True, align="C")
    pdf.set_font("Arial", "", 9); pdf.cell(0, 10, f"Generated: {date.today()} | Payload: {total_kg:,.0f}kg ({trucks} Trucks)", ln=True); pdf.ln(5)

    # Table Header
    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255)
    pdf.cell(80, 10, " Item", 1, 0, "L", True); pdf.cell(20, 10, " Qty", 1, 0, "C", True)
    pdf.cell(35, 10, " Rate/Basis", 1, 0, "C", True); pdf.cell(45, 10, " Total (Ex GST)", 1, 1, "R", True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    for _, row in df.iterrows():
        pdf.cell(80, 8, f" {row['Product']}", 1)
        pdf.cell(20, 8, f" {row['Qty']}", 1, 0, "C")
        pdf.cell(35, 8, f" ${row['Unit Rate']:,.2f}", 1, 0, "C")
        pdf.cell(45, 8, f" ${row['Total']:,.2f}", 1, 1, "R")
    
    pdf.ln(10); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, "V29.3 & V27.1 INTEGRATED MATH BREAKDOWN:", ln=True)
    pdf.set_font("Arial", "", 10)
    for line in lab_details: pdf.cell(0, 6, f"- {line}", ln=True)

    pdf.ln(5); pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, f"Base Hire: ${subtotal:,.2f}", ln=True)
    pdf.cell(0, 7, f"Total Labour: ${labour:,.2f}", ln=True)
    pdf.cell(0, 7, f"Damage Waiver (7%): ${waiver:,.2f}", ln=True)
    pdf.cell(0, 7, f"Cartage ({trucks} Trucks): ${cartage:,.2f}", ln=True)
    pdf.ln(5); pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, f"GRAND TOTAL: ${grand:,.2f}", 1, 1, "R")
    return bytes(pdf.output())

# --- APP UI ---
st.set_page_config(page_title="v30.0 Dual Engine", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Engine", "Hire_Math"])

st.title("🏗️ Dual-Engine Quoter (v30.0)")

# Global Logistics
c1, c2, c3 = st.columns(3)
start_d = c1.date_input("Start", value=date.today())
end_d = c2.date_input("End", value=date.today())
km_in = c3.number_input("Distance (KM)", min_value=0.0)
weeks = math.ceil(((end_d - start_d).days) / 7) if (end_d - start_d).days > 0 else 1

tab1, tab2 = st.tabs(["Engine A (Marquees v29.3)", "Engine B (Flooring v27.1)"])

# ENGINE A LOGIC
with tab1:
    m_in, m_q, m_s = st.columns([3, 1, 1])
    q_input = m_in.text_input("Span x Length (e.g. 4x12)")
    q_qty = m_q.number_input("Qty", min_value=1, key="mqty")
    q_sec = m_s.radio("Securing", ["Weights", "Pegging"])
    if st.button("Add Marquee Item"):
        nums = re.findall(r'\d+', q_input)
        if len(nums) >= 2:
            span, length = int(nums[0]), int(nums[1])
            new_rows = []
            # v29.3 Logic
            if span == 3 and (length == 3 or length == 6):
                key = f"3x{length} {'Hi Top' if length==3 else 'Shade'}"
                data = MARQUEE_UNITS.get(key, MARQUEE_UNITS["3x3 Hi Top"])
                h_val = data['rate'] * q_qty; l_val = h_val * data['lab']
                new_rows.append({"Qty": q_qty, "Product": key, "Unit Rate": data['rate'], "Total": 0.0, "Min_Lab": data['min'], "Raw_Lab": l_val, "Lab_Math": f"{key}: ${h_val:,.2f} x 55% = ${l_val:,.2f}", "KG": data['kg']*q_qty, "Engine": "A", "Hire_Math": f"{q_qty} - {key} x ${data['rate']}"})
                legs = data['legs']
            else:
                logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
                bays = math.ceil(length/logic['bay']); sqm = span*length
                rate = logic['s_rate'] if bays == 1 else logic['m_rate']
                lab_p = logic['s_lab'] if bays == 1 else logic['m_lab']
                h_val = sqm * rate * q_qty; l_val = h_val * lab_p
                new_rows.append({"Qty": q_qty, "Product": f"Structure {span}x{length}", "Unit Rate": sqm*rate, "Total": 0.0, "Min_Lab": logic['min_lab'], "Raw_Lab": l_val, "Lab_Math": f"{span}x{length}: ${h_val:,.2f} x {int(lab_p*100)}% = ${l_val:,.2f}", "KG": (sqm*2.5)*q_qty, "Engine": "A", "Hire_Math": f"{q_qty} - Structure {span}x{length} ({sqm}sqm x ${rate})"})
                legs = ((length/logic['bay'])+1)*2
            
            if q_sec == "Weights":
                w_total = int(legs*6*q_qty); w_h = w_total*6.60; w_l = w_h*0.25
                new_rows.append({"Qty": w_total, "Product": "30kg Weights", "Unit Rate": 6.60, "Total": 0.0, "Min_Lab": 0, "Raw_Lab": w_l, "Lab_Math": f"Weights: ${w_h:,.2f} x 25% = ${w_l:,.2f}", "KG": w_total*30, "Engine": "A", "Hire_Math": f"{w_total} - Weights x $6.60"})
            
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True); st.rerun()

# ENGINE B LOGIC
with tab2:
    f_p, f_q = st.columns(2)
    f_name = f_p.selectbox("Product", list(FLOORING_LOGIC.keys()))
    f_qty = f_q.number_input("SQM Amount", min_value=0.0)
    if st.button("Add Flooring Item"):
        data = FLOORING_LOGIC[f_name]
        # v27.1 Block Logic
        final_rate = (data['block']/4) if weeks >= 4 else data['rate']
        h_val = f_qty * final_rate; l_val = h_val * data['lab']
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
            "Qty": f_qty, "Product": f_name, "Unit Rate": final_rate, "Total": 0.0, "Min_Lab": 0, "Raw_Lab": l_val, "Lab_Math": f"{f_name}: ${h_val:,.2f} x 40% = ${l_val:,.2f}", "KG": f_qty*data['kg'], "Engine": "B", "Hire_Math": f"{f_qty}sqm - {f_name} x ${final_rate:,.2f} (Block rate applied: {weeks>=4})"
        }])], ignore_index=True); st.rerun()

# --- CALCS & DISPLAY ---
if not st.session_state.df.empty:
    st.divider()
    st.data_editor(st.session_state.df[["Qty", "Product", "Unit Rate", "Total"]], use_container_width=True)
    
    h_tot, raw_lab_sum, max_min_lab, total_kg = 0.0, 0.0, 0.0, 0.0
    lab_math_lines = []
    
    for idx, row in st.session_state.df.iterrows():
        is_mq = row["Engine"] == "A"
        line_h = row["Qty"] * row["Unit Rate"] * (weeks if is_mq and "Weights" not in row["Product"] else 1)
        h_tot += line_h; raw_lab_sum += row["Raw_Lab"]; max_min_lab = max(max_min_lab, row["Min_Lab"])
        total_kg += row["KG"]; st.session_state.df.at[idx, "Total"] = line_h
        lab_math_lines.append(row["Lab_Math"])

    trucks = math.ceil(total_kg / 6000) if total_kg > 0 else 1
    final_lab = max(max_min_lab, raw_lab_sum)
    waiver = h_tot * 0.07; cartage = trucks * km_in * 4 * 3.50; grand = h_tot + final_lab + waiver + cartage

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE", f"${h_tot:,.2f}"); m2.metric("LABOUR", f"${final_lab:,.2f}"); m3.metric("WAIVER", f"${waiver:,.2f}"); m4.metric("CARTAGE", f"${cartage:,.2f}")
    
    fn = st.text_input("Project Name:")
    pdf_bytes = create_unified_pdf(fn, st.session_state.df, h_tot, final_lab, waiver, cartage, grand, km_in, weeks, lab_math_lines, total_kg, trucks)
    st.download_button("📥 DOWNLOAD PDF", pdf_bytes, file_name=f"{fn}_Calculation.pdf")
    if st.button("RESET"): st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.rerun()
