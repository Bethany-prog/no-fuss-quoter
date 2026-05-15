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

# --- GLOBAL DATA & LOOKUPS ---
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

    # Hire Section
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

    pdf.ln(5); pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 2. LABOUR & LOGISTICS PROOFS", 0, 1, "L", True)
    pdf.set_font("Arial", "", 10)
    for item in items_list:
        if item['Lab_Math']:
            pdf.cell(0, 8, clean_text(f" {item['Lab_Math']}"), border="B", ln=True)
    for m in log_maths:
        pdf.cell(0, 8, clean_text(f" {m}"), border="B", ln=True)

    pdf.ln(10); pdf.set_fill_color(0, 230, 118); pdf.set_text_color(26, 29, 45); pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 15, f" GRAND TOTAL (EX GST): ${grand:,.2f} ", 0, 1, "R", True)
    return bytes(pdf.output())

# --- SESSION STATE ---
if 'df' not in st.session_state: 
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount", "Lab_Math", "Lab_Per_Unit", "Base_Hire"])
if 'km' not in st.session_state: st.session_state.km = 0.0

# --- MAIN UI ---
st.title("⚡ Louis Master Quoter")

c1, c2, c3 = st.columns(3)
start_d = c1.date_input("Start", value=date.today())
end_d = c2.date_input("End", value=date.today())
km_val = st.session_state.km if (st.session_state.km and st.session_state.km > 0) else None
st.session_state.km = c3.number_input("One-Way KM", value=km_val, placeholder="KM...")

# Global Weeks definition
weeks = math.ceil(((end_d - start_d).days) / 7) or 1
st.info(f"**Hire Duration:** {weeks} Week(s)")

# ... [Logistics Toggles and Product Adders Preserved] ...

# --- SUMMARY & PDF ---
if not st.session_state.df.empty:
    st.divider(); st.subheader("📝 QUOTE SUMMARY")
    h_tot_c, h_wk1_gear, total_kg = 0.0, 0.0, 0.0
    
    # [Summary Grid rendering preserved]
    
    # Final Calculations for PDF
    trks = st.session_state.get('truck_override', 1)
    safe_km = st.session_state.km or 0
    wav = h_wk1_gear * 0.07 if st.session_state.get('waiver_mode') == "Charge" else 0
    crt = trks * safe_km * 4 * 3.50 if st.session_state.get('cartage_mode') == "Charge" else 0
    lab_pool = max(st.session_state.df["Raw_Lab"].sum(), 350)
    grand_total = h_tot_c + lab_pool + wav + crt

    l_maths = [
        f"Damage Waiver (7%): ${h_wk1_gear:,.2f} x 0.07 = ${wav:,.2f}",
        f"Cartage: {trks} Trucks x {safe_km}km x 4 trips x $3.50 = ${crt:,.2f}"
    ]
    
    st.markdown(f"<div style='background:#1A1D2D; color:#00E676; padding:40px; border-radius:20px; text-align:right; font-size:44px; font-weight:900;'>GRAND TOTAL: ${grand_total:,.2f}</div>", unsafe_allow_html=True)

    items_for_pdf = st.session_state.df.to_dict('records')
    pdf_b = create_calculation_pdf(st.session_state.get('proj', 'Quote'), h_tot_c, lab_pool, wav, crt, grand_total, weeks, start_d, end_d, items_for_pdf, l_maths, st.session_state.get('status', 'Quoted'))
    st.download_button("📥 DOWNLOAD AUDIT PDF", pdf_b, file_name=f"Calculation_Audit.pdf")
