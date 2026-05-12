import streamlit as st
from streamlit_gsheets import GSheetsConnection
import math
import pandas as pd
from datetime import date
from fpdf import FPDF
import io

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

# --- PDF GENERATION (v26.3 - TABLE + RAW BREAKDOWN) ---
def create_calculation_pdf(name, df, subtotal, labour, waiver, cartage, grand_total, km, weeks):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "No Fuss Event Hire - Internal Calculation Sheet", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Generated on: {date.today()}", ln=True, align="C")
    pdf.ln(5)
    
    # Project Info
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Quote: {name}", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Hire Duration: {weeks} Week(s) | Total Distance: {km} km", ln=True)
    pdf.ln(5)

    # --- PART 1: THE TABLE (Like image on the right) ---
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
    
    pdf.ln(10)

    # --- PART 2: THE FINANCIAL BREAKDOWN (The Math) ---
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, "Financial Breakdown", ln=True)
    
    # 1. BASE HIRE SUBTOTAL
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"BASE HIRE SUBTOTAL: ${subtotal:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        if not row['Is_Lab_Line']:
            if "Marquee" in row['Product']:
                try:
                    parts = row['Product'].replace("Marquee ", "").upper().split("X")
                    sqm = int(parts[0].strip()) * int(parts[1].strip())
                    pdf.cell(0, 6, f"{row['Product']} - {sqm}sqm x 23 = {row['Total']:,.2f}", ln=True)
                except: pdf.cell(0, 6, f"{row['Product']} x {row['Unit Rate']} = {row['Total']:,.2f}", ln=True)
            elif "Weight" in row['Product']:
                pdf.cell(0, 6, f"Weights - {row['Qty']}EA x {row['Unit Rate']} = {row['Total']:,.2f}", ln=True)
            else:
                pdf.cell(0, 6, f"{row['Product']} - {row['Qty']} x {row['Unit Rate']} = {row['Total']:,.2f}", ln=True)

    # 2. LABOUR
    pdf.ln(4); pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"Labour: ${labour:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        if row['Is_Lab_Line']:
            clean_name = row['Product'].replace("Labour (", "").replace(")", "")
            pdf.cell(0, 6, f"{clean_name} x 55% = ${row['Total']:,.2f}", ln=True)

    # 3. WAIVER & CARTAGE
    pdf.ln(4); pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"Damage Waiver (7%): ${waiver:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(0, 6, f"${subtotal:,.2f} x 0.07", ln=True)
    
    pdf.ln(2); pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"Cartage Total: ${cartage:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(0, 6, f"{km} km x 4 trips x $3.50/km", ln=True)
    
    pdf.ln(10); pdf.set_font("Arial", "B", 14); pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, f"GRAND TOTAL (EX GST): ${grand_total:,.2f}", 1, 1, "R", True)
    
    return bytes(pdf.output())

# 3. APP UI & LOGIC
st.set_page_config(page_title="No Fuss Quote Pro", page_icon="📦", layout="wide")
st.markdown("<style>.main { background-color: #FFFFFF !important; } h3 { color: #FFFFFF !important; border-left: 5px solid #00E676; padding: 10px 15px; background-color: #1A1D2D; border-radius: 0 10px 10px 0; margin-top: 20px; } div.stMetric { background-color: #1A1D2D !important; padding: 20px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; } div[data-testid='stMetricValue'] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; } [data-testid='stMetricLabel'] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 16px !important; } div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; width: 100%; } .stDataFrame { border: 2px solid #00E676 !important; border-radius: 12px; }</style>", unsafe_allow_html=True)

CATALOG = {
    "MARQUEE": {
        "Structures": [
            {"Product": "Marquee 3 X 3", "w1_3": 207.00, "labour": 113.85, "weights_req": 24, "unit": "ea"},
            {"Product": "Marquee 4 X 3", "w1_3": 276.00, "labour": 151.80, "weights_req": 24, "unit": "ea"},
            {"Product": "Marquee 6 X 3", "w1_3": 414.00, "labour": 227.70, "weights_req": 32, "unit": "ea"},
            {"Product": "Marquee 9 X 3", "w1_3": 621.00, "labour": 341.55, "weights_req": 40, "unit": "ea"}
        ],
        "Accessories": [{"Product": "Orange Weight", "w1_3": 6.60, "labour": 0.00, "unit": "ea", "waiver": True}]
    },
    "FLOORING": {
        "I-Trac": [{"Product": "I-Trac flooring", "w1_3": 23.40, "block": 46.80, "labour": 4.65, "unit": "SQM", "waiver": True}],
        "Supa-Trac": [{"Product": "Supa-trac flooring", "w1_3": 11.55, "block": 25.00, "labour": 4.65, "unit": "SQM", "waiver": True}]
    }
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Block_Rate", "No_Waiver", "Unit_Type", "Is_Lab_Line"])

st.title("📦 No Fuss Quote Pro")

# LOGISTICS
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=None, placeholder="KM...")
live_weeks = math.ceil(((end_date - start_date).days) / 7) if (end_date - start_date).days > 0 else 1

