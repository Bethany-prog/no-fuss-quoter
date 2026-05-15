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
            # (Staff x Hrs x 55) x 2 (In/Out) x 2 (Profit)
            total_pool = (b["staff"] * b["hrs"] * rate) * 2 * 2
            per_seat = total_pool / seats
            desc = f"Grandstand Seating: ({b['staff']} staff x {b['hrs']}hrs x $55) x 2 x 2 = ${total_pool:,.2f}"
            return round(per_seat, 2), desc
    return 0, ""

# --- PDF ENGINE (RE-DESIGNED FOR TRANSPARENCY) ---
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
    
    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text("Louis Quoting Tool - Detailed Calculation Audit"), ln=True, align="C")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, clean_text(f"PROJECT: {name} | STATUS: {status.upper()}"), ln=True, align="C")
    pdf.cell(0, 7, f"PERIOD: {start.strftime('%d/%m/%Y')} to {end.strftime('%d/%m/%Y')} ({weeks} Week(s))", ln=True, align="C")
    pdf.ln(10)

    # 1. HIRE CALCULATIONS
    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 1. HIRE CALCULATIONS (Working Out)", 0, 1, "L", True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 10)
    
    for item in items_list:
        # Week 1 math
        w1_math = f"{item['Product']} (Wk 1): {item['Qty']:,.0f} x ${item['Base_Hire']:,.2f}"
        if item['Discount'] > 0:
            w1_math += f" [-{item['Discount']}% Disc]"
        w1_total = (item['Qty'] * item['Base_Hire']) * (1 - (item['Discount']/100))
        pdf.cell(140, 8, clean_text(w1_math), border="B")
        pdf.cell(50, 8, f"${w1_total:,.2f}", border="B", ln=True, align="R")
        
        # Recurring math
        if weeks > 1:
            r_rate = item['Base_Hire'] * 0.5 if item['Is_Marquee'] else item['Base_Hire']
            r_math = f"-> Recurring Hire: {item['Qty']:,.0f} x ${r_rate:,.2f} x {weeks-1} wks"
            r_total = (item['Qty'] * r_rate * (weeks-1)) * (1 - (item['Discount']/100))
            pdf.cell(140, 8, clean_text(r_math), border="B")
            pdf.cell(50, 8, f"${r_total:,.2f}", border="B", ln=True, align="R")

    pdf.set_font("Arial", "B", 10)
    pdf.cell(140, 10, "TOTAL HIRE COMPONENT:", align="R")
    pdf.cell(50, 10, f"${subtotal:,.2f}", ln=True, align="R")
    pdf.ln(5)

    # 2. LABOUR CALCULATIONS
    if any(item['Raw_Lab'] > 0 or item['Lab_Per_Unit'] > 0 for item in items_list):
        pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, " 2. LABOUR CALCULATIONS", 0, 1, "L", True)
        pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 10)
        
        for item in items_list:
            if item['Lab_Math']:
                pdf.cell(0, 8, clean_text(f" {item['Lab_Math']}"), border="B", ln=True)
        
        pdf.set_font("Arial", "B", 10)
        pdf.cell(140, 10, "TOTAL LABOUR POOL:", align="R")
        pdf.cell(50, 10, f"${labour:,.2f}", ln=True, align="R")
        pdf.ln(5)

    # 3. LOGISTICS
    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 3. LOGISTICS & FEES", 0, 1, "L", True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 10)
    for m in log_maths:
        pdf.cell(0, 8, clean_text(f" {m}"), border="B", ln=True)

    # Grand Total
    pdf.ln(10); pdf.set_fill_color(0, 230, 118); pdf.set_text_color(26, 29, 45)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 15, f" GRAND TOTAL (EX GST): ${grand:,.2f} ", 0, 1, "R", True)
    
    return bytes(pdf.output())

# --- MASTER DATA ---
CATALOG = {
    "Flooring": {
        "I-Trac®": {"rate": 23.40, "block": 46.80, "lab_fix": 4.65, "kg": 15.0},
        "Supa-Trac®": {"rate": 11.55, "block": 25.00, "lab_fix": 4.65, "kg": 4.5, "sheet_sqm": 3.13},
        "Plastorip": {"rate": 10.15, "block": 20.30, "lab_fix": 3.05, "kg": 4.0},
        "Trakmat": {"rate": 22.05, "block": 44.10, "lab_fix": 5.00, "kg": 35.0}
    },
    "Grandstands": {
        "Standard Seating": {"rate": 15.00, "block": 30.00, "kg": 25.0}
    }
}
STRUCT_LOGIC = {span: {"bay": (5 if span >= 10 else 3), "s_rate": 23.0, "m_rate": 18.20, "s_lab": 0.40} for span in [3, 4, 6, 9, 10, 12, 15, 20]}

