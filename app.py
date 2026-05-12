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

def save_to_google(name, df, start, end, km):
    try:
        new_entry = pd.DataFrame([{
            "Quote_Name": name, "Data_JSON": df.to_json(orient='records'),
            "Start_Date": str(start), "End_Date": str(end), "KM": km, "Saved_Date": str(date.today())
        }])
        existing_data = conn.read(ttl=0)
        updated_data = pd.concat([existing_data, new_entry], ignore_index=True)
        conn.update(data=updated_data)
        st.cache_data.clear()
        return True
    except: return False

# --- PDF GENERATION (v27.0) ---
def create_calculation_pdf(name, df, subtotal, labour, waiver, cartage, grand_total, km, weeks):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "No Fuss Event Hire - Internal Calculation Sheet", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Generated on: {date.today()}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, f"Quote: {name}", ln=True)
    pdf.set_font("Arial", "", 11); pdf.cell(0, 8, f"Hire Duration: {weeks} Week(s) | Total Distance: {km} km", ln=True)
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
    
    # Hire Breakdown
    pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"BASE HIRE SUBTOTAL: ${subtotal:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        if not row['Is_Lab_Line']:
            p_name, qty, rate, total = row['Product'], row['Qty'], row['Unit Rate'], row['Total']
            pdf.cell(0, 6, f"{qty} - {p_name} x ${rate:,.2f} = ${total:,.2f}", ln=True)

    # Labour
    pdf.ln(4); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Labour: ${labour:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        if row['Is_Lab_Line']:
            pdf.cell(0, 6, f"{row['Qty']} - {row['Product']} = ${row['Total']:,.2f}", ln=True)

    # Waiver/Cartage
    pdf.ln(4); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Damage Waiver (7%): ${waiver:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(0, 6, f"${subtotal:,.2f} x 0.07", ln=True)
    pdf.ln(2); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Cartage Total: ${cartage:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(0, 6, f"{km} km x 4 trips x $3.50/km", ln=True)
    
    pdf.ln(10); pdf.set_font("Arial", "B", 14); pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, f"GRAND TOTAL (EX GST): ${grand_total:,.2f}", 1, 1, "R", True)
    return bytes(pdf.output())

# 3. MODULAR DATA
MARQUEE_SERIES = {
    3: {"name": "3M Series", "starter_hire": 350.0, "starter_lab": 150.0, "ext_hire": 180.0, "ext_lab": 80.0, "bay_len": 3, "w_per_bay": 8},
    10: {"name": "10M Series", "starter_hire": 1250.0, "starter_lab": 550.0, "ext_hire": 750.0, "ext_lab": 350.0, "bay_len": 5, "w_per_bay": 12}
}

# 4. APP UI
st.set_page_config(page_title="No Fuss Quote Pro v27.0", layout="wide")
st.markdown("<style>.main { background-color: #FFFFFF !important; } h3 { color: #FFFFFF !important; border-left: 5px solid #00E676; padding: 10px 15px; background-color: #1A1D2D; border-radius: 0 10px 10px 0; margin-top: 20px; } div.stMetric { background-color: #1A1D2D !important; padding: 20px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; } div[data-testid='stMetricValue'] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; } [data-testid='stMetricLabel'] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 16px !important; } div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; width: 100%; }</style>", unsafe_allow_html=True)

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Block_Rate", "No_Waiver", "Unit_Type", "Is_Lab_Line"])

st.title("📦 No Fuss Quote Pro")

# LOGISTICS
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today())
end_date = c2.date_input("Hire End", value=date.today())
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=0.0)
live_weeks = math.ceil(((end_date - start_date).days) / 7) if (end_date - start_date).days > 0 else 1

# SMART QUICK-ADD
st.markdown("### ⚡ QUICK-ADD MARQUEE")
q_input = st.text_input("Type Size (e.g., 3x9, 6x3, 10x20)", placeholder="Width x Length...")
q_sec = st.radio("Securing", ["Weights", "Pegging"], horizontal=True)

