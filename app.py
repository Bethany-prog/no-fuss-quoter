import streamlit as st
from streamlit_gsheets import GSheetsConnection
import math
import pandas as pd
from datetime import date
from fpdf import FPDF

# 1. SETUP & STYLE
st.set_page_config(page_title="No Fuss Quoter", layout="wide")
st.markdown("<style>.main { background-color: #FFFFFF; } h3 { color: #FFFFFF; background-color: #1A1D2D; padding: 10px; border-radius: 5px; border-left: 5px solid #00E676; } div.stMetric { background-color: #1A1D2D !important; border: 1px solid #3D5AFE !important; border-radius: 10px; } [data-testid='stMetricValue'] { color: #00E676 !important; } .stDataFrame { border: 1px solid #00E676 !important; }</style>", unsafe_allow_html=True)

# 2. MASTER DATA (Reduced to Essentials)
ITEMS = {
    "Marquee 3 X 3": {"rate": 207.00, "labour": 113.85, "weights": 24, "unit": "ea"},
    "Supa-trac flooring": {"rate": 11.55, "block": 25.00, "labour": 4.65, "unit": "SQM"},
    "I-Trac flooring": {"rate": 23.40, "block": 46.80, "labour": 4.65, "unit": "SQM"},
    "Trakmats": {"rate": 23.20, "block": 45.00, "labour": 5.85, "unit": "ea"},
    "Orange Weight": {"rate": 6.60, "labour": 0.00, "unit": "ea"},
    "LD20 Roll": {"rate": 1800.00, "block": 825.00, "labour": 0.00, "unit": "Roll"},
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Labour_Rate", "Total", "No_Waiver"])

# 3. CLEAN INTERFACE
st.title("📦 No Fuss Quoter")

col_log1, col_log2 = st.columns(2)
km = col_log1.number_input("Distance (KM)", min_value=0.0, value=0.0)
weeks = col_log2.number_input("Weeks", min_value=1, value=1)

st.markdown("### ➕ ADD TO QUOTE")
c1, c2 = st.columns([3, 1])
selection = c1.selectbox("Select Product", list(ITEMS.keys()))
qty = c2.number_input("Qty", min_value=0.0, step=1.0)

if st.button("ADD ITEM"):
    item_data = ITEMS[selection]
    # Add Main Item
    new_row = pd.DataFrame([{"Qty": qty, "Product": selection, "Unit Rate": item_data['rate'], "Labour_Rate": item_data['labour'], "Total": 0.0, "No_Waiver": False}])
    st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
    
    # Auto-Add Weights for Marquee
    if "Marquee" in selection and item_data.get('weights', 0) > 0:
        w_row = pd.DataFrame([{"Qty": qty * item_data['weights'], "Product": "Orange Weight (Auto)", "Unit Rate": 6.60, "Labour_Rate": 0.0, "Total": 0.0, "No_Waiver": False}])
        st.session_state.df = pd.concat([st.session_state.df, w_row], ignore_index=True)
    st.rerun()

# 4. CALCS & DISPLAY
if not st.session_state.df.empty:
    st.markdown("### 🏗️ CURRENT QUOTE")
    edited = st.data_editor(st.session_state.df[["Qty", "Product", "Unit Rate", "Total"]], use_container_width=True)
    
    # Simple Math
    h_tot = 0.0
    for idx, row in st.session_state.df.iterrows():
        line_hire = row['Qty'] * row['Unit Rate'] * weeks
        line_lab = row['Qty'] * row['Labour_Rate']
        total = line_hire + line_lab
        st.session_state.df.at[idx, 'Total'] = total
        h_tot += total

    waiver = h_tot * 0.07
    cartage = km * 4 * 3.50
    grand = h_tot + waiver + cartage

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("SUBTOTAL", f"${h_tot:,.2f}")
    m2.metric("WAIVER (7%)", f"${waiver:,.2f}")
    m3.metric("CARTAGE", f"${cartage:,.2f}")
    m4.metric("GRAND TOTAL", f"${grand:,.2f}")

    if st.button("⚠️ RESET QUOTE"):
        st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns)
        st.rerun()

# 5. PDF EXPORT (Hidden in Sidebar to keep main screen clean)
with st.sidebar:
    st.header("Export Options")
    name = st.text_input("Project Name")
    if st.button("Generate Internal PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Internal Calculation: {name}", ln=True)
        pdf.set_font("Arial", "", 10)
        for _, r in st.session_state.df.iterrows():
            pdf.cell(0, 7, f"{r['Product']}: {r['Qty']} x ${r['Unit Rate']} = ${r['Total']}", ln=True)
        pdf.ln(5)
        pdf.cell(0, 7, f"Waiver: ${waiver:,.2f}", ln=True)
        pdf.cell(0, 7, f"Cartage: ${cartage:,.2f}", ln=True)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"TOTAL: ${grand:,.2f}", ln=True)
        
        pdf_output = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Download PDF", pdf_output, "Quote.pdf", "application/pdf")