# ADD PRODUCT
dept_choice = st.selectbox("Department", sorted(CATALOG.keys(), reverse=True))
bundle_choice = st.selectbox("Select Group", sorted(CATALOG[dept_choice].keys(), reverse=True))
selected_bundle = CATALOG[dept_choice][bundle_choice]

bundle_results = []
for item in selected_bundle:
    q_val = st.number_input(f"Qty: {item['Product']}", min_value=0.0, key=f"q_{item['Product']}")
    sec = None
    if q_val > 0 and dept_choice == "MARQUEE" and "weights_req" in item:
        sec = st.radio(f"Securing for {item['Product']}?", ["Weights", "Pegging"], horizontal=True, key=f"sec_{item['Product']}")
    if q_val > 0: bundle_results.append({"item": item, "qty": q_val, "secure": sec})

if st.button("ADD SELECTED ITEMS TO QUOTE"):
    new_rows = []
    for entry in bundle_results:
        it, q, secure = entry['item'], entry['qty'], entry['secure']
        new_rows.append({"Qty": q, "Product": it['Product'], "Unit Rate": it['w1_3'], "Disc %": 0.0, "Total": 0.0, "Block_Rate": it.get('block', it['w1_3']), "No_Waiver": False, "Unit_Type": it.get('unit','ea'), "Is_Lab_Line": False})
        if it.get('labour', 0) > 0:
            new_rows.append({"Qty": q, "Product": f"Labour ({it['Product']})", "Unit Rate": it['labour'], "Disc %": 0.0, "Total": 0.0, "Block_Rate": it['labour'], "No_Waiver": True, "Unit_Type": "ea", "Is_Lab_Line": True})
        if secure == "Weights":
            new_rows.append({"Qty": q * it['weights_req'], "Product": f"Orange Weight (For {it['Product']})", "Unit Rate": 6.60, "Disc %": 0.0, "Total": 0.0, "Block_Rate": 6.60, "No_Waiver": False, "Unit_Type": "ea", "Is_Lab_Line": False})
    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True); st.rerun()

# FINANCES
if not st.session_state.df.empty:
    display_df = st.session_state.df[["Qty", "Unit_Type", "Product", "Unit Rate", "Disc %", "Total"]]
    edited_df = st.data_editor(display_df, use_container_width=True, key="editor")
    
    if not edited_df.equals(display_df):
        for col in ["Qty", "Unit Rate", "Disc %"]: st.session_state.df[col] = edited_df[col]
        st.rerun()

    inc_cart, inc_waiv = st.checkbox("🚚 Include Cartage", value=True), st.checkbox("🛡️ Include Damage Waiver (7%)", value=True)
    
    h_tot, lab_tot, w_tot = 0.0, 0.0, 0.0
    for idx, row in st.session_state.df.iterrows():
        q, r, d, b, is_lab = row["Qty"], row["Unit Rate"], row["Disc %"], row["Block_Rate"], row["Is_Lab_Line"]
        current_unit_rate = (b / 4) if live_weeks >= 4 else r
        line_val = q * current_unit_rate * (live_weeks if not is_lab else 1) * (1 - (d/100))
        
        if is_lab: lab_tot += line_val
        else:
            if inc_waiv and not row["No_Waiver"]: w_tot += line_val * 0.07
            h_tot += line_val
        st.session_state.df.at[idx, "Total"] = line_val

    c_val = (km_input * 14.0 if km_input and inc_cart else 0)
    st.divider(); m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE SUBTOTAL", f"${h_tot:,.2f}"); m2.metric("LABOUR TOTAL", f"${lab_tot:,.2f}"); m3.metric("WAIVER", f"${w_tot:,.2f}"); m4.metric("CARTAGE", f"${c_val:,.2f}")
    st.metric("GRAND TOTAL (EX GST)", f"${h_tot + lab_tot + w_tot + c_val:,.2f}")

    fn = st.text_input("Project Name:")
    pdf_bytes = create_calculation_pdf(fn if fn else "Internal", st.session_state.df, h_tot, lab_tot, w_tot, c_val, h_tot + lab_tot + w_tot + c_val, km_input if km_input else 0, live_weeks)
    st.download_button("📥 DOWNLOAD INTERNAL PDF", pdf_bytes, file_name=f"{fn if fn else 'Quote'}_Calculations.pdf", mime="application/pdf")
    if st.button("⚠️ RESET"): st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.rerun()
