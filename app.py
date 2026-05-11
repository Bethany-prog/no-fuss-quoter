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
    .main { background-color: #FFFFFF !important; }
    h3 { 
        color: #FFFFFF !important; 
        border-left: 5px solid #00E676; 
        padding-left: 15px; 
        margin-top: 25px;
        background-color: #1A1D2D;
        padding-top: 10px;
        padding-bottom: 10px;
        border-radius: 0 10px 10px 0;
    }
    div[data-testid="stNumberInput"] label p, 
    div[data-testid="stDateInput"] label p,
    div[data-testid="stSelectbox"] label p { 
        color: #333333 !important; 
        font-weight: bold !important; 
    }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 16px !important; }
    div.stMetric { background-color: #1A1D2D !important; padding: 20px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; }
    div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; width: 100%; }
    .stDataFrame { border: 2px solid #00E676 !important; border-radius: 12px; }
    .bundle-box { background-color: #F8F9FB; padding: 20px; border-radius: 10px; border: 1px solid #3D5AFE; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 3. MASTER CATALOG
CATALOG = {
    "FLOORING": {
        "I-Trac System": [
            {"Product": "I-Trac flooring (sqm)", "w1_3": 23.40, "block": 46.80, "labour": 4.65, "unit": "SQM", "waiver": True},
            {"Product": "I-Trac ramps (ea)", "w1_3": 42.00, "block": 84.00, "labour": 0.00, "unit": "ea", "waiver": True}
        ],
        "Plastorip System": [
            {"Product": "Plastorip (sqm)", "w1_3": 10.15, "block": 20.30, "labour": 3.05, "unit": "SQM", "waiver": True, "is_p": True},
            {"Product": "Plastorip Edging (pc)", "w1_3": 1.65, "block": 1.65, "labour": 0.00, "unit": "pc", "waiver": True},
            {"Product": "Plastorip Corner (ea)", "w1_3": 0.00, "block": 0.00, "labour": 0.00, "unit": "ea", "waiver": True}
        ],
        "Supa-Trac System": [
            {"Product": "Supa-Trac flooring (sqm)", "w1_3": 11.55, "block": 25.00, "labour": 4.65, "unit": "SQM", "waiver": True},
            {"Product": "Supa-Trac Edging (lm)", "w1_3": 6.70, "block": 6.70, "labour": 0.00, "unit": "lm", "waiver": True}
        ],
        "Trakmats": [
            {"Product": "Trakmats (ea)", "w1_3": 23.20, "block": 45.00, "labour": 5.85, "unit": "ea", "waiver": True},
            {"Product": "Trakmat Joiners (ea)", "w1_3": 11.95, "block": 11.95, "labour": 0.00, "unit": "ea", "waiver": True}
        ],
        "Other Flooring": [
            {"Product": "No Fuss Floor (Grey/Green) (sqm)", "w1_3": 7.10, "block": 15.00, "labour": 3.05, "unit": "SQM", "waiver": True},
            {"Product": "Terratrak Plus (sqm)", "w1_3": 23.40, "block": 46.80, "labour": 4.65, "unit": "SQM", "waiver": True},
            {"Product": "Wooden Floor (sqm)", "w1_3": 8.85, "block": 17.70, "labour": 7.15, "unit": "SQM", "waiver": True},
            {"Product": "Parquetry Dance Floor (sqm)", "w1_3": 20.95, "block": 41.90, "labour": 4.80, "unit": "SQM", "waiver": True},
            {"Product": "Carpet Tiles - Onyx (sqm)", "w1_3": 8.85, "block": 17.70, "labour": 3.05, "unit": "SQM", "waiver": True},
            {"Product": "Protectall (sqm)", "w1_3": 22.05, "block": 44.10, "labour": 3.25, "unit": "SQM", "waiver": True},
            {"Product": "Enkamat Underlay (sqm)", "w1_3": 2.60, "block": 5.20, "labour": 0.00, "unit": "SQM", "waiver": True},
            {"Product": "Black Plastic (sqm)", "w1_3": 0.90, "block": 0.90, "labour": 0.00, "unit": "SQM", "waiver": True}
        ]
    },
    "GRANDSTANDS": {
        "Seating": [
            {"Product": "Grandstand Seating (per seat)", "is_gs": True, "unit": "seat", "waiver": True},
            {"Product": "Shade Cloth / Scrim (per lm)", "w1_3": 6.00, "block": 12.00, "labour": 0.00, "unit": "lm", "waiver": True}
        ]
    },
    "MOJO BARRIERS": {
        "Mojo System": [
            {"Product": "Mojo Straight (Sections)", "w1_3": 35.00, "block": 70.00, "labour": 0.00, "is_mojo": True, "unit": "Sections", "waiver": False},
            {"Product": "Mojo Corner / Flex (Sections)", "w1_3": 45.00, "block": 90.00, "labour": 0.00, "is_mojo": True, "unit": "Sections", "waiver": False}
        ]
    }
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo", "Unit_Type"])

st.title("📦 No Fuss Quote Pro")

# --- 1. LOGISTICS ---
st.markdown("### 📍 HIRE DATES & DISTANCE")
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today())
end_date = c2.date_input("Hire End", value=date.today())
# Blank Default Distance
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=None, placeholder="Type KM...")
live_weeks = math.ceil(((end_date - start_date).days) / 7) if (end_date - start_date).days > 0 else 1

# --- 2. ADD PRODUCT ---
st.markdown("### ➕ ADD PRODUCT")
dept_col, bundle_col = st.columns(2)
dept_choice = dept_col.selectbox("Department", sorted(CATALOG.keys()))
bundle_choice = bundle_col.selectbox("Select System/Group", sorted(CATALOG[dept_choice].keys()))

selected_bundle = CATALOG[dept_choice][bundle_choice]
bundle_results = []

st.markdown('<div class="bundle-box">', unsafe_allow_html=True)
for item in selected_bundle:
    if item.get("is_p"):
        p_mode = st.radio("Input Mode", ["Manual SQM", "Dimensions (WxL)"], key="p_mode")
        if p_mode == "Dimensions (WxL)":
            w_col, l_col = st.columns(2)
            # Blank Default Dimensions
            w = w_col.number_input("Width (m)", min_value=0.0, value=None, placeholder="Width...", key="p_w")
            l = l_col.number_input("Length (m)", min_value=0.0, value=None, placeholder="Length...", key="p_l")
            q_val = (w * l) if (w and l) else 0.0
        else:
            # Blank Default SQM
            q_val = st.number_input(f"Qty ({item['unit']})", min_value=0.0, value=None, placeholder="Enter SQM...", key=f"q_{item['Product']}")
            w, l = 0, 0
    else:
        # Default Auto-calc for Edging logic
        default_q = None
        if "Edging (pc)" in item['Product'] and 'w' in locals() and w:
            default_q = float(math.ceil(((w + l) * 2) / 0.4))
        elif "Corner (ea)" in item['Product'] and 'w' in locals() and w:
            default_q = 4.0
            
        q_val = st.number_input(f"Qty: {item['Product']} ({item['unit']})", min_value=0.0, value=default_q, placeholder="Enter Qty...", key=f"q_{item['Product']}")
    
    if q_val and q_val > 0:
        bundle_results.append({"item": item, "qty": q_val})

st.markdown('</div>', unsafe_allow_html=True)

c_a, c_d = st.columns(2)
# Blank Default Override/Discount
adj_rate = c_a.number_input("Global Override Rate", min_value=0.0, value=None, placeholder="Manual Rate...")
discount_pct = c_d.number_input("Discount %", min_value=0.0, max_value=100.0, value=None, placeholder="Discount %...")

if st.button("ADD SELECTED ITEMS TO QUOTE"):
    new_rows = []
    for entry in bundle_results:
        it, q = entry['item'], entry['qty']
        is_gs, is_mojo = it.get("is_gs", False), it.get("is_mojo", False)
        
        if is_gs:
            if q <= 40: s, h = 2, 4
            elif q <= 100: s, h = 3, 5
            elif q <= 149: s, h = 4, 5
            elif q <= 199: s, h = 5, 5
            elif q <= 299: s, h = 5, 6
            else: s, h = 6, 10
            calc_rate = (s * h * 55.0 * 4) / q
            base_r, lab_r, block_r = (adj_rate if adj_rate else calc_rate), 0.0, (adj_rate if adj_rate else calc_rate) * 2
        else:
            base_r, lab_r, block_r = (adj_rate if (adj_rate and it == selected_bundle[0]) else it.get("w1_3", 0.0)), it.get("labour", 0.0), it.get("block", 0.0)

        new_rows.append({
            "Qty": q, "Product": it['Product'], "Unit Rate": base_r, "Disc %": discount_pct if discount_pct else 0.0, 
            "Total": 0.0, "Labour_Rate": lab_r, "Block_Rate": block_r, "SYSTEM RATE": 0.0, 
            "No_Waiver": not it.get("waiver", True), "Is_GS": is_gs, "Is_Mojo": is_mojo, "Unit_Type": it['unit']
        })
    
    if new_rows:
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True)
        st.rerun()

