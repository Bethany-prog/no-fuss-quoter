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
        st.title("🔒 Private Quoting Access")
        password = st.text_input("Access Code", type="password")
        if st.button("Unlock Engine"):
            if password == "NoFuss2026":
                st.session_state.password_correct = True
                st.rerun()
            else: st.error("❌ Incorrect Code")
        return False
    return True

if not check_password():
    st.stop()

# --- DATA: MASTER RATE CARD (v28.4 - STRICT SPAN LOGIC) ---
STRUCT_LOGIC = {
    3:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00, "w_bay": 8},
    4:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00, "w_bay": 8},
    6:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00, "w_bay": 8},
    9:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00, "w_bay": 8},
    10: {"bay": 5, "s_rate": 23.00, "m_rate": 16.55, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00, "w_bay": 12},
    12: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 1500.00, "w_bay": 12},
    15: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 1500.00, "w_bay": 12},
    20: {"bay": 5, "s_rate": 19.95, "m_rate": 19.95, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 0.00, "w_bay": 16},
}

MARQUEE_UNITS = {
    "3x3 Hi Top": {"rate": 198.45, "lab_perc": 0.55, "min_lab": 350.00, "w": 24},
    "3x3 Shade": {"rate": 198.45, "lab_perc": 0.55, "min_lab": 350.00, "w": 24},
    "3x6 Shade": {"rate": 396.90, "lab_perc": 0.55, "min_lab": 350.00, "w": 32},
    "4.5x4.5": {"rate": 446.51, "lab_perc": 0.55, "min_lab": 350.00, "w": 32}
}

# --- PDF ENGINE ---
def create_calculation_pdf(name, df, subtotal, final_labour, waiver, cartage, grand_total, km, weeks):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "No Fuss Event Hire - Internal Calculation Sheet", ln=True, align="C")
    pdf.set_font("Arial", "", 10); pdf.cell(0, 10, f"Generated on: {date.today()}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, f"Quote: {name}", ln=True)
    pdf.set_font("Arial", "", 11); pdf.cell(0, 8, f"Duration: {weeks} Week(s) | Distance: {km} km", ln=True); pdf.ln(5)

    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 10, " Product", 1, 0, "L", True); pdf.cell(25, 10, " Qty", 1, 0, "C", True)
    pdf.cell(35, 10, " Rate", 1, 0, "C", True); pdf.cell(40, 10, " Total", 1, 1, "R", True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    for _, row in df.iterrows():
        pdf.cell(80, 8, f" {row['Product']}", 1)
        pdf.cell(25, 8, f" {row['Qty']} {row['Unit_Type']}", 1, 0, "C")
        pdf.cell(35, 8, f" ${row['Unit Rate']:,.2f}", 1, 0, "C")
        pdf.cell(40, 8, f" ${row['Total']:,.2f}", 1, 1, "R")
    
    pdf.ln(10); pdf.set_font("Arial", "B", 13); pdf.cell(0, 10, "Financial Breakdown", ln=True)
    pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"BASE HIRE SUBTOTAL: ${subtotal:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        if not row['Is_Lab_Line']:
            meta = f" ({row['Product_Meta']})" if row['Product_Meta'] else ""
            pdf.cell(0, 6, f"{row['Qty']} - {row['Product']}{meta} x ${row['Unit Rate']:,.2f} = ${row['Total']:,.2f}", ln=True)

    pdf.ln(4); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Labour Total: ${final_labour:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(0, 6, "Includes: Marquee/Struct Lab % + Weight Lab ($1.65/ea) + Min Charge logic", ln=True)

    pdf.ln(4); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Damage Waiver (7%): ${waiver:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(0, 6, f"${subtotal:,.2f} x 0.07", ln=True)
    pdf.ln(2); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Cartage Total: ${cartage:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(0, 6, f"{km} km x 4 trips x $3.50/km", ln=True)
    
    pdf.ln(10); pdf.set_font("Arial", "B", 14); pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, f"GRAND TOTAL (EX GST): ${grand_total:,.2f}", 1, 1, "R", True)
    return bytes(pdf.output())

# 4. APP UI
st.set_page_config(page_title="No Fuss Quote Pro v28.4", layout="wide")
st.markdown("<style>.main { background-color: #FFFFFF !important; } h3 { color: #FFFFFF !important; border-left: 5px solid #00E676; padding: 10px 15px; background-color: #1A1D2D; border-radius: 0 10px 10px 0; margin-top: 20px; } div.stMetric { background-color: #1A1D2D !important; padding: 20px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; } div[data-testid='stMetricValue'] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; } [data-testid='stMetricLabel'] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 16px !important; } div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; width: 100%; }</style>", unsafe_allow_html=True)

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Unit_Type", "Product_Meta", "Min_Lab_Floor", "Raw_Lab_Value", "Is_Lab_Line"])

st.title("📦 No Fuss Quote Pro")

# LOGISTICS
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today())
end_date = c2.date_input("Hire End", value=date.today())
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=0.0)
live_weeks = math.ceil(((end_date - start_date).days) / 7) if (end_date - start_date).days > 0 else 1

# --- QUICK-ADD ---
st.markdown("### ⚡ QUICK-ADD")
q_input = st.text_input("Type Size (Span x Length) - e.g., 4x12", placeholder="4x12...")
q_qty = st.number_input("Quantity of Units", min_value=1, value=1)
q_sec = st.radio("Securing", ["Weights", "Pegging"], horizontal=True)

if st.button("ADD TO QUOTE"):
    nums = re.findall(r'\d+', q_input)
    if len(nums) >= 2:
        span, length = int(nums[0]), int(nums[1])
        new_rows = []
        
        # STRICT DEFAULT RULE: 3x3 or 3x6
        if span == 3 and length == 3:
            data = MARQUEE_UNITS["3x3 Hi Top"]
            new_rows.append({"Qty": q_qty, "Product": "3m x 3m Hi Top", "Unit Rate": data['rate'], "Total": 0.0, "Unit_Type": "ea", "Product_Meta": "9sqm", "Min_Lab_Floor": data['min_lab'], "Raw_Lab_Value": data['rate'] * q_qty * data['lab_perc'], "Is_Lab_Line": False})
            weights_needed = data['w'] * q_qty
        elif span == 3 and length == 6:
            data = MARQUEE_UNITS["3x6 Shade"]
            new_rows.append({"Qty": q_qty, "Product": "3m x 6m Shade", "Unit Rate": data['rate'], "Total": 0.0, "Unit_Type": "ea", "Product_Meta": "18sqm", "Min_Lab_Floor": data['min_lab'], "Raw_Lab_Value": data['rate'] * q_qty * data['lab_perc'], "Is_Lab_Line": False})
            weights_needed = data['w'] * q_qty
        else:
            # STRUCTURE LOGIC (Strict: First Num = Span)
            logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
            bays = math.ceil(length / logic['bay'])
            sqm = span * length
            rate = logic['s_rate'] if bays == 1 else logic['m_rate']
            lab_perc = logic['s_lab'] if bays == 1 else logic['m_lab']
            hire_val = sqm * rate
            new_rows.append({"Qty": q_qty, "Product": f"Structure {span}m x {length}m", "Unit Rate": hire_val, "Total": 0.0, "Unit_Type": "ea", "Product_Meta": f"{sqm}sqm", "Min_Lab_Floor": logic['min_lab'], "Raw_Lab_Value": hire_val * q_qty * lab_perc, "Is_Lab_Line": False})
            weights_needed = bays * logic['w_bay'] * q_qty

        if q_sec == "Weights":
            new_rows.append({"Qty": weights_needed, "Product": "Orange Weights", "Unit Rate": 6.60, "Total": 0.0, "Unit_Type": "ea", "Product_Meta": "", "Min_Lab_Floor": 0, "Raw_Lab_Value": weights_needed * 1.65, "Is_Lab_Line": False})

        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True); st.rerun()

