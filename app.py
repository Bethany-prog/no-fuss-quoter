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

# --- PDF GENERATION (v24.8 - MARQUEE MATH) ---
def create_calculation_pdf(name, df, subtotal, labour, waiver, cartage, grand_total, km, weeks, lab_mode):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "No Fuss Event Hire - Internal Calculation Sheet", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Generated on: {date.today()}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Quote: {name}", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Hire Duration: {weeks} Week(s) | Total Distance: {km} km", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 10, " Product", 1, 0, "L", True); pdf.cell(25, 10, " Qty", 1, 0, "C", True)
    pdf.cell(35, 10, " Rate", 1, 0, "C", True); pdf.cell(40, 10, " Total", 1, 1, "R", True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    math_summary_parts = []
    for _, row in df.iterrows():
        pdf.cell(80, 8, f" {row['Product']}", 1)
        pdf.cell(25, 8, f" {row['Qty']} {row['Unit_Type']}", 1, 0, "C")
        pdf.cell(35, 8, f" ${row['Unit Rate']:,.2f}", 1, 0, "C")
        pdf.cell(40, 8, f" ${row['Total']:,.2f}", 1, 1, "R")
        math_summary_parts.append(f"{row['Qty']} x ${row['Unit Rate']:,.2f}")
    
    pdf.ln(10); pdf.set_font("Arial", "B", 13); pdf.cell(0, 10, "Financial Breakdown", ln=True)
    pdf.set_font("Arial", "B", 11); pdf.cell(100, 8, "Base Hire Subtotal:", 0); pdf.cell(0, 8, f"${subtotal:,.2f}", 0, 1, "R")
    pdf.set_font("Arial", "I", 9); pdf.set_text_color(100, 100, 100)
    sub_math = " + ".join(math_summary_parts)
    if weeks > 1: sub_math = f"({sub_math}) x {weeks} weeks"
    pdf.cell(0, 5, f"Calc: {sub_math}", ln=True)
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "B", 11)
    pdf.cell(100, 8, "Separate Labour Charges:", 0); pdf.cell(0, 8, f"${labour:,.2f}", 0, 1, "R")
    pdf.set_font("Arial", "I", 9); pdf.set_text_color(100, 100, 100)
    if lab_mode == "No Labour": pdf.cell(0, 5, "(Mode: No Labour selected)", ln=True)
    elif lab_mode == "Bake Labour into Unit Rate": pdf.cell(0, 5, "(Mode: Baked into rates / Marquee 55% Logic Applied)", ln=True)
    else: pdf.cell(0, 5, "(Mode: Separate Line Item)", ln=True)
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "B", 11)
    pdf.cell(100, 8, "Damage Waiver (7%):", 0); pdf.cell(0, 8, f"${waiver:,.2f}", 0, 1, "R")
    pdf.set_font("Arial", "I", 9); pdf.set_text_color(100, 100, 100); pdf.cell(0, 5, f"Calc: ${subtotal:,.2f} x 0.07", ln=True)
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "B", 11)
    pdf.cell(100, 8, "Cartage Total:", 0); pdf.cell(0, 8, f"${cartage:,.2f}", 0, 1, "R")
    pdf.set_font("Arial", "I", 9); pdf.set_text_color(100, 100, 100); pdf.cell(0, 5, f"Calc: {km} km x 4 trips x $3.50/km", ln=True)
    pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "B", 14); pdf.cell(100, 12, "GRAND TOTAL (EX GST):", "T"); pdf.cell(0, 12, f"${grand_total:,.2f}", "T", 1, "R")
    return bytes(pdf.output())

# 3. PAGE CONFIG
st.set_page_config(page_title="No Fuss Quote Pro", page_icon="📦", layout="wide")
st.markdown("<style>.main { background-color: #FFFFFF !important; } h3 { color: #FFFFFF !important; border-left: 5px solid #00E676; padding: 10px 15px; background-color: #1A1D2D; border-radius: 0 10px 10px 0; } div.stMetric { background-color: #1A1D2D !important; padding: 20px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; } div[data-testid='stMetricValue'] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; } [data-testid='stMetricLabel'] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 16px !important; } div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; width: 100%; } .stDataFrame { border: 2px solid #00E676 !important; border-radius: 12px; }</style>", unsafe_allow_html=True)

