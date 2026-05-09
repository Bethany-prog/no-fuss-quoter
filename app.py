import streamlit as st
import math
from datetime import date

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
            else:
                st.error("❌ Incorrect Code")
        return False
    return True

if not check_password():
    st.stop()

# 2. PAGE CONFIG & STYLING
st.set_page_config(page_title="No Fuss Quote Pro", page_icon="📦", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0F111A; }
    [data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; font-size: 16px !important; font-weight: bold !important; }
    div.stMetric { background-color: #1A1D2D; padding: 20px; border-radius: 12px; border: 2px solid #30364D; }
    label { color: white !important; font-weight: bold !important; }
    div.stButton > button:first-child {
        background-color: #3D5AFE; color: white; border-radius: 10px; width: 100%; height: 50px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. PRODUCT DATA
PRODUCT_CATALOG = {
    "I-Trac (sqm)": {"rate": 23.40, "labour": 4.65},
    "Supa-Trac (sqm)": {"rate": 11.55, "labour": 4.65},
    "No Fuss Floor - Grey/Green (sqm)": {"rate": 7.10, "labour": 3.05},
    "Terratrak Plus (sqm)": {"rate": 23.40, "labour": 4.65},
    "Wooden Floor (sqm)": {"rate": 8.85, "labour": 7.15},
    "Parquetry Dance Floor (sqm)": {"rate": 20.95, "labour": 4.80},
    "Protectall (sqm)": {"rate": 22.05, "labour": 3.25},
}

if 'quote_items' not in st.session_state:
    st.session_state.quote_items = []

st.title("📦 No Fuss Quote Pro")

# --- LOGISTICS & DATES ---
with st.expander("📍 LOGISTICS & DATES", expanded=True):
    c1, c2 = st.columns(2)
    # Date Selector set to DD/MM/YYYY format
    start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
    end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
    
    # Labeled KM Field
    km_input = st.number_input("One-Way Distance (KM) to Job", min_value=0.0, value=0.0, step=1.0)
    
    # Labour and Cartage Toggles
    col_lab, col_cart = st.columns(2)
    charge_labour = col_lab.checkbox("Charge Labour?", value=True)
    charge_cartage = col_cart.checkbox("Charge Cartage?", value=True)

# --- ADD ITEM ---
st.markdown("### ➕ Add Line Item")
item_choice = st.selectbox("Select Product", sorted(PRODUCT_CATALOG.keys()))
qty = st.number_input("Quantity (sqm)", min_value=0.0, value=0.0)

if st.button("ADD TO QUOTE"):
    if qty > 0:
        days = (end_date - start_date).days
        weeks = math.ceil(days / 7) if days > 0 else 1
        
        base_rate = PRODUCT_CATALOG[item_choice]["rate"]
        
        # Hire Breakdown
        first_week_hire = qty * base_rate
        extra_weeks_hire = qty * base_rate * (weeks - 1)
        total_item_hire = first_week_hire + extra_weeks_hire
        
        # SYSTEM ENTRY RATE: (Total Hire Cost) / (SQM)
        # This matches your example: 150sqm I-trac for 3 weeks = $10,530 / 150 = $70.20
        entry_rate = total_item_hire / qty
        
        st.session_state.quote_items.append({
            "Item": item_choice,
            "Qty": qty,
            "Weeks": weeks,
            "FirstWeek": first_week_hire,
            "ExtraWeeks": extra_weeks_hire,
            "TotalHire": total_item_hire,
            "SystemRate": entry_rate,
            "LabourCost": qty * PRODUCT_CATALOG[item_choice]["labour"] if charge_labour else 0.0
        })
        st.rerun()

# --- SUMMARY TABLE ---
if st.session_state.quote_items:
    st.markdown("### 📋 Quote Summary")
    display_data = []
    for i in st.session_state.quote_items:
        display_data.append({
            "Product": i["Item"],
            "Qty": f"{i['Qty']:,}",
            "Weeks": i["Weeks"],
            "Entry Rate ($)": f"{i['SystemRate']:.2f}",
            "Total ($)": f"{i['TotalHire']:,.2f}"
        })
    st.table(display_data)
    
    if st.button("🗑️ Reset Quote"):
        st.session_state.quote_items = []
        st.rerun()

# --- CALCULATIONS ---
raw_hire = sum(i["TotalHire"] for i in st.session_state.quote_items)
hire_final = max(300.0, raw_hire) if st.session_state.quote_items else 0.0
waiver = hire_final * 0.07
labour_final = sum(i["LabourCost"] for i in st.session_state.quote_items) if charge_labour else 0.0
cartage_final = (km_input * 4 * 3.50) if charge_cartage else 0.0

st.divider()
st.markdown("### 💰 Totals (Ex GST)")
c_left, c_right = st.columns(2)

# Specific Requested Layout for Hire
c_left.write(f"**First week of hire:** ${sum(i['FirstWeek'] for i in st.session_state.quote_items):,.2f}")
c_left.write(f"**Per additional week:** ${sum(i['ExtraWeeks'] for i in st.session_state.quote_items):,.2f}")

c_left.metric("TOTAL HIRE", f"${hire_final:,.2f}")
c_left.metric("LABOUR", f"${labour_final:,.2f}")
c_right.metric("WAIVER (7%)", f"${waiver:,.2f}")
c_right.metric("CARTAGE", f"${cartage_final:,.2f}")

grand_total = hire_final + waiver + labour_final + cartage_final
st.metric("GRAND TOTAL", f"${grand_total:,.2f}")

# --- DATA ENTRY HELPER ---
if st.session_state.quote_items:
    st.markdown("### 🖥️ Entry Helper (Total Period)")
    for i in st.session_state.quote_items:
        st.success(f"**{i['Item']}** | QTY: **{i['Qty']}** | Rate: **${i['SystemRate']:.2f}**")