if st.button("ADD TO QUOTE"):
    try:
        # Parse 3x9 or 10x20
        match = re.search(r'(\d+)\s*[xX]\s*(\d+)', q_input)
        if match:
            w, l = int(match.group(1)), int(match.group(2))
            # Determine Series (If user types 6x3, width is 3)
            series_w = w if w in [3, 10] else (l if l in [3, 10] else 3)
            data = MARQUEE_SERIES[series_w]
            total_len = l if series_w == w else w
            bays = math.ceil(total_len / data['bay_len'])
            ext_bays = bays - 1
            
            # Build rows
            new_rows = []
            # Starter
            new_rows.append({"Qty": 1, "Product": f"Starter Bay ({series_w}m Series)", "Unit Rate": data['starter_hire'], "Total": 0.0, "Block_Rate": data['starter_hire'], "No_Waiver": False, "Unit_Type": "ea", "Is_Lab_Line": False, "Disc %": 0.0})
            new_rows.append({"Qty": 1, "Product": f"Labour: Starter Bay ({series_w}m)", "Unit Rate": data['starter_lab'], "Total": 0.0, "Block_Rate": data['starter_lab'], "No_Waiver": True, "Unit_Type": "ea", "Is_Lab_Line": True, "Disc %": 0.0})
            # Extensions
            if ext_bays > 0:
                new_rows.append({"Qty": ext_bays, "Product": f"Extension Bay ({series_w}m Series)", "Unit Rate": data['ext_hire'], "Total": 0.0, "Block_Rate": data['ext_hire'], "No_Waiver": False, "Unit_Type": "ea", "Is_Lab_Line": False, "Disc %": 0.0})
                new_rows.append({"Qty": ext_bays, "Product": f"Labour: Extension Bay ({series_w}m)", "Unit Rate": data['ext_lab'], "Total": 0.0, "Block_Rate": data['ext_lab'], "No_Waiver": True, "Unit_Type": "ea", "Is_Lab_Line": True, "Disc %": 0.0})
            # Weights
            if q_sec == "Weights":
                w_qty = bays * data['w_per_bay']
                new_rows.append({"Qty": w_qty, "Product": f"Orange Weights ({series_w}m Series)", "Unit Rate": 6.60, "Total": 0.0, "Block_Rate": 6.60, "No_Waiver": False, "Unit_Type": "ea", "Is_Lab_Line": False, "Disc %": 0.0})
            
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True)
            st.success(f"Added {series_w}x{total_len} Marquee ({bays} Bays)")
        else: st.error("Please use format Width x Length (e.g. 3x9)")
    except: st.error("Size not recognized. Use 3m or 10m widths.")

# QUOTE TABLE
if not st.session_state.df.empty:
    st.markdown("### 🏗️ QUOTED ITEMS")
    edited_df = st.data_editor(st.session_state.df[["Qty", "Unit_Type", "Product", "Unit Rate", "Total"]], use_container_width=True)
    
    # CALCS
    h_tot, lab_tot, w_tot = 0.0, 0.0, 0.0
    for idx, row in st.session_state.df.iterrows():
        q, r, is_lab = row["Qty"], row["Unit Rate"], row["Is_Lab_Line"]
        line_val = q * r * (live_weeks if not is_lab else 1)
        if is_lab: lab_tot += line_val
        else:
            h_tot += line_val
            if not row["No_Waiver"]: w_tot += line_val * 0.07
        st.session_state.df.at[idx, "Total"] = line_val

    # SUMMARY
    c_val = km_input * 4 * 3.50
    st.divider(); m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE", f"${h_tot:,.2f}"); m2.metric("LABOUR", f"${lab_tot:,.2f}"); m3.metric("WAIVER", f"${w_tot:,.2f}"); m4.metric("CARTAGE", f"${c_val:,.2f}")
    
    fn = st.text_input("Project Name:")
    pdf_bytes = create_calculation_pdf(fn, st.session_state.df, h_tot, lab_tot, w_tot, c_val, h_tot+lab_tot+w_tot+c_val, km_input, live_weeks)
    st.download_button("📥 DOWNLOAD PDF", pdf_bytes, file_name=f"{fn}_Calculations.pdf")
    if st.button("⚠️ RESET"): st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.rerun()
