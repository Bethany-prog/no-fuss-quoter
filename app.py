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
    [data-testid="stCheckbox"] {
        background-color: #1A1D2D;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #3D5AFE;
        margin-bottom: 8px;
    }
    [data-testid="stCheckbox"] label p {
        font-size: 18px !important;
        font-weight: bold !important;
        color: #00E676 !important;
    }
    label { color: #000000 !important; font-weight: 800 !important; font-size: 16px !important; }
    [data-testid="stMetricValue"] { color: #00E676 !important; font-size: 30px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; font-size: 14px !important; }
    div.stMetric { background-color: #1A1D2D; padding: 20px; border-radius: 12px; border: 2px solid #3D5AFE; }
    div.stButton > button:first-child {
        background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold;
    }
    h3 { color: #00E676 !important; border-left: 5px solid #00E676; padding-left: 15px; margin-top: 25px; }
    .stDataFrame { border: 2px solid #00E676 !important; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 3. EXPANDED MASTER CATALOG
PRODUCT_CATALOG = {
    "FLOORING": {
        "I-Trac flooring (sqm)": {"w1_3": 23.40, "block": 46.80, "labour": 4.65},
        "I-Trac ramps (ea)": {"w1_3": 42.00, "block": 84.00, "labour": 0.00},
        "Supa-Trac flooring (sqm)": {"w1_3": 11.55, "block": 25.00, "labour": 4.65},
        "Supa-Trac Edging (lm)": {"w1_3": 6.70, "block": 6.70, "labour": 0.00},
        "Trakmats (ea)": {"w1_3": 23.20, "block": 45.00, "labour": 5.85},
        "No Fuss Floor (Grey/Green) (sqm)": {"w1_3": 7.10, "block": 15.00, "labour": 3.05}
    },
    "MOJO BARRIERS": {
        "Mojo Straight (1m Bay)": {"w1_3": 0.00, "block": 0.00, "labour": 0.00},
        "Mojo Corner / Flex": {"w1_3": 0.00, "block": 0.00, "labour": 0.00},
        "Mojo Gate Bay": {"w1_3": 0.00, "block": 0.00, "labour": 0.00}
    },
    "MARQUEES": {
        "6m x 6m Pagoda": {"w1_3": 0.00, "block": 0.00, "labour": 0.00},
        "10m Structure (per sqm)": {"w1_3": 0.00, "block": 0.00, "labour": 0.00},
        "Weights / Anchoring": {"w1_3": 0.00, "block": 0.00, "labour": 0.00}
    },
    "GRANDSTANDS": {
        "3-Tier Seating (per bay)": {"w1_3": 0.00, "block": 0.00, "labour": 0.00},
        "Grandstand Staircase": {"w1_3": 0.00, "block": 0.00, "labour": 0.00}
    }
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE"])

st.title("📦 No Fuss Quote Pro")

# --- LOGISTICS ---
st.markdown("### 📍 LOGISTICS & DATES")
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=None, placeholder="Type KM...")

charge_labour = st.checkbox("👷 INCLUDE LABOUR COST IN QUOTE", value=True)
split_labour = st.checkbox("✂️ SPLIT LABOUR TO SEPARATE LINE ITEM", value=False)
charge_cartage = st.checkbox("🚚 INCLUDE CARTAGE / TRANSPORT COSTS", value=True)

days_diff = (end_date - start_date).days
live_weeks = math.ceil(days_diff / 7) if days_diff > 0 else 1

# --- ADD PRODUCT ---
st.markdown("### ➕ ADD PRODUCT")
dept_col, item_col = st.columns(2)
dept_choice = dept_col.selectbox("Department", sorted(PRODUCT_CATALOG.keys()))
item_choice = item_col.selectbox("Select Product", sorted(PRODUCT_CATALOG[dept_choice].keys()))

c_q, c_a, c_d = st.columns([2, 2, 2])
qty_in = c_q.number_input("Quantity", min_value=0.0, value=None, placeholder="Type Qty...")
adj_rate = c_a.number_input("Override Wk 1-3 Rate", min_value=0.0, value=None, placeholder="Adjust Rate...")
discount_pct = c_d.number_input("Discount %", min_value=0.0, max_value=100.0, value=None, placeholder="0%")

if st.button("ADD TO QUOTE ENGINE"):
    if qty_in and qty_in > 0:
        ref = PRODUCT_CATALOG[dept_choice][item_choice]
        # Fallback to 0.0 if rate cards aren't in yet
        base_rate = adj_rate if (adj_rate and adj_rate > 0) else ref["w1_3"]
        
        new_row = pd.DataFrame([{
            "Qty": qty_in, "Product": item_choice, "Unit Rate": base_rate,
            "Disc %": discount_pct if discount_pct else 0.0, "Total": 0.0, 
            "Labour_Rate": ref["labour"], "Block_Rate": ref["block"], "SYSTEM RATE": 0.0
        }])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.rerun()

# --- CALCULATION LOOP ---
if not st.session_state.df.empty:
    lab_total_standalone = 0.0
    for idx, row in st.session_state.df.iterrows():
        q, r1_3, d, block, lab_r = row["Qty"], row["Unit Rate"], row["Disc %"], row["Block_Rate"], row["Labour_Rate"]
        hire_comp = (q * r1_3 * live_weeks) if live_weeks <= 3 else (q * r1_3 * 3) + (q * block)
        
        if not charge_labour:
            item_lab = 0.0
        elif split_labour:
            item_lab = 0.0
            lab_total_standalone += (q * lab_r) * (1 - (d / 100))
        else:
            item_lab = q * lab_r
            
        final_tot = (hire_comp + item_lab) * (1 - (d / 100))
        st.session_state.df.at[idx, "Total"] = final_tot
        st.session_state.df.at[idx, "SYSTEM RATE"] = final_tot / q if q > 0 else 0.0

    st.markdown("### 🏗️ QUOTED ITEMS & SYSTEM RATES")
    edited_df = st.data_editor(st.session_state.df[["Qty", "Product", "SYSTEM RATE", "Unit Rate", "Disc %", "Total"]], 
                               num_rows="dynamic", use_container_width=True, key="editor")

    if not edited_df.equals(st.session_state.df[["Qty", "Product", "SYSTEM RATE", "Unit Rate", "Disc %", "Total"]]):
        for col in ["Qty", "Unit Rate", "Disc %"]:
            st.session_state.df[col] = edited_df[col]
        st.rerun()

    pure_hire = st.session_state.df["Total"].sum()
    waiver = max(300.0, pure_hire + lab_total_standalone) * 0.07
    cart_final = (km_input * 4 * 3.50) if km_input and charge_cartage else 0.0
    
    st.divider()
    st.markdown("### 💰 FINANCIAL SUMMARY (EX GST)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE TOTAL", f"${pure_hire:,.2f}")
    m2.metric("LABOUR TOTAL", f"${lab_total_standalone:,.2f}")
    m3.metric("WAIVER (7%)", f"${waiver:,.2f}")
    m4.metric("CARTAGE TOTAL", f"${cart_final:,.2f}")
    st.metric("GRAND TOTAL QUOTE", f"${(pure_hire + lab_total_standalone + waiver + cart_final):,.2f}")
    
    st.markdown("### 📋 SYSTEM DESCRIPTION BLOCKS")
    for idx, row in st.session_state.df.iterrows():
        p, lab_r = row["Unit Rate"], row["Labour_Rate"]
        init_p = p if split_labour else p + lab_r
        copy_block = f"PRICING BASED ON {live_weeks} WEEK HIRE PERIOD\n"
        
        if init_p == p:
            end_wk = min(live_weeks, 3)
            copy_block += f"Price for weeks 1-{end_wk} = ${p:,.2f} per unit/week + GST\n" if end_wk > 1 else f"Price for week 1 = ${p:,.2f} per unit + GST\n"
        else:
            copy_block += f"Price for Initial Week including install/removal = ${init_p:,.2f} per unit + GST\n"
            if live_weeks > 1:
                end_wk = min(live_weeks, 3)
                copy_block += f"Price for week 2 = ${p:,.2f}/unit week + GST\n" if end_wk == 2 else f"Price for weeks 2-{end_wk} = ${p:,.2f}/unit week + GST\n"
        
        if live_weeks >= 4:
            copy_block += f"Price for weeks 4+ = ${row['Block_Rate'] / 4:,.2f} per unit/week + GST"
            
        st.text_area(f"Line Item {idx+1}: {row['Product']}", value=copy_block, height=140)

    if st.button("⚠️ RESET ENTIRE QUOTE"):
        st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE"])
        st.rerun()
