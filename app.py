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

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Price", "Disc %", "Total", "Labour_Rate"])

st.title("📦 No Fuss Quoting Engine")

# --- LOGISTICS ---
with st.expander("📍 LOGISTICS & DATES", expanded=True):
    c1, c2, c3 = st.columns(3)
    start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
    end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
    # value=None removes the 0.00 default
    km_input = c3.number_input("Distance (KM)", min_value=0.0, value=None, placeholder="Type KM...")
    
    col_lab, col_cart = st.columns(2)
    charge_labour = col_lab.checkbox("Include Labour/Crew?", value=True)
    charge_cartage = col_cart.checkbox("Include Cartage?", value=True)

# Calculate live weeks based on currently selected dates
days_diff = (end_date - start_date).days
live_weeks = math.ceil(days_diff / 7) if days_diff > 0 else 1

# --- ADD PRODUCT ---
st.markdown("### ➕ ADD PRODUCT")
item_choice = st.selectbox("Select Product", sorted(PRODUCT_CATALOG.keys()))
c_q, c_a, c_d = st.columns([2, 2, 2])
# value=None removes the 0.00 default for faster filling
qty_in = c_q.number_input("Quantity", min_value=0.0, value=None, placeholder="Type Qty...")
adj_rate = c_a.number_input("Override Rate", min_value=0.0, value=None, placeholder="Standard Rate...")
discount_pct = c_d.number_input("Discount %", min_value=0.0, max_value=100.0, value=None, placeholder="0%")

if st.button("ADD TO QUOTE"):
    if qty_in and qty_in > 0:
        base_rate = adj_rate if (adj_rate and adj_rate > 0) else PRODUCT_CATALOG[item_choice]["rate"]
        labour_r = PRODUCT_CATALOG[item_choice]["labour"]
        final_disc = discount_pct if discount_pct else 0.0
        
        new_row = pd.DataFrame([{
            "Qty": qty_in,
            "Product": item_choice,
            "Unit Price": base_rate,
            "Disc %": final_disc,
            "Total": 0.0, 
            "Labour_Rate": labour_r
        }])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.rerun()

# --- LIVE SYNC AND CALCULATION LOOP ---
if not st.session_state.df.empty:
    for index, row in st.session_state.df.iterrows():
        q = row["Qty"]
        p = row["Unit Price"]
        d = row["Disc %"]
        hire_pre_disc = (q * p) + (q * p * (live_weeks - 1))
        st.session_state.df.at[index, "Total"] = hire_pre_disc * (1 - (d / 100))

    st.markdown("### 🏗️ FLOORING")
    edited_df = st.data_editor(
        st.session_state.df,
        column_order=("Qty", "Product", "Unit Price", "Disc %", "Total"),
        num_rows="dynamic",
        use_container_width=True,
        key="live_editor"
    )

    if not edited_df.equals(st.session_state.df):
        st.session_state.df = edited_df
        st.rerun()

    # Final math
    km_val = km_input if km_input else 0.0
    cart_final = (km_val * 4 * 3.50) if charge_cartage else 0.0
    lab_final = (st.session_state.df["Qty"] * st.session_state.df["Labour_Rate"]).sum() if charge_labour else 0.0
    pure_hire = st.session_state.df["Total"].sum()
    hire_final = max(300.0, pure_hire)
    waiver = hire_final * 0.07
    grand_total = hire_final + waiver + cart_final + lab_final

    # --- TOTALS METRICS ---
    st.divider()
    st.markdown("### 💰 SUMMARY (EX GST)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE COST", f"${pure_hire:,.2f}")
    m2.metric("WAIVER (7%)", f"${waiver:,.2f}")
    m3.metric("LABOUR", f"${lab_final:,.2f}")
    m4.metric("CARTAGE", f"${cart_final:,.2f}")
    st.metric("GRAND TOTAL", f"${grand_total:,.2f}")
    
    # --- DYNAMIC SYSTEM TEXT ---
    st.markdown("### 📋 QUOTE TEXT FOR SYSTEM")
    st.info(f"Pricing below is calculated based on a **{live_weeks} week** hire period.")
    
    for index, row in st.session_state.df.iterrows():
        init_week = row["Unit Price"] + row["Labour_Rate"]
        sub_week = row["Unit Price"]
        copy_block = (
            f"PRICING BASED ON {live_weeks} WEEK HIRE PERIOD\n"
            f"Price for Initial Week's Hire including installation & removal = ${init_week:.2f}/sqm + GST\n"
            f"Price for each Subsequent Week's Hire = ${sub_week:.2f}/sqm + GST"
        )
        st.text_area(f"Copy for {row['Product']} (Row {index+1}):", value=copy_block, height=110)

    if st.button("RESET ALL"):
        st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Price", "Disc %", "Total", "Labour_Rate"])
        st.rerun()
