import streamlit as st
import math
from datetime import datetime

# PAGE CONFIG
st.set_page_config(page_title="No Fuss Quote Pro", page_icon="📦", layout="centered")

# STYLING
st.markdown("""
    <style>
    .main { background-color: #0F111A; }
    div.stButton > button:first-child {
        background-color: #3D5AFE; color: white; border-radius: 10px; width: 100%;
    }
    .stMetric { background-color: #1A1D2D; padding: 15px; border-radius: 10px; border: 1px solid #30364D; }
    </style>
    """, unsafe_allow_html=True)

# FULL CATALOG FROM OCT 2025 LIST
PRODUCT_CATALOG = {
    "I-Trac (sqm)": {"rate": 23.40, "labour": 4.65},
    "Ramp for I-Trac (ea)": {"rate": 42.00, "labour": 0.00},
    "Supa-Trac (sqm)": {"rate": 11.55, "labour": 4.65},
    "Supa-Trac Edging (lm)": {"rate": 6.70, "labour": 0.00},
    "Trakmats (ea)": {"rate": 23.20, "labour": 5.85},
    "Trakmat Joiners 4 hole (ea)": {"rate": 11.95, "labour": 0.00},
    "Trakmat Joiners 2 hole (ea)": {"rate": 4.40, "labour": 0.00},
    "LD 20 Roll (3m x 20m)": {"rate": 1800.00, "labour": 0.00},
    "No Fuss Floor - Grey/Green (sqm)": {"rate": 7.10, "labour": 3.05},
    "No Fuss Floor Ramp 1m (ea)": {"rate": 6.60, "labour": 0.00},
    "No Fuss Expansion Joiner 1.2m (ea)": {"rate": 6.60, "labour": 0.00},
    "Plastorip (sqm)": {"rate": 10.15, "labour": 3.05},
    "Plastorip Edging (lm)": {"rate": 1.65, "labour": 0.00},
    "Plastorip Expansion Joiner 1m (ea)": {"rate": 12.15, "labour": 0.00},
    "Terratrak Plus (sqm)": {"rate": 23.40, "labour": 4.65},
    "Enkamat Underlay (sqm)": {"rate": 2.60, "labour": 0.00},
    "Geotextile Underlay (sqm)": {"rate": 2.60, "labour": 0.00},
    "Black Plastic (sqm)": {"rate": 0.90, "labour": 0.00},
    "Wooden Floor (sqm)": {"rate": 8.85, "labour": 7.15},
    "Parquetry Dance Floor (sqm)": {"rate": 20.95, "labour": 4.80},
    "Carpet Tiles - Onyx (sqm)": {"rate": 8.85, "labour": 3.05},
    "Protectall (sqm)": {"rate": 22.05, "labour": 3.25},
}

st.title("📦 No Fuss Quote Pro")
st.subheader("Internal Calculation Engine")

# SESSION STATE FOR TABLE
if 'items' not in st.session_state:
    st.session_state.items = []

# --- LOGISTICS SECTION ---
with st.expander("📍 LOGISTICS & DATES", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Hire Start")
    with col2:
        end_date = st.date_input("Hire End")
    
    km_input = st.number_input("One-Way KM to Job", min_value=0.0, step=1.0)

# --- ITEM ADDITION ---
with st.container():
    st.markdown("### ➕ Add Line Item")
    item_choice = st.selectbox("Select Product", sorted(PRODUCT_CATALOG.keys()))
    qty = st.number_input("Quantity", min_value=0.0, step=1.0)
    
    if st.button("Add to Quote"):
        if qty > 0:
            days = (end_date - start_date).days
            weeks = math.ceil(days / 7) if days > 0 else 1
            
            hire_val = qty * PRODUCT_CATALOG[item_choice]["rate"] * weeks
            lab_val = qty * PRODUCT_CATALOG[item_choice]["labour"]
            
            st.session_state.items.append({
                "Item": item_choice,
                "Qty": qty,
                "Weeks": weeks,
                "Hire": hire_val,
                "Labour": lab_val
            })
            st.toast(f"Added {item_choice}")

# --- QUOTE TABLE ---
if st.session_state.items:
    st.markdown("### 📋 Quote Summary")
    st.table(st.session_state.items)
    
    if st.button("Reset Quote"):
        st.session_state.items = []
        st.rerun()

# --- FINAL CALCULATIONS ---
raw_hire = sum(i["Hire"] for i in st.session_state.items)
# $300 Minimum Rule
hire_final = max(300.0, raw_hire) if st.session_state.items else 0.0
waiver = hire_final * 0.07
labour_total = sum(i["Labour"] for i in st.session_state.items)
cartage_total = km_input * 4 * 3.50

st.divider()

# MOBILE FRIENDLY DISPLAY
st.markdown("### 💰 Totals (Ex GST)")
c1, c2 = st.columns(2)
with c1:
    st.metric("Hire (Min Applied)" if hire_final > raw_hire else "Hire Total", f"${hire_final:,.2f}")
    st.metric("Labour", f"${labour_total:,.2f}")
with c2:
    st.metric("Damage Waiver", f"${waiver:,.2f}")
    st.metric("Cartage", f"${cartage_total:,.2f}")

grand_total = hire_final + waiver + labour_total + cartage_total
st.metric("GRAND TOTAL", f"${grand_total:,.2f}")

# CLIPBOARD HELPER
copy_text = f"Hire: {hire_final:.2f}\nWaiver: {waiver:.2f}\nLabour: {labour_total:.2f}\nCartage: {cartage_total:.2f}"
st.text_area("Copy this to your system:", copy_text)
