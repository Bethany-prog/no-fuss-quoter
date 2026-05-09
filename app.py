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

# 2. PAGE CONFIG & HIGH CONTRAST STYLING
st.set_page_config(page_title="No Fuss Quote Pro", page_icon="📦", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0F111A; }
    /* Fix for dark-on-dark text in metrics */
    [data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; font-size: 16px !important; font-weight: bold !important; }
    div.stMetric { background-color: #1A1D2D; padding: 20px; border-radius: 12px; border: 2px solid #30364D; }
    
    /* Input styling */
    label { color: white !important; font-weight: bold !important; }
    div.stButton > button:first-child {
        background-color: #3D5AFE; color: white; border-radius: 10px; width: 100%; height: 50px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. PRODUCT DATA (OCT 2025) [cite: 1, 10]
# LD 20 Roll has specific tiered pricing from your PDF [cite: 10]
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

# --- LOGISTICS ---
with st.expander("📍 LOGISTICS & DATES", expanded=True):
    c1, c2 = st.columns(2)
    start_date = c1.date_input("Hire Start", value=date.today())
    end_date = c2.date_input("Hire End", value=date.today())
    km_input = st.number_input("One-Way KM to Job", min_value=0.0, value=0.0)

# --- ADD ITEM ---
st.markdown("### ➕ Add Line Item")
item_choice = st.selectbox("Select Product", sorted(PRODUCT_CATALOG.keys()))
qty = st.number_input("Quantity", min_value=0.0, value=0.0)

if st.button("ADD TO QUOTE"):
    if qty > 0:
        days = (end_date - start_date).days
        weeks = math.ceil(days / 7) if days > 0 else 1
        
        base_rate = PRODUCT_CATALOG[item_choice]["rate"]
        # Working out [cite: 11]
        first_week_cost = qty * base_rate
        additional_weeks_cost = qty * base_rate * (weeks - 1)
        total_hire = first_week_cost + additional_weeks_cost
        
        # Calculate the unit rate for your external system entry
        # Entry Rate = Total Hire / Weeks / Qty
        entry_rate = total_hire / weeks / qty
        
        st.session_state.quote_items.append({
            "Item": item_choice,
            "Qty": qty,
            "Weeks": weeks,
            "First Week": f"${first_week_cost:,.2f}",
            "Extra Weeks": f"${additional_weeks_cost:,.2f}",
            "Total Hire": total_hire,
            "System Entry Rate": entry_rate,
            "Labour": qty * PRODUCT_CATALOG[item_choice]["labour"]
        })
        st.rerun()

# --- TABLE ---
if st.session_state.quote_items:
    st.markdown("### 📋 Quote Breakdown")
    # Clean table for display
    display_items = []
    for i in st.session_state.quote_items:
        display_items.append({
            "Product": i["Item"],
            "Qty": i["Qty"],
            "Weeks": i["Weeks"],
            "Unit Rate (System)": f"${i['System Entry Rate']:,.4f}",
            "Total Hire": f"${i['Total Hire']:,.2f}"
        })
    st.table(display_items)
    
    if st.button("🗑️ Reset Quote"):
        st.session_state.quote_items = []
        st.rerun()

# --- TOTALS ---
raw_hire = sum(i["Total Hire"] for i in st.session_state.quote_items)
hire_final = max(300.0, raw_hire) if st.session_state.quote_items else 0.0 # Min Fee [cite: 1]
waiver = hire_final * 0.07 # 7% Waiver [cite: 1]
lab_final = sum(i["Labour"] for i in st.session_state.quote_items)
cart_final = km_input * 4 * 3.50

st.divider()
st.markdown("### 💰 Totals (Ex GST)")
col_a, col_b = st.columns(2)
col_a.metric("HIRE TOTAL", f"${hire_final:,.2f}")
col_a.metric("LABOUR TOTAL", f"${lab_final:,.2f}")
col_b.metric("DAMAGE WAIVER", f"${waiver:,.2f}")
col_b.metric("CARTAGE", f"${cart_final:,.2f}")

st.divider()
grand_total = hire_final + waiver + lab_final + cart_final
st.metric("GRAND TOTAL", f"${grand_total:,.2f}")

# --- SYSTEM ENTRY HELPER ---
st.markdown("### 🖥️ DATA ENTRY HELPER")
for i in st.session_state.quote_items:
    st.info(f"**{i['Item']}**\n\n- QTY: {i['Qty']}\n- Rate to enter: **${i['System Entry Rate']:.4f}**\n- (Total period cost: ${i['Total Hire']:.2f})")
