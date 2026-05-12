import streamlit as st
from streamlit_gsheets import GSheetsConnection
import math
import pandas as pd
from datetime import date
from fpdf import FPDF
import io
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

# 2. DATABASE CONNECTION
conn = st.connection("gsheets", type=GSheetsConnection)

# --- PDF GENERATION (v27.3) ---
def create_calculation_pdf(name, df, subtotal, labour, waiver, cartage, grand_total, km, weeks):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "No Fuss Event Hire - Internal Calculation Sheet", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Generated on: {date.today()}", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, f"Quote: {name}", ln=True)
    pdf.set_font("Arial", "", 11); pdf.cell(0, 8, f"Hire Duration: {weeks} Week(s) | Distance: {km} km", ln=True)
    pdf.ln(5)

    # Main Table
    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
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
            qty, total, p_name = row['Qty'], row['Total'], row['Product']
            if "Marquee" in p_name:
                pdf.cell(0, 6, f"{qty} - {p_name} x ${row['Unit Rate']:,.2f} = ${total:,.2f}", ln=True)
            else:
                pdf.cell(0, 6, f"{qty} - {row['Product']} x ${row['Unit Rate']:,.2f} = ${total:,.2f}", ln=True)

    pdf.ln(4); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Labour: ${labour:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        if row['Is_Lab_Line']:
            clean_name = row['Product'].replace("Labour (", "").replace(")", "")
            pdf.cell(0, 6, f"{row['Qty']} - {clean_name} x 55% = ${row['Total']:,.2f}", ln=True)

    pdf.ln(4); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Damage Waiver (7%): ${waiver:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(0, 6, f"${subtotal:,.2f} x 0.07", ln=True)
    pdf.ln(2); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Cartage Total: ${cartage:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(0, 6, f"{km} km x 4 trips x $3.50/km", ln=True)
    
    pdf.ln(10); pdf.set_font("Arial", "B", 14); pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, f"GRAND TOTAL (EX GST): ${grand_total:,.2f}", 1, 1, "R", True)
    return bytes(pdf.output())

# 3. MASTER DATA
MARQUEE_SERIES = {
    3: {"starter_hire": 350.0, "starter_lab": 150.0, "ext_hire": 180.0, "ext_lab": 80.0, "bay_len": 3, "w_per_bay": 8},
    10: {"starter_hire": 1250.0, "starter_lab": 550.0, "ext_hire": 750.0, "ext_lab": 350.0, "bay_len": 5, "w_per_bay": 12}
}

FLOORING_CAT = {
    "Supa-trac flooring": {"w1_3": 11.55, "block": 25.00, "labour": 4.65, "unit": "SQM"},
    "I-Trac flooring": {"w1_3": 23.40, "block": 46.80, "labour": 4.65, "unit": "SQM"}
}

# 4. APP UI
st.set_page_config(page_title="No Fuss Quote Pro v27.3", layout="wide")
st.markdown("<style>.main { background-color: #FFFFFF !important; } h3 { color: #FFFFFF !important; border-left: 5px solid #00E676; padding: 10px 15px; background-color: #1A1D2D; border-radius: 0 10px 10px 0; margin-top: 20px; } div.stMetric { background-color: #1A1D2D !important; padding: 20px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; } div[data-testid='stMetricValue'] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; } [data-testid='stMetricLabel'] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 16px !important; } div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; width: 100%; }</style>", unsafe_allow_html=True)

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Block_Rate", "No_Waiver", "Unit_Type", "Is_Lab_Line"])

st.title("📦 No Fuss Quote Pro")

# LOGISTICS
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today())
end_date = c2.date_input("Hire End", value=date.today())
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=0.0)
live_weeks = math.ceil(((end_date - start_date).days) / 7) if (end_date - start_date).days > 0 else 1

# --- SECTION A: MARQUEES ---
st.markdown("### ⚡ QUICK-ADD MARQUEE")
mq1, mq2 = st.columns([3, 1])
q_input = mq1.text_input("Type Size (e.g., 4x12, 10x15)", placeholder="Width x Length...")
q_sec = mq2.radio("Securing", ["Weights", "Pegging"], horizontal=True)