# --- FINANCES ---
if not st.session_state.df.empty:
    st.markdown("### 🏗️ QUOTED ITEMS")
    st.data_editor(st.session_state.df[["Qty", "Unit_Type", "Product", "Unit Rate", "Total"]], use_container_width=True)
    
    h_tot, raw_lab_sum, max_min_lab = 0.0, 0.0, 0.0
    for idx, row in st.session_state.df.iterrows():
        line_hire = row["Qty"] * row["Unit Rate"] * live_weeks
        h_tot += line_hire
        raw_lab_sum += row["Raw_Lab_Value"]
        max_min_lab = max(max_min_lab, row["Min_Lab_Floor"])
        st.session_state.df.at[idx, "Total"] = line_hire

    final_lab_charge = max(max_min_lab, raw_lab_sum)
    w_tot = h_tot * 0.07; c_val = km_input * 4 * 3.50; grand = h_tot + final_lab_charge + w_tot + c_val

    st.divider(); col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("HIRE", f"${h_tot:,.2f}"); col_m2.metric("LABOUR", f"${final_lab_charge:,.2f}"); col_m3.metric("WAIVER", f"${w_tot:,.2f}"); col_m4.metric("CARTAGE", f"${c_val:,.2f}")
    
    fn = st.text_input("Project Name:")
    pdf_bytes = create_calculation_pdf(fn, st.session_state.df, h_tot, final_lab_charge, w_tot, c_val, grand, km_input, live_weeks)
    st.download_button("📥 DOWNLOAD PDF", pdf_bytes, file_name=f"{fn}_Calculations.pdf")
    if st.button("⚠️ RESET"): st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.rerun()
