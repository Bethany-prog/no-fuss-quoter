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
    
    /* Bigger Checkboxes */
    [data-testid="stCheckbox"] {
        background-color: #1A1D2D;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3D5AFE;
        margin-bottom: 10px;
    }
    [data-testid="stCheckbox"] label p {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #00E676 !important;
    }
    
    /* Metrics and Header Styling */
    label { color: #000000 !important; font-weight: 800 !important; font-size: 16px !important; }
    [data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; font-size: 16px !important; }
    div.stMetric { background-color: #1A1D2D; padding: 20px; border-radius: 12px; border: 2px solid #3D5AFE; }
    
    /* Button Styling */
    div.stButton > button:first-child {
        background-color: #3D5AFE; color: white; border-radius: 10px; height: 55px; font-weight: bold; font-size: 18px;
    }
    
    /* Section Headers */
    h3 { color: #00E676 !important; border-left: 5px solid #00E676; padding-left: 15px; margin-top: 30px; margin-bottom: 20px; }
    
    /* Data Grid Styling */
    .stDataFrame { border: 2px solid #00E676 !important; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 3. OFFICIAL CATALOG 
PRODUCT_CATALOG = {
    "I-TRAC": {
        "I-Trac flooring (sqm)": {"w1_3": 23.40, "block": 46.80, "labour": 4.65},
        "I-Trac ramps (ea)": {"w1_3": 42.00, "block": 84.00, "labour": 0.00}
    },
    "SUPA-TRAC": {
        "Supa-Trac flooring (sqm)": {"w1_3": 11.55, "block": 25.00, "labour": 4.65},
        "Supa-Trac Edging (lm)": {"w1_3": 6.70, "block": 6.70, "labour": 0.00}
    },
    "TRAKMATS": {
        "Trakmats (ea)": {"w1_3": 23.20, "block": 45.00, "labour": 5.85},
        "Trakmat Joiners 4 hole (ea)": {"w1_3": 11.95, "block": 11.95, "labour": 0.00},
        "Trakmat Joiners 2 hole (ea)": {"w1_3": 4.40, "block": 4.40, "labour": 0.00},
        "LD 20 Roll - 3m x 20m": {"w1_3": 1800.00, "block": 3300.00, "labour": 0.00}
    },
    "NO FUSS FLOORING": {
        "No Fuss Floor (Grey/Green) (sqm)": {"w1_3": 7.10, "block": 15.00, "labour": 3.05},
        "No Fuss Floor Ramp 1m (ea)": {"w1_3": 6.60, "block": 13.20, "labour": 0.00},
        "Expansion Joiner 1.2m (ea)": {"w1_3": 6.60, "block": 13.20, "labour": 0.00}
    },
    "PLASTORIP": {
        "Plastorip (sqm)": {"w1_3": 10.15, "block": 20.30, "labour": 3.05},
        "Plastorip Edging (lm)": {"w1_3": 1.65, "block": 1.65, "labour": 0.00},
        "Plastorip Expansion Joiner 1m": {"w1_3": 12.15, "block": 12.15, "labour": 0.00}
    },
    "OTHER": {
        "Terratrak Plus (sqm)": {"w1_3": 23.40, "block": 46.80, "labour": 4.65},
        "Enkamat Underlay (sqm)": {"w1_3": 2.60, "block": 2.60, "labour": 0.00},
        "Geotextile Underlay (sqm)": {"w1_3": 2.60, "block": 2.60, "labour": 0.00},
        "Black Plastic (sqm)": {"w1_3": 0.90, "block": 0.90, "labour": 0.00},
        "Wooden Floor (sqm)": {"w1_3": 8.85, "block": 8.85, "labour": 7.15},
        "Parquetry Dance Floor (sqm)": {"w1_3": 20.95, "block": 20.95, "labour": 4.80},
        "Carpet Tiles - Onyx (sqm)": {"w1_3": 8.85, "block": 8.85, "labour": 3.05},
        "Protectall (sqm)": {"w1_3": 22.05, "block": 22.05, "labour": 3.25}
    }
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE"])

st.title("📦 No Fuss Quoting Pro")

# --- 📍 LOGISTICS (FIXED SECTION) ---
st.markdown("### 📍 LOGISTICS & DATES")
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
km_input = c3.number_input("Distance (KM) from 9 Battery Crt", min_value=0.0, value=None, placeholder="Type KM...")

st.markdown("<br>", unsafe_allow_html=True)
charge_labour = st.checkbox("👷 INCLUDE LABOUR / CREW COSTS", value=True)
charge_cartage = st.checkbox("🚚 INCLUDE CARTAGE / TRANSPORT COSTS", value=True)

# LIVE WEEKS CALC
days_diff = (end_date - start_date).days
live_weeks = math.ceil(days_diff / 7) if days_diff > 0 else 1

# --- ➕ ADD PRODUCT ---
st.markdown("### ➕ ADD PRODUCT")
cat_col, item_col = st.columns(2)
cat_choice = cat_col.selectbox("Product Category", sorted(PRODUCT_CATALOG.keys()))
item_choice = item_col.selectbox("Specific Item", sorted(PRODUCT_CATALOG[cat_choice].keys()))

c_q, c_a, c_d = st.columns([2, 2, 2])
qty_in = c_q.number_input("Quantity", min_value=0.0, value=None, placeholder="Type Qty...")
adj_rate = c_a.number_input("Override Base Rate", min_value=0.0, value=None, placeholder="Adjust Rate...")
discount_pct = c_d.number_input("Special Discount %", min_value=0.0, max_value=100.0, value=None, placeholder="0%")

if st.button("ADD TO QUOTE ENGINE"):
    if qty_in and qty_in > 0:
        ref = PRODUCT_CATALOG[cat_choice][item_choice]
        base_rate = adj_rate if (adj_rate and adj_rate > 0) else ref["w1_3"]
        
        new_row = pd.DataFrame([{
            "Qty": qty_in,
            "Product": item_choice,
            "Unit Rate": base_rate,
            "Disc %": discount_pct if discount_pct else 0.0,
            "Total": 0.0, 
            "Labour_Rate": ref["labour"],
            "Block_Rate": ref["block"],
            "SYSTEM RATE": 0.0
        }])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.rerun()

# --- CALCULATION LOOP ---
if not st.session_state.df.empty:
    for idx, row in st.session_state.df.iterrows():
        q, r1_3, d = row["Qty"], row["Unit Rate"], row["Disc %"]
        block = row["Block_Rate"]
        labour = row["Labour_Rate"]
        
        # Calculate Hire + Optional Labour
        if live_weeks <= 3:
            hire_component = (q * r1_3 * live_weeks)
        else:
            hire_component = (q * r1_3 * 3) + (q * block)
        
        labour_component = (q * labour) if charge_labour else 0.0
        final_total = (hire_component + labour_component) * (1 - (d / 100))
        
        st.session_state.df.at[idx, "Total"] = final_total
        st.session_state.df.at[idx, "SYSTEM RATE"] = final_total / q if q > 0 else 0.0

    st.markdown("### 🏗️ QUOTED ITEMS & SYSTEM RATES")
    edited_df = st.data_editor(st.session_state.df[["Qty", "Product", "SYSTEM RATE", "Unit Rate", "Disc %", "Total"]], 
                               num_rows="dynamic", use_container_width=True, key="editor",
                               column_config={
                                   "SYSTEM RATE": st.column_config.NumberColumn("🔢 COPY TO SYSTEM", format="$%.2f")
                               })

    if not edited_df.equals(st.session_state.df[["Qty", "Product", "SYSTEM RATE", "Unit Rate", "Disc %", "Total"]]):
        for col in ["Qty", "Unit Rate", "Disc %"]:
            st.session_state.df[col] = edited_df[col]
        st.rerun()

    # Summary Totals
    pure_hire = st.session_state.df["Total"].sum()
    hire_final = max(300.0, pure_hire)
    waiver = hire_final * 0.07
    cart_final = (km_input * 4 * 3.50) if km_input and charge_cartage else 0.0
    
    st.divider()
    st.markdown("### 💰 FINANCIAL SUMMARY (EX GST)")
    m1, m2, m3 = st.columns(3)
    m1.metric("TOTAL LINE ITEMS", f"${pure_hire:,.2f}")
    m2.metric("WAIVER (7%)", f"${waiver:,.2f}")
    m3.metric("CARTAGE TOTAL", f"${cart_final:,.2f}")
    st.metric("GRAND TOTAL QUOTE", f"${(hire_final + waiver + cart_final):,.2f}")
    
    # --- DYNAMIC SYSTEM TEXT ---
    st.markdown("### 📋 SYSTEM DESCRIPTION BLOCKS")
    for idx, row in st.session_state.df.iterrows():
        p = row["Unit Rate"]
        init = p + row["Labour_Rate"]
        block_weekly = row["Block_Rate"] / 4
        
        copy_block = (
            f"PRICING BASED ON {live_weeks} WEEK HIRE PERIOD\n"
            f"Price for Initial Week's Hire including installation & removal = ${init:,.2f}/sqm + GST\n"
            f"Price for weeks 2 & 3 = ${p:,.2f}/sqm per week + GST\n"
        )
        if live_weeks >= 4:
            copy_block += f"Price for weeks 4+ = ${block_weekly:,.2f}/sqm per week + GST"
            
        st.text_area(f"Line Item {idx+1}: {row['Product']}", value=copy_block, height=140)

    if st.button("⚠️ RESET ENTIRE QUOTE"):
        st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE"])
        st.rerun()