# --- UI STYLING & SESSION ---
if 'df' not in st.session_state: 
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount", "Lab_Math", "Lab_Per_Unit", "Base_Hire"])
if 'status' not in st.session_state: st.session_state.status = "Quoted"
if 'proj' not in st.session_state: st.session_state.proj = "New Project"
if 'km' not in st.session_state: st.session_state.km = 0.0
if 'truck_override' not in st.session_state: st.session_state.truck_override = 0

st.markdown("""<style>
    .main { background-color: #F4F7F9 !important; }
    h1 { color: #1A1D2D !important; font-size: 52px !important; font-weight: 900 !important; }
    h3 { color: #FFFFFF !important; border-left: 10px solid #00E676; padding: 30px; background-color: #1A1D2D; border-radius: 0 12px 12px 0; font-size: 26px !important; }
    div.stMetric { background-color: #FFFFFF !important; padding: 15px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; }
    .gt-banner { background: #1A1D2D; color: #00E676; padding: 40px; border-radius: 20px; text-align: right; font-size: 44px !important; font-weight: 900; margin-top: 30px; border: 6px solid #00E676; }
</style>""", unsafe_allow_html=True)

# --- WORKSPACE ---
st.title("⚡ Louis Master Quoter")
# [Sidebar, Start/End, KM, and Addition Logic preserved from v45.9]
# ... (Code truncated for brevity, but logically complete in app)

# --- SUMMARY CALCULATIONS ---
if not st.session_state.df.empty:
    st.divider(); st.subheader("📝 QUOTE SUMMARY")
    h_tot_c, h_wk1_gear, total_kg = 0.0, 0.0, 0.0
    items_for_pdf = st.session_state.df.to_dict('records')
    
    for idx, row in st.session_state.df.iterrows():
        qty, brate, dm = row["Qty"], row["Unit Rate"], (1 - (row["Discount"]/100))
        total_kg += row["KG"]; h_wk1_gear += (qty * row["Base_Hire"])
        
        # Display logic for Summary (unchanged FOH)
        c0, c1, c2, c3, c4, c5 = st.columns([0.4, 4.0, 0.8, 1.2, 1.0, 1.4])
        # ... (Delete, Product Name, Qty, Rate, Discount, Total columns)
        
        wk1_val = (qty * brate + row["Raw_Lab"]) * dm
        h_tot_c += wk1_val
        
        if weeks > 1:
            r_rate = row["Base_Hire"] * 0.5 if row["Is_Marquee"] else row["Base_Hire"]
            h_tot_c += (qty * r_rate * (weeks-1)) * dm

    # Logistics
    min_trucks = math.ceil(total_kg / 6000) or 1
    trks = st.session_state.truck_override or min_trucks
    safe_km = st.session_state.km or 0
    
    wav = h_wk1_gear * 0.07 if st.session_state.get('waiver_mode') != "Free" else 0
    crt = trks * safe_km * 4 * 3.50 if st.session_state.get('cartage_mode') != "Free" else 0
    lab = max(st.session_state.df["Raw_Lab"].sum(), 350)

    # FINAL BANNER & PDF
    st.markdown(f"<div class='gt-banner'>GRAND TOTAL (EX GST): ${h_tot_c + lab + wav + crt:,.2f}</div>", unsafe_allow_html=True)
    
    log_maths = [
        f"Damage Waiver (7%): ${h_wk1_gear:,.2f} x 0.07 = ${wav:,.2f}",
        f"Cartage: {trks} Trucks x {safe_km}km x 4 trips x $3.50 = ${crt:,.2f}"
    ]
    
    pdf_b = create_calculation_pdf(st.session_state.proj, h_tot_c, lab, wav, crt, h_tot_c+lab+wav+crt, weeks, datetime.now(), datetime.now(), items_for_pdf, log_maths, st.session_state.status)
    st.download_button("📥 DOWNLOAD AUDIT PDF", pdf_b, file_name=f"{st.session_state.proj}_Audit.pdf")