# 4. MASTER CATALOG (Flooring + NEW Marquee)
CATALOG = {
    "FLOORING": {
        "I-Trac System": [
            {"Product": "I-Trac flooring", "w1_3": 23.40, "block": 46.80, "labour": 4.65, "unit": "SQM", "waiver": True},
            {"Product": "I-Trac Ramp", "w1_3": 42.00, "block": 84.00, "labour": 0.00, "unit": "ea", "waiver": True}
        ],
        "Supa-Trac System": [
            {"Product": "Supa-trac flooring", "w1_3": 11.55, "block": 25.00, "labour": 4.65, "unit": "SQM", "waiver": True, "is_st": True},
            {"Product": "Supa-trac Edging", "w1_3": 6.70, "block": 6.70, "labour": 0.00, "unit": "lm", "waiver": False}
        ],
        "Trakmat System": [
            {"Product": "Trakmats", "w1_3": 23.20, "block": 45.00, "labour": 5.85, "unit": "ea", "waiver": True},
            {"Product": "Trakmat Joiners 4 Hole", "w1_3": 11.95, "block": 11.95, "labour": 0.00, "unit": "ea", "waiver": True}
        ]
    },
    "MARQUEE": {
        "Structures": [
            {"Product": "Marquee 3 X 3 (9 SQM)", "w1_3": 207.00, "block": 207.00, "labour": 113.85, "unit": "ea", "waiver": True},
            {"Product": "Marquee 4 X 3 (12 SQM)", "w1_3": 276.00, "block": 276.00, "labour": 151.80, "unit": "ea", "waiver": True},
            {"Product": "Marquee 6 X 3 (18 SQM)", "w1_3": 414.00, "block": 414.00, "labour": 227.70, "unit": "ea", "waiver": True},
            {"Product": "Marquee 9 X 3 (27 SQM)", "w1_3": 621.00, "block": 621.00, "labour": 341.55, "unit": "ea", "waiver": True},
            {"Product": "Marquee 10 X 5 (50 SQM)", "w1_3": 1150.00, "block": 1150.00, "labour": 632.50, "unit": "ea", "waiver": True},
            {"Product": "Marquee 12 X 5 (60 SQM)", "w1_3": 1380.00, "block": 1380.00, "labour": 759.00, "unit": "ea", "waiver": True},
            {"Product": "Marquee 15 X 5 (75 SQM)", "w1_3": 1725.00, "block": 1725.00, "labour": 948.75, "unit": "ea", "waiver": True}
        ],
        "Weights & Accessories": [
            {"Product": "Orange Weight", "w1_3": 6.60, "block": 6.60, "labour": 0.00, "unit": "ea", "waiver": True},
            {"Product": "Pegging", "w1_3": 0.00, "block": 0.00, "labour": 0.00, "unit": "ea", "waiver": False}
        ]
    }
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo", "Unit_Type", "Is_ST"])

st.title("📦 No Fuss Quote Pro")

# LOGISTICS
st.markdown("### 📍 HIRE DATES & DISTANCE")
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=None, placeholder="KM...")
live_weeks = math.ceil(((end_date - start_date).days) / 7) if (end_date - start_date).days > 0 else 1

# ADD PRODUCT
st.markdown("### ➕ ADD PRODUCT")
dept_col, bundle_col = st.columns(2)
dept_choice = dept_col.selectbox("Department", sorted(CATALOG.keys()))
bundle_choice = bundle_col.selectbox("Select Group", sorted(CATALOG[dept_choice].keys()))
selected_bundle = CATALOG[dept_choice][bundle_choice]
bundle_results = []
for item in selected_bundle:
    q_val = st.number_input(f"Qty: {item['Product']} ({item['unit']})", min_value=0.0, value=None, key=f"q_{item['Product']}")
    if q_val and q_val > 0: bundle_results.append({"item": item, "qty": q_val})

