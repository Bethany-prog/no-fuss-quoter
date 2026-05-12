import streamlit as st
import math
import pandas as pd
from datetime import date
import json
import os

# --- SAVE/LOAD UTILITIES ---
DB_FILE = "quote_db.json"

def save_quote(name, data_df, start_d, end_d, km):
    db = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                db = json.load(f)
        except: db = {}
    db[name] = {"df": data_df.to_dict('records'), "start": str(start_d), "end": str(end_d), "km": km, "saved_at": str(date.today())}
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

def load_quote_list():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return list(json.load(f).keys())
        except: return []
    return []

def get_quote_data(name):
    with open(DB_FILE, "r") as f:
        return json.load(f)[name]

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
    div[data-testid="stSelectbox"] label p { color: #333333 !important; font-weight: bold !important; }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 16px !important; }
    div.stMetric { background-color: #1A1D2D !important; padding: 20px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; }
    div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; width: 100%; }
    .stDataFrame { border: 2px solid #00E676 !important; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 3. MASTER CATALOG
CATALOG = {
    "FLOORING": {
        "I-Trac System": [
            {"Product": "I-Trac flooring", "w1_3": 23.40, "block": 46.80, "labour": 4.65, "unit": "SQM", "waiver": True},
            {"Product": "I-Trac Ramp", "w1_3": 42.00, "block": 84.00, "labour": 0.00, "unit": "ea", "waiver": True}
        ],
        "Supa-Trac System": [
            {"Product": "Supa-trac flooring", "w1_3": 11.55, "block": 25.00, "labour": 4.65, "unit": "SQM", "waiver": True, "is_st": True},
            {"Product": "Supa-trac Edging", "w1_3": 6.70, "block": 6.70, "labour": 0.00, "unit": "lm", "waiver": False}
        ],
        "Trakmat System": [
            {"Product": "Trakmats", "w1_3": 23.20, "block": 45.00, "labour": 5.85, "unit": "ea", "waiver": True},
            {"Product": "Trakmat Joiners 4 Hole", "w1_3": 11.95, "block": 11.95, "labour": 0.00, "unit": "ea", "waiver": True},
            {"Product": "Trakmat Joiners 2 Hole", "w1_3": 4.40, "block": 4.40, "labour": 0.00, "unit": "ea", "waiver": True}
        ],
        "Plastorip System": [
            {"Product": "Plastorip", "w1_3": 10.15, "block": 20.30, "labour": 3.05, "unit": "SQM", "waiver": True, "is_p": True},
            {"Product": "Plastorip Edging", "w1_3": 1.65, "block": 1.65, "labour": 0.00, "unit": "pc", "waiver": False},
            {"Product": "Plastorip Corners", "w1_3": 0.00, "block": 0.00, "labour": 0.00, "unit": "ea", "waiver": False},
            {"Product": "Plastorip Expansion Joiners", "w1_3": 12.15, "block": 12.15, "labour": 0.00, "unit": "ea", "waiver": False}
        ],
        "No Fuss Floor": [
            {"Product": "No Fuss Floor (Grey/Green)", "w1_3": 7.10, "block": 15.00, "labour": 3.05, "unit": "SQM", "waiver": True},
            {"Product": "Ramp 1M", "w1_3": 6.60, "block": 13.20, "labour": 0.00, "unit": "ea", "waiver": True},
            {"Product": "Expansion Joiner 1.2M", "w1_3": 6.60, "block": 13.20, "labour": 0.00, "unit": "ea", "waiver": True}
        ],
        "Specialty/Protection": [
            {"Product": "Terratrak Plus", "w1_3": 23.40, "block": 46.80, "labour": 4.365, "unit": "SQM", "waiver": True},
            {"Product": "LD20 Roll", "w1_3": 1800.00, "block": 3300.00, "labour": 0.00, "unit": "Roll", "waiver": True},
            {"Product": "Geotextile Underlay", "w1_3": 2.60, "block": 2.60, "labour": 0.00, "unit": "SQM", "waiver": True},
            {"Product": "Black Plastic", "w1_3": 0.90, "block": 0.90, "labour": 0.00, "unit": "SQM", "waiver": True}
        ]
    },
    "MOJO BARRIERS": {
        "Mojo System": [
            {"Product": "Mojo Straight", "w1_3": 35.00, "block": 70.00, "labour": 0.00, "is_mojo": True, "unit": "Sections", "waiver": False},
            {"Product": "Mojo Corner / Flex", "w1_3": 45.00, "block": 90.00, "labour": 0.00, "is_mojo": True, "unit": "Sections", "waiver": False}
        ]
    }
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo", "Unit_Type", "Is_ST"])

st.title("📦 No Fuss Quote Pro")

# --- 0. LOAD ARCHIVE ---
st.markdown("### 📂 LOAD RECENT QUOTES")
existing = load_quote_list()
l_col1, l_col2 = st.columns([3, 1])
load_choice = l_col1.selectbox("Archive History", ["Select..."] + existing, label_visibility="collapsed")
if l_col2.button("LOAD DATA"):
    if load_choice != "Select...":
        saved = get_quote_data(load_choice)
        st.session_state.df = pd.DataFrame(saved["df"])
        st.rerun()

# --- 1. LOGISTICS ---
st.markdown("### 📍 HIRE DATES & DISTANCE")
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=None, placeholder="KM...")
live_weeks = math.ceil(((end_date - start_date).days) / 7) if (end_date - start_date).days > 0 else 1

# --- 2. ADD PRODUCT ---
st.markdown("### ➕ ADD PRODUCT")
dept_col, bundle_col = st.columns(2)
dept_choice = dept_col.selectbox("Department", sorted(CATALOG.keys()))
bundle_choice = bundle_col.selectbox("Select System/Group", sorted(CATALOG[dept_choice].keys()))

selected_bundle = CATALOG[dept_choice][bundle_choice]
bundle_results, w, l = [], 0, 0
for item in selected_bundle:
    if item.get("is_p"):
        p_mode = st.radio("Input Mode", ["Manual SQM", "Dimensions (WxL)"], key="p_mode")
        if p_mode == "Dimensions (WxL)":
            w_col, l_col = st.columns(2)
            w = w_col.number_input("Width (m)", min_value=0.0, value=None, placeholder="Width...", key="p_w")
            l = l_col.number_input("Length (m)", min_value=0.0, value=None, placeholder="Length...", key="p_l")
            q_val = (w * l) if (w and l) else 0.0
        else:
            q_val = st.number_input(f"Qty: {item['Product']} ({item['unit']})", min_value=0.0, value=None, key=f"q_{item['Product']}")
    else:
        default_q = None
        if "Edging" in item['Product'] and w > 0: default_q = float(math.ceil(((w + l) * 2) / 0.4))
        elif "Corner" in item['Product'] and w > 0: default_q = 4.0
        q_val = st.number_input(f"Qty: {item['Product']} ({item['unit']})", min_value=0.0, value=default_q, key=f"q_{item['Product']}")
    if q_val and q_val > 0: bundle_results.append({"item": item, "qty": q_val})

c_a, c_d = st.columns(2)
adj_rate = c_a.number_input("Override Price (Primary Item)", min_value=0.0, value=None)
discount_pct = c_d.number_input("Discount %", min_value=0.0, max_value=100.0, value=None)

if st.button("ADD SELECTED ITEMS TO QUOTE"):
    new_rows = []
    for entry in bundle_results:
        it, q = entry['item'], entry['qty']
        is_gs, is_mojo, is_st = it.get("is_gs", False), it.get("is_mojo", False), it.get("is_st", False)
        base_r, lab_r, block_r = (adj_rate if (adj_rate and it == selected_bundle[0]) else it.get("w1_3", 0.0)), it.get("labour", 0.0), it.get("block", 0.0)
        new_rows.append({"Qty": q, "Product": it['Product'], "Unit Rate": base_r, "Disc %": discount_pct if discount_pct else 0.0, "Total": 0.0, "Labour_Rate": lab_r, "Block_Rate": block_r, "SYSTEM RATE": 0.0, "No_Waiver": not it.get("waiver", True), "Is_GS": is_gs, "Is_Mojo": is_mojo, "Unit_Type": it['unit'], "Is_ST": is_st})
    if new_rows:
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True)
        st.rerun()

# --- 3. QUOTED ITEMS ---
if not st.session_state.df.empty:
    st.markdown("### 🏗️ QUOTED ITEMS")
    # Improved labels to clarify where the $23.20 vs $29.05 comes from
    display_cols = ["Qty", "Unit_Type", "Product", "Unit Rate", "Disc %", "SYSTEM RATE", "Total"]
    edited_df = st.data_editor(st.session_state.df[display_cols], num_rows="dynamic", use_container_width=True, key="editor",
                               column_config={
                                   "Unit Rate": st.column_config.NumberColumn("Hire Rate (Rent Only)", format="$%.2f"), 
                                   "SYSTEM RATE": st.column_config.NumberColumn("Total Rate (Rent + Lab)", format="$%.2f")
                               })
    if not edited_df.equals(st.session_state.df[display_cols]):
        for col in ["Qty", "Unit Rate", "Disc %"]: st.session_state.df[col] = edited_df[col]
        st.rerun()

    st.markdown("### ⚙️ LABOUR & CARTAGE")
    labour_mode = st.selectbox("Labour Mode", ["Bake Labour into Unit Rate", "Show Labour as Separate Line Item", "No Labour"])
    
    mojo_lab, has_mojo = 0.0, st.session_state.df["Is_Mojo"].any()
    if has_mojo and labour_mode != "No Labour":
        m_qty = st.session_state.df[st.session_state.df["Is_Mojo"] == True]["Qty"].sum()
        if m_qty <= 30: sup, hand, h_in, h_out = 1, 1, 4, 4
        elif m_qty <= 60: sup, hand, h_in, h_out = 1, 2, 4, 4
        elif m_qty <= 100: sup, hand, h_in, h_out = 1, 4, 4, 4
        elif m_qty <= 200: sup, hand, h_in, h_out = 1, 6, 6, 4
        else: sup, hand, h_in, h_out = 2, 8, 6, 6
        mojo_lab = ((sup + hand) * (h_in + h_out) * 55.0)

    col_cart, col_waiv = st.columns(2)
    charge_cartage = col_cart.checkbox("🚚 Include Cartage ($3.50/km x 4)", value=True)
    include_damage_waiver = col_waiv.checkbox("🛡️ Include Damage Waiver (7%)", value=True)

    # --- 5. FINANCES ---
    hire_total, lab_total, waiver_total, total_sheets = 0.0, 0.0, 0.0, 0
    m_baked = (mojo_lab / st.session_state.df[st.session_state.df["Is_Mojo"] == True]["Qty"].sum()) if (has_mojo and labour_mode == "Bake Labour into Unit Rate" and st.session_state.df[st.session_state.df["Is_Mojo"] == True]["Qty"].sum() > 0) else 0.0
    if has_mojo and labour_mode == "Show Labour as Separate Line Item": lab_total = mojo_lab

    for idx, row in st.session_state.df.iterrows():
        q, r, d, b, lr, im, ist = row["Qty"], row["Unit Rate"], row["Disc %"], row["Block_Rate"], row["Labour_Rate"], row["Is_Mojo"], row["Is_ST"]
        if ist: total_sheets += math.ceil(q / 3.135)
        hire_val = (q * (b / 4) * live_weeks) if (live_weeks >= 4 and not im) else (q * r * live_weeks)
        hire_disc = hire_val * (1 - (d / 100))
        if include_damage_waiver and not row["No_Waiver"]: waiver_total += hire_disc * 0.07
        item_lab = (q * m_baked) if im and labour_mode == "Bake Labour into Unit Rate" else (q * lr) if labour_mode == "Bake Labour into Unit Rate" else 0.0
        if not im and labour_mode == "Show Labour as Separate Line Item": lab_total += (q * lr) * (1 - (d / 100))
        total_line = hire_disc + (item_lab * (1 - (d / 100)))
        st.session_state.df.at[idx, "Total"], st.session_state.df.at[idx, "SYSTEM RATE"] = total_line, (total_line / q if q > 0 else 0)
        hire_total += total_line

    subtotal = max(300.0, (hire_total + (350.0 - st.session_state.df[st.session_state.df["Is_Mojo"] == True]["Total"].sum()) if (has_mojo and st.session_state.df[st.session_state.df["Is_Mojo"] == True]["Total"].sum() < 350.0) else hire_total))
    cartage = (km_input * 4 * 3.50) if km_input and charge_cartage else 0.0
    st.divider()
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("SUBTOTAL (HIRE)", f"${subtotal:,.2f}"); m_col2.metric("LABOUR", f"${lab_total:,.2f}"); m_col3.metric("WAIVER", f"${waiver_total:,.2f}"); m_col4.metric("CARTAGE", f"${cartage:,.2f}")
    c1, c2 = st.columns(2)
    c1.metric("GRAND TOTAL (EX GST)", f"${(subtotal + lab_total + waiver_total + cartage):,.2f}")
    if total_sheets > 0: c2.metric("TOTAL SHEETS (Supa-Trac)", f"{total_sheets}")

    # --- UPDATED DESCRIPTION BLOCKS ---
    st.markdown("### 📋 DESCRIPTION BLOCKS")
    for idx, row in st.session_state.df.iterrows():
        p, lr, br, ut = row["Unit Rate"], row["Labour_Rate"], row["Block_Rate"], row["Unit_Type"]
        wk_r = br/4 if live_weeks >= 4 else p
        init = wk_r + (lr if labour_mode == "Bake Labour into Unit Rate" else 0)
        
        copy_block = f"PRICING BASED ON {live_weeks} WEEK HIRE PERIOD\n"
        
        # 1-Week simplified logic
        if live_weeks == 1:
            copy_block += f"Price per {ut} = ${init:,.2f} + GST"
        else:
            # Multi-week logic
            if round(init, 2) == round(wk_r, 2):
                copy_block += f"Price per {ut} = ${init:,.2f} + GST"
            else:
                copy_block += f"Price for Initial Week (Incl. Install) = ${init:,.2f} per {ut} + GST\n"
                copy_block += f"Price for weeks 2+ = ${wk_r:,.2f} per {ut}/week + GST"
        
        st.text_area(f"Line {idx+1}: {row['Product']}", value=copy_block, height=100)

    st.markdown("### 💾 FINISH & SAVE")
    save_col1, save_col2 = st.columns([3, 1])
    finish_name = save_col1.text_input("Save finalized quote as:", placeholder="Client Name / Project", key="finish_save")
    if save_col2.button("ARCHIVE QUOTE"):
        if finish_name:
            save_quote(finish_name, st.session_state.df, start_date, end_date, km_input)
            st.success(f"Archived: {finish_name}")
    if st.button("⚠️ RESET ALL"): st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo", "Unit_Type", "Is_ST"]); st.rerun()
