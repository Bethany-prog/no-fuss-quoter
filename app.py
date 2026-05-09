import streamlit as st
import math
import pandas as pd
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
st.set_page_config(page_title="No Fuss Quote Pro", page_icon="📦", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0F111A; }
    label, .stCheckbox { color: #000000 !important; font-weight: 800 !important; }
    [data-testid="stMetricValue"] { color: #00E676 !important; font-size: 24px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; font-size: 14px !important; }
    div.stMetric { background-color: #1A1D2D; padding: 15px; border-radius: 10px; border: 1px solid #3D5AFE; }
    div.stButton > button:first-child {
        background-color: #3D5AFE; color: white; border-radius: 8px; width: 100%; font-weight: bold;
    }
    [data-testid="stExpander"] { border: 2px solid #3D5AFE; border-radius: 12px; background-color: #FFFFFF; }
    h3 { color: #00E676 !important; border-bottom: 2px solid #00E676; padding-bottom: 5px; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 3. OFFICIAL CATALOG (OCTOBER 2025 PDF)
# sub = Standard Weekly | block_weekly = (4 Week Block Price / 4)
PRODUCT_CATALOG = {
    "Black Plastic (sqm)": {"sub": 0.90, "block_weekly": 0.90, "labour": 0.00},
    "Carpet Tiles - Onyx 1m x 1m": {"sub": 8.85, "block_weekly": 8.85, "labour": 3.05},
    "Enkamat Underlay (sqm)": {"sub": 2.60, "block_weekly": 2.60, "labour": 0.00},
    "Geotextile Underlay (sqm)": {"sub": 2.60, "block_weekly": 2.60, "labour": 0.00},
    "I-Trac (sqm)": {"sub": 23.40, "block_weekly": 11.70, "labour": 4.65},
    "LD 20 Roll-3m x 20m": {"sub": 1800.00, "block_weekly": 500.00, "labour": 0.00, "special_ld20": True},
    "No Fuss Expansion Joiner 1.2m": {"sub": 6.60, "block_weekly": 3.30, "labour": 0.00},
    "No Fuss Floor (Grey or Green)": {"sub": 7.10, "block_weekly": 3.75, "labour": 3.05},
    "No Fuss Floor Ramp 1m": {"sub": 6.60, "block_weekly": 3.30, "labour": 0.00},
    "Parquetry Dance Floor": {"sub": 20.95, "block_weekly": 20.95, "labour": 4.80},
    "Plastorip": {"sub": 10.15, "block_weekly": 5.075, "labour": 3.05},
    "Plastorip Edging (per lineal metre)": {"sub": 1.65, "block_weekly": 1.65, "labour": 0.00},
    "Plastorip Expansion Joiners 1m": {"sub": 12.15, "block_weekly": 12.15, "labour": 0.00},
    "Protectall": {"sub": 22.05, "block_weekly": 22.05, "labour": 3.25},
    "Ramp for I-Trac (1.07m x 1.18m)": {"sub": 42.00, "block_weekly": 21.00, "labour": 0.00},
    "Supa-Trac (per sqm)": {"sub": 11.55, "block_weekly": 6.25, "labour": 4.65},
    "Supa-Trac Edging (per lineal metre)": {"sub": 6.70, "block_weekly": 6.70, "labour": 0.00},
    "Terratrak Plus": {"sub": 23.40, "block_weekly": 11.70, "labour": 4.65},
    "Trakmat Joiners 2 hole": {"sub": 4.40, "block_weekly": 4.40, "labour": 0.00},
    "Trakmat Joiners 4 hole": {"sub": 11.95, "block_weekly": 11.95, "labour": 0.00},
    "Trakmats": {"sub": 23.20, "block_weekly": 11.25, "labour": 5.85},
    "Wooden Floor": {"sub": 8.85, "block_weekly": 8.85, "labour": 7.15},
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Price", "Disc %", "Total", "Labour_Rate"])

st.title("📦 No Fuss Quoting Engine")

# --- LOGISTICS ---
with st.expander("📍 LOGISTICS & DATES", expanded=True):
    c1, c2, c3 = st.columns(3)
    start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
    end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
    km_input = c3.number_input("Distance (KM)", min_value=0.0, value=None, placeholder="Type KM...")
    
    col_lab, col_cart = st.columns(2)
    charge_labour = col_lab.checkbox("Include Labour/Crew?", value=True)
    charge_cartage = col_cart.checkbox("Include Cartage?", value=True)

# LIVE WEEKS CALC
days_diff = (end_date - start_date).days
live_weeks = math.ceil(days_diff / 7) if days_diff > 0 else 1

# --- ADD PRODUCT ---
st.markdown("### ➕ ADD PRODUCT")
item_choice = st.selectbox("Select Product", sorted(PRODUCT_CATALOG.keys()))
c_q, c_a, c_d = st.columns([2, 2, 2])
qty_in = c_q.number_input("Quantity", min_value=0.0, value=None, placeholder="Type Qty...")
adj_rate = c_a.number_input("Override Sub Rate", min_value=0.0, value=None, placeholder="Adjust Rate...")
discount_pct = c_d.number_input("Discount %", min_value=0.0, max_value=100.0, value=None, placeholder="0%")

if st.button("ADD TO QUOTE"):
    if qty_in and qty_in > 0:
        labour_r = PRODUCT_CATALOG[item_choice]["labour"]
        initial_base = adj_rate if (adj_rate and adj_rate > 0) else PRODUCT_CATALOG[item_choice]["sub"]
        
        new_row = pd.DataFrame([{
            "Qty": qty_in,
            "Product": item_choice,
            "Unit Price": initial_base,
            "Disc %": discount_pct if discount_pct else 0.0,
            "Total": 0.0, 
            "Labour_Rate": labour_r
        }])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.rerun()

# --- LIVE RE-CALCULATION BLOCK ---
if not st.session_state.df.empty:
    for idx, row in st.session_state.df.iterrows():
        q, p, d = row["Qty"], row["Unit Price"], row["Disc %"]
        l_rate = row["Labour_Rate"]
        item_key = row["Product"]
        
        # SPECIAL LOGIC: LD 20 Roll
        if PRODUCT_CATALOG[item_key].get("special_ld20"):
            initial_week_rate = 1800.00
            sub_rate_to_use = 500.00
        else:
            # BLOCK LOGIC: If hire is 5+ weeks (1 initial + 4 subsequent), use the discounted block rate
            sub_rate_to_use = PRODUCT_CATALOG[item_key]["block_weekly"] if live_weeks >= 5 else p
            initial_week_rate = sub_rate_to_use + l_rate
            
        hire_val = (q * initial_week_rate) + (q * sub_rate_to_use * (live_weeks - 1))
        
        st.session_state.df.at[idx, "Total"] = hire_val * (1 - (d / 100))
        st.session_state.df.at[idx, "Unit Price"] = sub_rate_to_use

    st.markdown("### 🏗️ FLOORING")
    edited_df = st.data_editor(st.session_state.df[["Qty", "Product", "Unit Price", "Disc %", "Total"]], num_rows="dynamic", use_container_width=True, key="editor")

    if not edited_df.equals(st.session_state.df[["Qty", "Product", "Unit Price", "Disc %", "Total"]]):
        for col in ["Qty", "Unit Price", "Disc %"]:
            st.session_state.df[col] = edited_df[col]
        st.rerun()

    # Final Summary Math
    pure_hire = st.session_state.df["Total"].sum()
    hire_final = max(300.0, pure_hire)
    waiver = hire_final * 0.07
    cart_final = (km_input * 4 * 3.50) if km_input and charge_cartage else 0.0
    lab_final = (st.session_state.df["Qty"] * st.session_state.df["Labour_Rate"]).sum() if charge_labour else 0.0
    
    st.divider()
    st.markdown("### 💰 SUMMARY (EX GST)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE COST", f"${pure_hire:,.2f}")
    m2.metric("WAIVER (7%)", f"${waiver:,.2f}")
    m3.metric("LABOUR", f"${lab_final:,.2f}")
    m4.metric("CARTAGE", f"${cart_final:,.2f}")
    st.metric("GRAND TOTAL", f"${(hire_final + waiver + cart_final + lab_final):,.2f}")
    
    # --- DYNAMIC SYSTEM TEXT ---
    st.markdown("### 📋 QUOTE TEXT FOR SYSTEM")
    for idx, row in st.session_state.df.iterrows():
        item_key = row["Product"]
        p = row["Unit Price"]
        
        if PRODUCT_CATALOG[item_key].get("special_ld20"):
            init = 1800.00
        else:
            init = p + row["Labour_Rate"]
            
        copy_block = (
            f"PRICING BASED ON {live_weeks} WEEK HIRE PERIOD\n"
            f"Price for Initial Week's Hire including installation & removal = ${init:,.2f}/sqm + GST\n"
            f"Price for each Subsequent Week's Hire = ${p:,.2f}/sqm + GST"
        )
        st.text_area(f"Copy for {row['Product']}:", value=copy_block, height=110)

    if st.button("RESET ALL"):
        st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Price", "Disc %", "Total", "Labour_Rate"])
        st.rerun()