if st.button("ADD MARQUEE"):
    nums = re.findall(r'\d+', q_input)
    if len(nums) == 2:
        val1, val2 = int(nums[0]), int(nums[1])
        # Determine Width vs Length (Width is usually the series 3 or 10)
        # If user puts 4x12, width is 4, length is 12. We use 3m series logic.
        width = val1 if val1 in [3, 10] else (val2 if val2 in [3, 10] else val1)
        length = val2 if width == val1 else val1
        
        series_key = 10 if width >= 10 else 3
        data = MARQUEE_SERIES[series_key]
        bays = math.ceil(length / data['bay_len'])
        
        hire_cost = data['starter_hire'] + ((bays - 1) * data['ext_hire'])
        labour_cost = data['starter_lab'] + ((bays - 1) * data['ext_lab'])
        
        new_rows = [
            {"Qty": 1, "Product": f"Marquee {val1} X {val2}", "Unit Rate": hire_cost, "Total": 0.0, "Block_Rate": hire_cost, "No_Waiver": False, "Unit_Type": "ea", "Is_Lab_Line": False},
            {"Qty": 1, "Product": f"Labour (Marquee {val1} X {val2})", "Unit Rate": labour_cost, "Total": 0.0, "Block_Rate": labour_cost, "No_Waiver": True, "Unit_Type": "ea", "Is_Lab_Line": True}
        ]
        if q_sec == "Weights":
            w_qty = bays * data['w_per_bay']
            new_rows.append({"Qty": w_qty, "Product": f"Orange Weights (For {val1}x{val2})", "Unit Rate": 6.60, "Total": 0.0, "Block_Rate": 6.60, "No_Waiver": False, "Unit_Type": "ea", "Is_Lab_Line": False})
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True); st.rerun()
    else: st.error("Format error: use '4x12'")

# --- SECTION B: FLOORING ---
st.markdown("### 🪵 ADD FLOORING")
f1, f2 = st.columns([3, 1])
f_choice = f1.selectbox("Floor Type", list(FLOORING_CAT.keys()))
f_qty = f2.number_input("SQM Amount", min_value=0.0, step=10.0)

if st.button("ADD FLOORING"):
    f_data = FLOORING_CAT[f_choice]
    new_f_rows = [
        {"Qty": f_qty, "Product": f_choice, "Unit Rate": f_data['w1_3'], "Total": 0.0, "Block_Rate": f_data['block'], "No_Waiver": False, "Unit_Type": "SQM", "Is_Lab_Line": False},
        {"Qty": f_qty, "Product": f"Labour ({f_choice})", "Unit Rate": f_data['labour'], "Total": 0.0, "Block_Rate": f_data['labour'], "No_Waiver": True, "Unit_Type": "SQM", "Is_Lab_Line": True}
    ]
    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_f_rows)], ignore_index=True); st.rerun()

# --- FINANCES ---
if not st.session_state.df.empty:
    st.markdown("### 🏗️ QUOTED ITEMS")
    edited_df = st.data_editor(st.session_state.df[["Qty", "Unit_Type", "Product", "Unit Rate", "Total"]], use_container_width=True)
    
    h_tot, lab_tot, w_tot = 0.0, 0.0, 0.0
    for idx, row in st.session_state.df.iterrows():
        q, r, b, is_lab = row["Qty"], row["Unit Rate"], row["Block_Rate"], row["Is_Lab_Line"]
        final_rate = (b / 4) if (live_weeks >= 4 and row["Unit_Type"] == "SQM") else r
        line_val = q * final_rate * (live_weeks if not is_lab else 1)
        
        if is_lab: lab_tot += line_val
        else:
            h_tot += line_val
            if not row["No_Waiver"]: w_tot += line_val * 0.07
        st.session_state.df.at[idx, "Total"] = line_val

    c_val = km_input * 4 * 3.50
    st.divider(); m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE", f"${h_tot:,.2f}"); m2.metric("LABOUR", f"${lab_tot:,.2f}"); m3.metric("WAIVER", f"${w_tot:,.2f}"); m4.metric("CARTAGE", f"${c_val:,.2f}")
    
    fn = st.text_input("Project Name:")
    pdf_bytes = create_calculation_pdf(fn, st.session_state.df, h_tot, lab_tot, w_tot, c_val, h_tot+lab_tot+w_tot+c_val, km_input, live_weeks)
    st.download_button("📥 DOWNLOAD PDF", pdf_bytes, file_name=f"{fn}_Calculations.pdf")
    if st.button("⚠️ RESET"): st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.rerun()