c_a, c_d = st.columns(2)
adj_rate, discount_pct = c_a.number_input("Override Price", min_value=0.0, value=None), c_d.number_input("Discount %", min_value=0.0, max_value=100.0, value=None)
if st.button("ADD SELECTED ITEMS TO QUOTE"):
    new_rows = []
    for entry in bundle_results:
        it, q = entry['item'], entry['qty']
        base_r = adj_rate if adj_rate and it == selected_bundle[0] else it['w1_3']
        new_rows.append({"Qty": q, "Product": it['Product'], "Unit Rate": base_r, "Disc %": discount_pct if discount_pct else 0.0, "Total": 0.0, "Labour_Rate": it['labour'], "Block_Rate": it['block'], "SYSTEM RATE": 0.0, "No_Waiver": not it['waiver'], "Is_GS": False, "Is_Mojo": False, "Unit_Type": it['unit'], "Is_ST": it.get('is_st', False)})
    if new_rows: st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True); st.rerun()

# FINANCES
if not st.session_state.df.empty:
    st.markdown("### 🏗️ QUOTED ITEMS")
    display_cols = ["Qty", "Unit_Type", "Product", "Unit Rate", "Disc %", "SYSTEM RATE", "Total"]
    edited_df = st.data_editor(st.session_state.df[display_cols], use_container_width=True, key="editor")
    if not edited_df.equals(st.session_state.df[display_cols]):
        for col in ["Qty", "Unit Rate", "Disc %"]: st.session_state.df[col] = edited_df[col]
        st.rerun()

    labour_mode = st.selectbox("Labour Mode", ["Bake Labour into Unit Rate", "Show Labour as Separate Line Item", "No Labour"])
    charge_cartage, include_damage_waiver = st.checkbox("🚚 Include Cartage", value=True), st.checkbox("🛡️ Include Damage Waiver (7%)", value=True)
    
    hire_total, lab_total, waiver_total = 0.0, 0.0, 0.0
    for idx, row in st.session_state.df.iterrows():
        q, r, d, b, lr = row["Qty"], row["Unit Rate"], row["Disc %"], row["Block_Rate"], row["Labour_Rate"]
        hire_val = (q * (b / 4) * live_weeks) if live_weeks >= 4 else (q * r * live_weeks)
        hire_disc = hire_val * (1 - (d / 100))
        if include_damage_waiver and not row["No_Waiver"]: waiver_total += hire_disc * 0.07
        item_lab = q * lr if labour_mode == "Bake Labour into Unit Rate" else 0.0
        if labour_mode == "Show Labour as Separate Line Item": lab_total += (q * lr) * (1 - (d / 100))
        total_line = hire_disc + (item_lab * (1 - (d / 100)))
        st.session_state.df.at[idx, "Total"], st.session_state.df.at[idx, "SYSTEM RATE"] = total_line, (total_line / q if q > 0 else 0)
        hire_total += total_line

    cart_val = (km_input * 14.0 if km_input and charge_cartage else 0)
    final_grand = hire_total + lab_total + waiver_total + cart_val

    st.divider(); m1, m2, m3, m4 = st.columns(4)
    m1.metric("SUBTOTAL", f"${hire_total:,.2f}"); m2.metric("LABOUR", f"${lab_total:,.2f}"); m3.metric("WAIVER", f"${waiver_total:,.2f}"); m4.metric("CARTAGE", f"${cart_val:,.2f}")
    st.metric("GRAND TOTAL (EX GST)", f"${final_grand:,.2f}")

    # --- SAVE & EXPORT ---
    st.markdown("### 💾 FINISH & EXPORT")
    save_col1, save_col2, save_col3 = st.columns([2, 1, 1])
    fn = save_col1.text_input("Quote Name:", placeholder="Client Name")
    if save_col2.button("CLOUD ARCHIVE") and fn:
        save_to_google(fn, st.session_state.df, start_date, end_date, km_input)
        st.success("Archived!")
            
    pdf_bytes = create_calculation_pdf(fn if fn else "Internal_Quote", st.session_state.df, hire_total, lab_total, waiver_total, cart_val, final_grand, km_input if km_input else 0, live_weeks, labour_mode)
    save_col3.download_button(label="📥 DOWNLOAD INTERNAL PDF", data=pdf_bytes, file_name=f"{fn if fn else 'Quote'}_Calculations.pdf", mime="application/pdf")
    if st.button("⚠️ RESET ALL"): st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo", "Unit_Type", "Is_ST"]); st.rerun()
