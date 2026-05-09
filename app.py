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

# Initialize the main dataframe in session state
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Price", "Disc %", "Total", "Weeks", "Labour_Rate"])

st.title("📦 No Fuss Quoting Engine")

# --- LOGISTICS ---
with st.expander("📍 LOGISTICS & DATES", expanded=True):
    c1, c2, c3 = st.columns(3)
    start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
    end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
    km_input = c3.number_input("Distance (KM)", min_value=0.0, value=0.0)
    
    col_lab, col_cart = st.columns(2)
    charge_labour = col_lab.checkbox("Include Labour/Crew?", value=True)
    charge_cartage = col_cart.checkbox("Include Cartage?", value=True)

# --- ADD PRODUCT ---
st.markdown("### ➕ ADD PRODUCT")
item_choice = st.selectbox("Select Product", sorted(PRODUCT_CATALOG.keys()))
c_q, c_a, c_d = st.columns([2, 2, 2])
qty_in = c_q.number_input("Quantity", min_value=0.0, value=0.0)
adj_rate = c_a.number_input("Override Rate", min_value=0.0, value=0.0)
discount_pct = c_d.number_input("Discount %", min_value=0.0, max_value=100.0, value=0.0)

if st.button("ADD TO QUOTE"):
    if qty_in > 0:
        days = (end_date - start_date).days
        weeks = math.ceil(days / 7) if days > 0 else 1
        base_rate = adj_rate if adj_rate > 0 else PRODUCT_CATALOG[item_choice]["rate"]
        labour_r = PRODUCT_CATALOG[item_choice]["labour"]
        
        # Calculate Initial Total
        subtotal = (qty_in * base_rate) + (qty_in * base_rate * (weeks - 1))
        final_total = subtotal * (1 - (discount_pct / 100))
        
        new_row = pd.DataFrame([{
            "Qty": qty_in,
            "Product": item_choice,
            "Unit Price": base_rate,
            "Disc %": discount_pct,
            "Total": final_total,
            "Weeks": weeks,
            "Labour_Rate": labour_r
        }])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.rerun()

# --- THE GRIDS ---
if not st.session_state.df.empty:
    st.markdown("### 🏗️ FLOORING")
    
    # Capture edits directly from the grid
    edited_df = st.data_editor(
        st.session_state.df,
        column_order=("Qty", "Product", "Unit Price", "Disc %", "Total"),
        num_rows="dynamic",
        use_container_width=True,
        key="editor"
    )

    # MANDATORY SYNC: This ensures manual edits to Qty/Price/Discount update the totals and labour
    if not edited_df.equals(st.session_state.df):
        for index, row in edited_df.iterrows():
            # Recalculate based on possibly edited values
            w = row["Weeks"]
            q = row["Qty"]
            p = row["Unit Price"]
            d = row["Disc %"]
            
            sub = (q * p) + (q * p * (w - 1))
            edited_df.at[index, "Total"] = sub * (1 - (d / 100))
            
        st.session_state.df = edited_df
        st.rerun()

    # 2. CARTAGE GRID
    if charge_cartage:
        st.markdown("### 🚚 CARTAGE")
        cart_price = km_input * 4 * 3.50
        st.table([{"QTY": 1, "Description": "Cartage", "Price": f"${cart_price:,.2f}"}])

    # 3. LABOUR GRID
    if charge_labour:
        st.markdown("### 👷 LABOUR")
        # Calculate labour based on edited Qty and fixed Labour Rate
        lab_sum = (st.session_state.df["Qty"] * st.session_state.df["Labour_Rate"]).sum()
        st.table([{"QTY": 1, "Description": "Crew", "Price": f"${lab_sum:,.2f}"}])

    # FINAL CALCULATIONS
    pure_hire = st.session_state.df["Total"].sum()
    hire_final = max(300.0, pure_hire)
    waiver = hire_final * 0.07
    cart_final = (km_input * 4 * 3.50) if charge_cartage else 0.0
    lab_final = (st.session_state.df["Qty"] * st.session_state.df["Labour_Rate"]).sum() if charge_labour else 0.0
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
    
    # --- DYNAMIC SYSTEM TEXT (Matches Grid exactly) ---
    st.markdown("### 📋 QUOTE TEXT FOR SYSTEM")
    for index, row in st.session_state.df.iterrows():
        # Math for the text blocks based on current row state
        init_week = row["Unit Price"] + row["Labour_Rate"]
        sub_week = row["Unit Price"]
        
        copy_block = (
            f"PRICING BASED ON {row['Weeks']} WEEK HIRE PERIOD\n"
            f"Price for Initial Week's Hire including installation & removal = ${init_week:.2f}/sqm + GST\n"
            f"Price for each Subsequent Week's Hire = ${sub_week:.2f}/sqm + GST"
        )
        st.text_area(f"Copy for {row['Product']} (Row {index+1}):", value=copy_block, height=110)

    if st.button("RESET ALL"):
        st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Price", "Disc %", "Total", "Weeks", "Labour_Rate"])
        st.rerun()
