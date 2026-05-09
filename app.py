import streamlit as st
import math
from datetime import date

# 1. PASSWORD PROTECTION LOGIC
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.title("🔒 Private Quoting Access")
        st.write("9 Battery Crt Internal Calculation Engine")
        
        password = st.text_input("Access Code", type="password")
        if st.button("Unlock Engine"):
            if password == "NoFuss2026":  # You can change this password here
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Incorrect Code")
        return False
    return True

if not check_password():
    st.stop()

# 2. PAGE CONFIG
st.set_page_config(page_title="No Fuss Quote Pro", page_icon="📦", layout="centered")

# 3. STYLING
st.markdown("""
    <style>
    .main { background-color: #0F111A; }
    div.stButton > button:first-child {
        background-color: #3D5AFE; color: white; border-radius: 10px; width: 100%; height: 50px; font-weight: bold;
    }
    .stMetric { background-color: #1A1D2D; padding: 15px; border-radius: 10px; border: 1px solid #30364D; }
    </style>
    """, unsafe_allow_html=True)

# 4. PRODUCT DATA (OCT 2025)
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

# INITIALIZE STATE
if 'quote_items' not in st.session_state:
    st.session_state.quote_items = []

st.title("📦 No Fuss Quote Pro")

# --- LOGISTICS ---
with st.expander("📍 LOGISTICS & DATES", expanded=True):
    c1, c2 = st.columns(2)
    start_date = c1.date_input("Hire Start", value=date.today())
    end_date = c2.date_input("Hire End", value=date.today())
    km_input = st.number_input("One-Way KM to Job", min_value=0.0, value=0.0, step=1.0)

# --- ADD ITEM ---
st.markdown("### ➕ Add Line Item")
item_choice = st.selectbox("Select Product", sorted(PRODUCT_CATALOG.keys()))
qty = st.number_input("Quantity", min_value=0.0, value=0.0, step=1.0)
disc = st.number_input("Discount %", min_value=0.0, max_value=100.0, value=0.0)

if st.button("ADD TO QUOTE"):
    if qty > 0:
        delta = end_date - start_date
        weeks = math.ceil(delta.days / 7) if delta.days > 0 else 1
        
        base_hire = qty * PRODUCT_CATALOG[item_choice]["rate"] * weeks
        final_hire = base_hire * (1 - (disc / 100))
        labour = qty * PRODUCT_CATALOG[item_choice]["labour"]
        
        st.session_state.quote_items.append({
            "Item": item_choice, "Qty": qty, "Weeks": weeks,
            "Disc": f"{disc}%", "Hire": final_hire, "Labour": labour
        })
        st.rerun()

# --- TABLE ---
if st.session_state.quote_items:
    st.table(st.session_state.quote_items)
    if st.button("🗑️ Reset Quote"):
        st.session_state.quote_items = []
        st.rerun()

# --- FINAL CALCULATIONS ---
raw_hire = sum(float(i["Hire"]) for i in st.session_state.quote_items)
hire_final = max(300.0, raw_hire) if st.session_state.quote_items else 0.0 # $300 Min Fee
waiver = hire_final * 0.07 # 7% Waiver
labour_final = sum(float(i["Labour"]) for i in st.session_state.quote_items)
cartage_final = km_input * 4 * 3.50 # Cartage Calculation

st.divider()
st.markdown("### 💰 Totals (Ex GST)")
col_a, col_b = st.columns(2)
col_a.metric("Hire Total", f"${hire_final:,.2f}", delta="Min Applied" if hire_final > raw_hire else None)
col_a.metric("Labour", f"${labour_final:,.2f}")
col_b.metric("Waiver (7%)", f"${waiver:,.2f}")
col_b.metric("Cartage", f"${cartage_final:,.2f}")

grand_total = hire_final + waiver + labour_final + cartage_final
st.metric("GRAND TOTAL", f"${grand_total:,.2f}")

# CLIPBOARD BOX
st.markdown("---")
copy_str = f"Hire: {hire_final:.2f}\nWaiver: {waiver:.2f}\nLabour: {labour_final:.2f}\nCartage: {cartage_final:.2f}"
st.text_area("Tap & Hold to Copy for System:", value=copy_str, height=100)
