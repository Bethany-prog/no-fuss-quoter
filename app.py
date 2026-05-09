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
    
    /* Make Input Labels Pop */
    label, .stCheckbox { color: #000000 !important; font-weight: 800 !important; font-size: 16px !important; }
    
    /* Metric Card Styling */
    [data-testid="stMetricValue"] { color: #00E676 !important; font-size: 28px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; font-size: 14px !important; font-weight: bold !important; }
    div.stMetric { background-color: #1A1D2D; padding: 15px; border-radius: 12px; border: 2px solid #3D5AFE; margin-bottom: 10px; }
    
    /* Button Styling */
    div.stButton > button:first-child {
        background-color: #3D5AFE; color: white; border-radius: 10px; width: 100%; height: 50px; font-weight: bold; border: none;
    }
    
    /* Expander / Card Styling */
    [data-testid="stExpander"] { border: 3px solid #3D5AFE; border-radius: 15px; background-color: #FFFFFF; padding: 10px; }
    
    /* Headers */
    h1, h2, h3, h4 { color: white !important; font-weight: bold !important; }
    
    .breakdown-box { background-color: #161925; padding: 20px; border-radius: 12px; border: 1px solid #444; margin-top: 20px; color: white; }
    .min-fee-note { color: #FFAB40; font-weight: bold; padding: 10px; border: 1px dashed #FFAB40; border-radius: 5px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. PRODUCT CATALOG
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

if 'quote_items' not in st.session_state:
    st.session_state.quote_items = []

st.title("📦 No Fuss Quote Pro")

# --- LOGISTICS & DATES ---
with st.expander("📍 1. LOGISTICS & DATES", expanded=True):
    c1, c2 = st.columns(2)
    start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
    end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
    km_input = st.number_input("One-Way Distance (KM) from 9 Battery Crt", min_value=0.0, value=0.0, step=1.0)
    col_lab, col_cart = st.columns(2)
    charge_labour = col_lab.checkbox("Charge Labour?", value=True)
    charge_cartage = col_cart.checkbox("Charge Cartage?", value=True)

# --- ADD ITEM ---
st.markdown("### ➕ 2. ADD PRODUCT")
item_choice = st.selectbox("Select Product", sorted(PRODUCT_CATALOG.keys()))
qty = st.number_input("Quantity (sqm/ea/lm)", min_value=0.0, value=0.0)

if st.button("ADD TO QUOTE"):
    if qty > 0:
        days = (end_date - start_date).days
        weeks = math.ceil(days / 7) if days > 0 else 1
        base_rate = PRODUCT_CATALOG[item_choice]["rate"]
        total_item_hire = (qty * base_rate) + (qty * base_rate * (weeks - 1))
        
        st.session_state.quote_items.append({
            "Item": item_choice,
            "Qty": qty,
            "Weeks": weeks,
            "Rate": base_rate,
            "TotalHire": total_item_hire,
            "LabourCost": qty * PRODUCT_CATALOG[item_choice]["labour"] if charge_labour else 0.0
        })
        st.rerun()

# --- ITEM MANAGEMENT ---
if st.session_state.quote_items:
    st.markdown("### 📋 CURRENT ITEMS")
    for idx, item in enumerate(st.session_state.quote_items):
        c_i, c_d = st.columns([4, 1])
        c_i.write(f"**{item['Item']}** ({item['Qty']} units) - ${item['TotalHire']:,.2f}")
        if c_d.button("🗑️", key=f"del_{idx}"):
            st.session_state.quote_items.pop(idx)
            st.rerun()

# --- CALCULATIONS ---
actual_hire = sum(i["TotalHire"] for i in st.session_state.quote_items)
min_hire_applied = False
min_fee_diff = 0.0

if 0 < actual_hire < 300.0:
    min_hire_applied = True
    min_fee_diff = 300.0 - actual_hire
    final_hire = 300.0
else:
    final_hire = actual_hire

waiver = final_hire * 0.07
labour_final = sum(i["LabourCost"] for i in st.session_state.quote_items) if charge_labour else 0.0
cartage_final = (km_input * 4 * 3.50) if charge_cartage else 0.0
grand_total = final_hire + waiver + labour_final + cartage_final

# --- TOTALS DISPLAY ---
st.divider()
st.markdown("### 💰 3. TOTALS (EX GST)")

if min_hire_applied:
    st.markdown(f'<div class="min-fee-note">⚠️ Minimum Hire Requirement: Adding ${min_fee_diff:,.2f} to meet $300.00 min.</div>', unsafe_allow_html=True)

r1c1, r1c2 = st.columns(2)
r1c1.metric("TOTAL HIRE", f"${final_hire:,.2f}")
r1c2.metric("WAIVER (7%)", f"${waiver:,.2f}")

r2c1, r2c2 = st.columns(2)
r2c1.metric("LABOUR", f"${labour_final:,.2f}")
r2c2.metric("CARTAGE", f"${cartage_final:,.2f}")

st.metric("GRAND TOTAL", f"${grand_total:,.2f}")

# --- UNIT RATE & CARTAGE BREAKDOWN ---
if st.session_state.quote_items or km_input > 0:
    st.markdown('<div class="breakdown-box">', unsafe_allow_html=True)
    
    if charge_cartage and km_input > 0:
        st.markdown("#### 🚚 CARTAGE CALCULATION")
        st.write(f"{km_input}km x 4 trips x $3.50 rate = **${cartage_final:,.2f}**")
        st.markdown("---")

    if st.session_state.quote_items:
        st.markdown("#### 📏 HIRE RATE BREAKDOWN")
        for i in st.session_state.quote_items:
            sys_rate = (i["TotalHire"] / i["Qty"])
            st.write(f"**{i['Item']}** (Weeks: {i['Weeks']})")
            st.write(f"- First week: ${i['Rate']:,.2f} | Extra weeks: ${(i['Rate']*(i['Weeks']-1)):,.2f}")
            st.success(f"**RATE TO ENTER: ${sys_rate:.2f}**")
            st.markdown("---")
            
    if st.button("RESET ALL"):
        st.session_state.quote_items = []
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