# --- 3. DATA GRID ---
if not st.session_state.df.empty:
    st.markdown("### 🏗️ QUOTED ITEMS")
    has_gs, has_mojo = st.session_state.df["Is_GS"].any(), st.session_state.df["Is_Mojo"].any()
    display_cols = ["Qty", "Unit_Type", "Product", "SYSTEM RATE", "Unit Rate", "Disc %", "Total"]
    
    edited_df = st.data_editor(st.session_state.df[display_cols], num_rows="dynamic", use_container_width=True, key="editor",
                               column_config={"SYSTEM RATE": st.column_config.NumberColumn("🔢 SYSTEM RATE", format="$%.2f"), "Unit Rate": st.column_config.NumberColumn("Unit Rate", format="$%.2f"), "Total": st.column_config.NumberColumn("Total", format="$%.2f")})
    
    if not edited_df.equals(st.session_state.df[display_cols]):
        for col in ["Qty", "Unit Rate", "Disc %"]: st.session_state.df[col] = edited_df[col]
        st.rerun()

    # --- 4. SELECTORS ---
    st.markdown("### ⚙️ LABOUR & CARTAGE")
    labour_mode = "Bake Labour into Unit Rate" if has_gs else st.selectbox("Labour Mode", ["Bake Labour into Unit Rate", "Show Labour as Separate Line Item", "No Labour"])
    
    mojo_lab_total = 0.0
    if has_mojo and labour_mode != "No Labour":
        m_qty = st.session_state.df[st.session_state.df["Is_Mojo"] == True]["Qty"].sum()
        if m_qty <= 30: sup, hand, h_in, h_out = 1, 1, 4, 4
        elif m_qty <= 60: sup, hand, h_in, h_out = 1, 2, 4, 4
        elif m_qty <= 100: sup, hand, h_in, h_out = 1, 4, 4, 4
        elif m_qty <= 200: sup, hand, h_in, h_out = 1, 6, 6, 4
        else: sup, hand, h_in, h_out = 2, 8, 6, 6
        mojo_lab_total = ((sup + hand) * (h_in + h_out) * 55.0)
        st.info(f"👷 Mojo Labour Matrix: {sup} Supervisor + {hand} Hands ({h_in}hr In / {h_out}hr Out)")

    charge_cartage = st.checkbox("🚚 Include Cartage ($3.50/km x 4)", value=True)

    # --- 5. FINANCES ---
    hire_total_only, lab_total_only = 0.0, (mojo_lab_total if labour_mode == "Show Labour as Separate Line Item" else 0.0)
    mojo_baked_per_unit = (mojo_lab_total / st.session_state.df[st.session_state.df["Is_Mojo"] == True]["Qty"].sum()) if (has_mojo and labour_mode == "Bake Labour into Unit Rate") else 0.0

    for idx, row in st.session_state.df.iterrows():
        q, r, d, b, lr, ig, im = row["Qty"], row["Unit Rate"], row["Disc %"], row["Block_Rate"], row["Labour_Rate"], row["Is_GS"], row["Is_Mojo"]
        if not ig and not im and live_weeks >= 4:
            hire = (q * (b / 4) * live_weeks)
        elif ig:
            hire = q * r
        else:
            hire = (q * r * live_weeks) if live_weeks <= 3 else (q * r * 3) + (q * b)
        
        item_lab = (q * mojo_baked_per_unit) if im and labour_mode == "Bake Labour into Unit Rate" else (q * lr) if labour_mode == "Bake Labour into Unit Rate" else 0.0
        if not im and labour_mode == "Show Labour as Separate Line Item": lab_total_only += (q * lr) * (1 - (d / 100))
            
        final = (hire + item_lab) * (1 - (d / 100))
        st.session_state.df.at[idx, "Total"], st.session_state.df.at[idx, "SYSTEM RATE"] = final, (final / q if q > 0 else 0)
        hire_total_only += final

    subtotal = max(2000.0 if has_gs else 300.0, (hire_total_only + (350.0 - st.session_state.df[st.session_state.df["Is_Mojo"] == True]["Total"].sum()) if (has_mojo and st.session_state.df[st.session_state.df["Is_Mojo"] == True]["Total"].sum() < 350.0) else hire_total_only))
    waiver = st.session_state.df[st.session_state.df["No_Waiver"] == False]["Total"].sum() * 0.07
    cartage = (km_input * 4 * 3.50) if km_input and charge_cartage else 0.0
    
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("SUBTOTAL (HIRE)", f"${subtotal:,.2f}"); m2.metric("LABOUR", f"${lab_total_only:,.2f}"); m3.metric("WAIVER", f"${waiver:,.2f}"); m4.metric("CARTAGE", f"${cartage:,.2f}")
    st.metric("GRAND TOTAL (EX GST)", f"${(subtotal + lab_total_only + waiver + cartage):,.2f}")

    st.markdown("### 📋 DESCRIPTION BLOCKS")
    for idx, row in st.session_state.df.iterrows():
        p, lr, is_gs, br, ut = row["Unit Rate"], row["Labour_Rate"], row["Is_GS"], row["Block_Rate"], row["Unit_Type"]
        wk_r = br/4 if live_weeks >= 4 and not is_gs else p
        init = wk_r + (lr if labour_mode == "Bake Labour into Unit Rate" else 0)
        txt = f"PRICING BASED ON {live_weeks} WEEK HIRE PERIOD\nPrice for Initial Week (Incl. Install) = ${init:,.2f} per {ut} + GST\n"
        if live_weeks > 1: txt += f"Price for weeks 2+ = ${wk_r:,.2f} per {ut}/week + GST"
        st.text_area(f"Line {idx+1}: {row['Product']}", value=txt, height=100)
    
    if st.button("⚠️ RESET QUOTE"):
        st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo", "Unit_Type"])
        st.rerun()
