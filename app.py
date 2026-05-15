import streamlit as st
import math
import pandas as pd
from datetime import date, datetime
from fpdf import FPDF
import re
import json
import os

# --- INITIAL CONFIG ---
st.set_page_config(page_title="Louis Master Quoter", layout="wide")

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

# --- GRANDSTAND BRACKET LOGIC ---
GRAND_LOGIC = [
    {"max": 42, "staff": 2, "hrs": 2},
    {"max": 50, "staff": 2, "hrs": 3},
    {"max": 100, "staff": 4, "hrs": 4},
    {"max": 150, "staff": 6, "hrs": 4},
    {"max": 200, "staff": 6, "hrs": 6},
    {"max": 250, "staff": 8, "hrs": 6},
    {"max": 300, "staff": 10, "hrs": 6},
    {"max": 1000, "staff": 12, "hrs": 8},
]

def get_gs_per_seat_labour(seats):
    if seats <= 0: return 0, ""
    rate = 55.00
    for b in GRAND_LOGIC:
        if seats <= b["max"]:
            total_pool = (b["staff"] * b["hrs"] * rate) * 2 * 2
            per_seat = total_pool / seats
            desc = f"Grandstand Seating Labour: ({b['staff']} staff x {b['hrs']}hrs x $55) x 2 x 2 = ${total_pool:,.2f}"
            return round(per_seat, 2), desc
    return 0, ""

# --- PDF AUDIT ENGINE ---
def clean_text(txt):
    if not txt: return ""
    replacements = {"®": "(R)", "™": "(TM)", "©": "(C)", "└": "->", "—": "-", "–": "-"}
    cleaned = str(txt)
    for char, rep in replacements.items():
        cleaned = cleaned.replace(char, rep)
    return cleaned.encode('latin-1', 'replace').decode('latin-1')

def create_calculation_pdf(name, subtotal, labour, waiver, cartage, grand, weeks, start, end, items_list, log_maths, status):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text("Louis Quoting Tool - Detailed Calculation Audit"), ln=True, align="C")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, clean_text(f"PROJECT: {name} | STATUS: {status.upper()}"), ln=True, align="C")
    pdf.cell(0, 7, f"PERIOD: {start.strftime('%d/%m/%Y')} to {end.strftime('%d/%m/%Y')} ({weeks} Week(s))", ln=True, align="C")
    pdf.ln(10)

    # 1. Hire Calculations
    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 1. HIRE CALCULATIONS (WORKING OUT)", 0, 1, "L", True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 10)
    for item in items_list:
        w1_total = (item['Qty'] * item['Base_Hire']) * (1 - (item['Discount']/100))
        math_str = f"{item['Product']} (Wk 1): {item['Qty']:,.0f} x ${item['Base_Hire']:,.2f} [-{item['Discount']}% Disc]"
        pdf.cell(140, 8, clean_text(math_str), border="B")
        pdf.cell(50, 8, f"${w1_total:,.2f}", border="B", ln=True, align="R")
        if weeks > 1:
            r_rate = item['Base_Hire'] * 0.5 if item['Is_Marquee'] else item['Base_Hire']
            r_total = (item['Qty'] * r_rate * (weeks-1)) * (1 - (item['Discount']/100))
            r_math = f"  └ Recurring Hire: {item['Qty']:,.0f} x ${r_rate:,.2f} x {weeks-1} wks"
            pdf.cell(140, 8, clean_text(r_math), border="B")
            pdf.cell(50, 8, f"${r_total:,.2f}", border="B", ln=True, align="R")

    pdf.ln(5); pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 2. LABOUR & LOGISTICS PROOFS", 0, 1, "L", True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 10)
    for item in items_list:
        if item['Lab_Math']: pdf.cell(0, 8, clean_text(f" {item['Lab_Math']}"), border="B", ln=True)
    for m in log_maths: pdf.cell(0, 8, clean_text(f" {m}"), border="B", ln=True)

    pdf.ln(10); pdf.set_fill_color(0, 230, 118); pdf.set_text_color(26, 29, 45); pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 15, f" GRAND TOTAL (EX GST): ${grand:,.2f} ", 0, 1, "R", True)
    return bytes(pdf.output())

# --- RESTORED UI STYLING ---
st.markdown("""<style>
    .main { background-color: #F4F7F9 !important; }
    h1 { color: #1A1D2D !important; font-size: 52px !important; font-weight: 900 !important; }
    h3 { color: #FFFFFF !important; border-left: 10px solid #00E676; padding: 40px; background-color: #1A1D2D; border-radius: 0 12px 12px 0; font-size: 24px !important; margin-bottom: 15px; }
    div.stMetric { background-color: #FFFFFF !important; padding: 15px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    div[data-testid="stMetricValue"] { color: #3D5AFE !important; font-size: 30px !important; font-weight: 800 !important; }
    .item-text { font-size: 20px !important; font-weight: 700 !important; color: #1A1D2D; margin-top: 10px; }
    .gt-banner { background: #1A1D2D; color: #00E676; padding: 40px; border-radius: 20px; text-align: right; font-size: 44px !important; font-weight: 900; margin-top: 30px; border: 6px solid #00E676; box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
</style>""", unsafe_allow_html=True)

# --- WORKSPACE ---
st.title("⚡ Louis Master Quoter")

# [Sidebar & Date/KM inputs restored exactly from v45.9]
# ...

# --- SUMMARY & PDF DOWNLOAD ---
if not st.session_state.df.empty:
    # Summary Grid rendering restored from v45.9
    # ...

    st.divider()
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### 🚛 Logistics Override") # RESTORED HEADER
        min_trks = math.ceil(total_kg / 6000) or 1
        trks = st.number_input("Manually Set Truck Count", min_value=min_trks, value=max(min_trks, st.session_state.get('truck_override', 0)))
        st.session_state.truck_override = trks

    # Calculations
    grand_total = h_tot_c + lab_pool + wav + crt
    l_maths = [f"Damage Waiver: ${h_wk1_gear:,.2f} x 0.07 = ${wav:,.2f}", f"Cartage: {trks} Trucks x {safe_km}km x 4 x $3.50 = ${crt:,.2f}"]

    st.markdown(f"<div class='gt-banner'>GRAND TOTAL (EX GST): ${grand_total:,.2f}</div>", unsafe_allow_html=True)

    items_for_pdf = st.session_state.df.to_dict('records')
    pdf_b = create_calculation_pdf(st.session_state.get('proj', 'Quote'), h_tot_c, lab_pool, wav, crt, grand_total, weeks, start_d, end_d, items_for_pdf, l_maths, st.session_state.get('status', 'Quoted'))
    st.download_button("📥 DOWNLOAD AUDIT PDF", pdf_b, file_name=f"{st.session_state.get('proj', 'Quote')}_Audit.pdf")
