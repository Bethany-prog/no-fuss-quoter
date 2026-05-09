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
    label, .stCheckbox { color: #000000 !important; font-weight: 800 !important; font-size: 16px !important; }
    [data-testid="stMetricValue"] { color: #00E676 !important; font-size: 28px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; font-size: 14px !important; font-weight: bold !important; }
    div.stMetric { background-color: #1A1D2D; padding: 15px; border-radius: 12px; border: 2px solid #3D5AFE; margin-bottom: 10px; }
    div.stButton > button:first-child {
        background-color: #3D5AFE; color: white; border-radius: 10px; width: 100%; height: 50px; font-weight: bold;
    }
    [data-testid="stExpander"] { border: 3px solid #3D5AFE; border-radius: 15px; background-color: #FFFFFF; padding: 10px; }
    h1, h2, h3, h4 { color: white !important; font-weight: bold !important; }
    .breakdown-box { background-color: #161925; padding: 20px; border-radius: 12px; border: 1px solid #444; margin-top: 20px; color: white; }
    .override-note { color: #FFD700; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. PRODUCT CATALOG
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
    start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
    end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
    km_input = st.number_input("One-Way Distance (KM) from 9 Battery Crt", min_value=0.0, value=0.0, step=1.0)
    col_lab, col_cart = st.columns(2)
    charge_labour = col_lab.checkbox("Charge Labour?", value=True)
    charge_cartage = col_cart.checkbox("Charge Cartage?", value=True)

# --- ADD PRODUCT ---
st.markdown("### ➕ ADD PRODUCT")
item_choice = st.selectbox("Select Product", sorted(PRODUCT_CATALOG.keys()))

col_qty, col_adj = st.columns(2)
qty = col_qty.number_input("Quantity (sqm/ea/lm)", min_value=0.0, value=0.0)
adj_rate = col_adj.number_input("Adjusted Price (Optional)", min_value=0.0, value=0.0, help="Leave at 0.00 to use standard catalog rate.")

if st.button("ADD TO QUOTE"):
    if qty > 0:
        days = (end_date - start_date).days
        weeks = math.ceil(days / 7) if days > 0 else 1
        
        catalog_rate = PRODUCT_CATALOG[item_choice]["rate"]
        labour_unit = PRODUCT_CATALOG[item_choice]["labour"]
        
        # Use adjusted rate if provided, otherwise use catalog
        applied_rate = adj_rate if adj_rate > 0 else catalog_rate
        
        initial_week_total = applied_rate + labour_unit
        total_item_hire = (qty * applied_rate) + (qty * applied_rate * (weeks - 1))
        
        st.session_state.quote_items.append({
            "Item": item_choice, 
            "Qty": qty, 
            "Weeks": weeks,
            "OrigRate": catalog_rate,
            "AppliedRate": applied_rate,
            "InitialRate": initial_week_total,
            "TotalHire": total_item_hire,
            "LabourCost": qty * labour_unit if charge_labour else 0.0,
            "IsOverridden": adj_rate > 0
        })
        st.rerun()

# --- ITEM LIST ---
if st.session_state.quote_items:
    st.markdown("### 📋 CURRENT ITEMS")
    for idx, item in enumerate(st.session_state.quote_items):
        ci, cd = st.columns([4, 1])
        override_txt = f" (Overridden from ${item['OrigRate']:.2f})" if item['IsOverridden'] else ""
        ci.write(f"**{item['Item']}** ({item['Qty']}) - Hire: ${item['TotalHire']:,.2f}{override_txt}")
        if cd.button("🗑️", key=f"del_{idx}"):
            st.session_state.quote_items.pop(idx)
            st.rerun()

# --- CALCULATIONS ---
actual_hire = sum(i["TotalHire"] for i in st.session_state.quote_items)
final_hire = max(300.0, actual_hire) if st.session_state.quote_items else 0.0
waiver = final_hire * 0.07
labour_final = sum(i["LabourCost"] for i in st.session_state.quote_items)
cartage_final = (km_input * 4 * 3.50) if charge_cartage else 0.0
grand_total = final_hire + waiver + labour_final + cartage_final

# --- TOTALS DISPLAY ---
st.divider()
st.markdown("### 💰 TOTALS (EX GST)")
r1c1, r1c2 = st.columns(2)
r1c1.metric("TOTAL HIRE", f"${final_hire:,.2f}")
r1c2.metric("WAIVER (7%)", f"${waiver:,.2f}")
r2c1, r2c2 = st.columns(2)
r2c1.metric("LABOUR", f"${labour_final:,.2f}")
r2c2.metric("CARTAGE", f"${cartage_final:,.2f}")
st.metric("GRAND TOTAL", f"${grand_total:,.2f}")

# --- BREAKDOWN & COPY BLOCK ---
if st.session_state.quote_items:
    st.markdown('<div class="breakdown-box">', unsafe_allow_html=True)
    st.markdown("#### 📋 QUOTE TEXT FOR SYSTEM")
    
    for i in st.session_state.quote_items:
        copy_block = (
            f"PRICING BASED ON {i['Weeks']} WEEK HIRE PERIOD\n"
            f"Price for Initial Week's Hire including installation & removal = ${i['InitialRate']:.2f}/sqm + GST\n"
            f"Price for each Subsequent Week's Hire = ${i['AppliedRate']:.2f}/sqm + GST"
        )
        
        st.write(f"**{i['Item']}**")
        if i['IsOverridden']:
            st.markdown(f'<span class="override-note">Manual override applied (Orig: ${i["OrigRate"]:.2f})</span>', unsafe_allow_html=True)
        
        st.text_area("Copy this block:", value=copy_block, height=110, key=f"copy_{idx}_{i['Item']}")
        
        sys_rate = i["TotalHire"] / i["Qty"]
        st.success(f"**RATE TO ENTER IN SYSTEM: ${sys_rate:.2f}**")
        st.markdown("---")
    
    if st.button("RESET QUOTE"):
        st.session_state.quote_items = []
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
