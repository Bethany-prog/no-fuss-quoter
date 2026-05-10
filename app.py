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
    div[data-testid="stSelectbox"] label p { font-size: 18px !important; color: #00E676 !important; font-weight: bold !important; }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; }
    div.stMetric { background-color: #1A1D2D; padding: 20px; border-radius: 12px; border: 2px solid #3D5AFE; }
    div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; }
    h3 { color: #00E676 !important; border-left: 5px solid #00E676; padding-left: 15px; margin-top: 25px; }
    .stDataFrame { border: 2px solid #00E676 !important; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 3. MASTER CATALOG (October 2025 Standard)
PRODUCT_CATALOG = {
    "FLOORING": {
        "I-Trac flooring (sqm)": {"w1_3": 23.40, "block": 46.80, "labour": 4.65},
        "I-Trac ramps (ea)": {"w1_3": 42.00, "block": 84.00, "labour": 0.00},
        "Supa-Trac flooring (sqm)": {"w1_3": 11.55, "block": 25.00, "labour": 4.65},
        "Supa-Trac Edging (lm)": {"w1_3": 6.70, "block": 6.70, "labour": 0.00},
        "Trakmats (ea)": {"w1_3": 23.20, "block": 45.00, "labour": 5.85},
        "No Fuss Floor (Grey/Green) (sqm)": {"w1_3": 7.10, "block": 15.00, "labour": 3.05}
    },
    "GRANDSTANDS": {
        "Grandstand Seating (per seat)": {"is_gs": True, "labour": 0.00},
        "Shade Cloth / Scrim (per lm)": {"w1_3": 6.00, "block": 12.00, "labour": 0.00}
    },
    "MOJO BARRIERS": {
        "Mojo Straight (1m Bay)": {"w1_3": 0.00, "block": 0.00, "labour": 0.00},
        "Mojo Corner / Flex": {"w1_3": 0.00, "block": 0.00, "labour": 0.00}
    }
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS"])

st.title("📦 No Fuss Quote Pro")

# --- 1. LOGISTICS & LABOUR ---
st.markdown("### 📍 LOGISTICS & LABOUR")
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=None, placeholder="Type KM...")

has_gs = st.session_state.df["Is_GS"].any()
if has_gs:
    st.info("💡 Grandstand pricing automatically includes built-in installation labour.")
    labour_mode = "Bake Labour into Unit Rate"
else:
    labour_mode = st.selectbox("How should Labour be handled?", 
                               ["Bake Labour into Unit Rate", "Show Labour as Separate Line Item", "No Labour (Delivery Only)"])

charge_cartage = st.checkbox("🚚 Include Cartage Costs ($3.50/km x 4 trips)", value=True)

days_diff = (end_date - start_date).days
live_weeks = math.ceil(days_diff / 7) if days_diff > 0 else 1

# --- 2. ADD PRODUCT ---
st.markdown("### ➕ ADD PRODUCT")
dept_col, item_col = st.columns(2)
dept_choice = dept_col.selectbox("Department", sorted(PRODUCT_CATALOG.keys()))
item_choice = item_col.selectbox("Product", sorted(PRODUCT_CATALOG[dept_choice].keys()))

c_q, c_a, c_d = st.columns([2, 2, 2])
qty_in = c_q.number_input("Quantity / Seats", min_value=0.0, value=None, placeholder="Qty...")
adj_rate = c_a.number_input("Override Rate", min_value=0.0, value=None, placeholder="Manual Price...")
discount_pct = c_d.number_input("Special Discount %", min_value=0.0, max_value=100.0, value=None, placeholder="0%")

if st.button("ADD TO QUOTE"):
    if qty_in and qty_in > 0:
        ref = PRODUCT_CATALOG[dept_choice][item_choice]
        is_gs = ref.get("is_gs", False)
        
        if is_gs:
            # Corrected Ratios v19.4
            if qty_in <= 40: s, h = 2, 4
            elif qty_in <= 100: s, h = 3, 5
            elif qty_in <= 149: s, h = 4, 5
            elif qty_in <= 199: s, h = 5, 5
            elif qty_in <= 299: s, h = 5, 6
            else: s, h = 6, 10
            
            calc_rate = (s * h * 55.0 * 4) / qty_in
            base_rate = adj_rate if (adj_rate and adj_rate > 0) else calc_rate
            lab_r, block_r = 0.0, base_rate * 2
        else:
            base_rate = adj_rate if (adj_rate and adj_rate > 0) else ref.get("w1_3", 0.0)
            lab_r, block_r = ref.get("labour", 0.0), ref.get("block", 0.0)

        new_row = pd.DataFrame([{
            "Qty": qty_in, "Product": item_choice, "Unit Rate": base_rate,
            "Disc %": discount_pct if discount_pct else 0.0, "Total": 0.0, 
            "Labour_Rate": lab_r, "Block_Rate": block_r, "SYSTEM RATE": 0.0, 
            "No_Waiver": False, "Is_GS": is_gs
        }])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.rerun()

# --- 3. DYNAMIC ENGINEER TICK OPTION ---
if has_gs:
    st.divider()
    if st.checkbox("👷 Add Engineer Sign-off ($750.00)", value=any(st.session_state.df["Product"] == "Engineer Sign-off")):
        if not any(st.session_state.df["Product"] == "Engineer Sign-off"):
            new_row = pd.DataFrame([{"Qty": 1, "Product": "Engineer Sign-off", "Unit Rate": 750.00, "Disc %": 0.0, "Total": 750.00, "Labour_Rate": 0.0, "Block_Rate": 750.00, "SYSTEM RATE": 750.00, "No_Waiver": True, "Is_GS": False}])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            st.rerun()
    elif any(st.session_state.df["Product"] == "Engineer Sign-off"):
        st.session_state.df = st.session_state.df[st.session_state.df["Product"] != "Engineer Sign-off"]
        st.rerun()

# --- 4. CALCULATION & DATA GRID ---
if not st.session_state.df.empty:
    lab_total_standalone = 0.0
    for idx, row in st.session_state.df.iterrows():
        q, r1_3, d, block, lab_r = row["Qty"], row["Unit Rate"], row["Disc %"], row["Block_Rate"], row["Labour_Rate"]
        hire_comp = (q * r1_3 * live_weeks) if live_weeks <= 3 else (q * r1_3 * 3) + (q * block)
        
        if labour_mode == "No Labour (Delivery Only)":
            item_lab = 0.0
        elif labour_mode == "Show Labour as Separate Line Item":
            item_lab = 0.0
            lab_total_standalone += (q * lab_r) * (1 - (d / 100))
        else:
            item_lab = q * lab_r
            
        final_tot = (hire_comp + item_lab) * (1 - (d / 100))
        st.session_state.df.at[idx, "Total"] = final_tot
        st.session_state.df.at[idx, "SYSTEM RATE"] = final_tot / q if q > 0 else 0.0

    st.markdown("### 🏗️ QUOTED ITEMS")
    # UPDATED COLUMN CONFIG FOR FORCED CENTS
    edited_df = st.data_editor(
        st.session_state.df[["Qty", "Product", "SYSTEM RATE", "Unit Rate", "Disc %", "Total"]], 
        num_rows="dynamic", 
        use_container_width=True, 
        key="editor",
        column_config={
            "SYSTEM RATE": st.column_config.NumberColumn("🔢 SYSTEM RATE", format="$%.2f"),
            "Unit Rate": st.column_config.NumberColumn("Unit Rate", format="$%.2f"),
            "Total": st.column_config.NumberColumn("Total", format="$%.2f")
        }
    )

    if not edited_df.equals(st.session_state.df[["Qty", "Product", "SYSTEM RATE", "Unit Rate", "Disc %", "Total"]]):
        for col in ["Qty", "Unit Rate", "Disc %"]: st.session_state.df[col] = edited_df[col]
        st.rerun()

    pure_hire = st.session_state.df["Total"].sum()
    subtotal = max(2000.00 if has_gs else 300.00, pure_hire + lab_total_standalone)
    
    waiver_base = st.session_state.df[st.session_state.df["No_Waiver"] == False]["Total"].sum()
    waiver = (waiver_base + (lab_total_standalone if labour_mode == "Show Labour as Separate Line Item" else 0)) * 0.07
    cartage = (km_input * 4 * 3.50) if km_input and charge_cartage else 0.0
    
    st.divider()
    st.markdown("### 💰 FINANCIAL SUMMARY")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("SUBTOTAL", f"${subtotal:,.2f}")
    m2.metric("LABOUR (Split)", f"${lab_total_standalone:,.2f}")
    m3.metric("WAIVER (7%)", f"${waiver:,.2f}")
    m4.metric("CARTAGE", f"${cartage:,.2f}")
    st.metric("GRAND TOTAL (EX GST)", f"${(subtotal + waiver + cartage):,.2f}")
    
    st.markdown("### 📋 DESCRIPTION BLOCKS")
    for idx, row in st.session_state.df.iterrows():
        p, lab_r = row["Unit Rate"], row["Labour_Rate"]
        init_p = p if (labour_mode != "Bake Labour into Unit Rate" or lab_r == 0) else p + lab_r
        copy_block = f"PRICING BASED ON {live_weeks} WEEK HIRE PERIOD\n"
        if init_p == p:
            end_wk = min(live_weeks, 3)
            copy_block += f"Price for weeks 1-{end_wk} = ${p:,.2f} per unit/week + GST\n"
        else:
            copy_block += f"Price for Initial Week (Incl. Install) = ${init_p:,.2f} per unit + GST\n"
            if live_weeks > 1: copy_block += f"Price for weeks 2-3 = ${p:,.2f} per unit/week + GST\n"
        if live_weeks >= 4: copy_block += f"Price for weeks 4+ = ${row['Block_Rate'] / 4:,.2f} per unit/week + GST"
        st.text_area(f"Line Item {idx+1}: {row['Product']}", value=copy_block, height=125)

    if st.button("⚠️ RESET QUOTE"):
        st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS"])
        st.rerun()
