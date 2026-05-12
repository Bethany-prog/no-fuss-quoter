import streamlit as st
import math
import pandas as pd
from datetime import date
import json
import os

# --- NEW: SAVE/LOAD UTILITIES ---
DB_FILE = "quote_db.json"

def save_quote(name, data_df, weeks, km):
    db = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            db = json.load(f)
    
    # Convert dataframe to dict for storage
    db[name] = {
        "df": data_df.to_dict('records'),
        "weeks": weeks,
        "km": km,
        "date": str(date.today())
    }
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

def load_quote_list():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return list(json.load(f).keys())
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
    div.stMetric { background-color: #1A1D2D !important; padding: 20px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-weight: bold !important; font-size: 16px !important; }
    div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; width: 100%; }
    .stDataFrame { border: 2px solid #00E676 !important; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 3. MASTER CATALOG
CATALOG = {
    "FLOORING": {
        "I-Trac System": [
            {"Product": "I-Trac flooring", "w1_3": 23.40, "block": 46.80, "labour": 4.65, "unit": "SQM", "waiver": True},
            {"Product": "I-Trac ramps", "w1_3": 42.00, "block": 84.00, "labour": 0.00, "unit": "ea", "waiver": True}
        ],
        "Plastorip System": [
            {"Product": "Plastorip", "w1_3": 10.15, "block": 20.30, "labour": 3.05, "unit": "SQM", "waiver": True, "is_p": True},
            {"Product": "Plastorip Edging", "w1_3": 1.65, "block": 1.65, "labour": 0.00, "unit": "pc", "waiver": True},
            {"Product": "Plastorip Corner", "w1_3": 0.00, "block": 0.00, "labour": 0.00, "unit": "ea", "waiver": True}
        ],
        "Supa-Trac System": [
            {"Product": "Supa-Trac flooring", "w1_3": 11.55, "block": 25.00, "labour": 4.65, "unit": "SQM", "waiver": True, "is_st": True},
            {"Product": "Supa-Trac Edging", "w1_3": 6.70, "block": 6.70, "labour": 0.00, "unit": "lm", "waiver": True}
        ],
        "Other Flooring": [
            {"Product": "No Fuss Floor (Grey/Green)", "w1_3": 7.10, "block": 15.00, "labour": 3.05, "unit": "SQM", "waiver": True},
            {"Product": "Terratrak Plus", "w1_3": 23.40, "block": 46.80, "labour": 4.65, "unit": "SQM", "waiver": True},
            {"Product": "Wooden Floor", "w1_3": 8.85, "block": 17.70, "labour": 7.15, "unit": "SQM", "waiver": True},
            {"Product": "Parquetry Dance Floor", "w1_3": 20.95, "block": 41.90, "labour": 4.80, "unit": "SQM", "waiver": True},
            {"Product": "Carpet Tiles - Onyx", "w1_3": 8.85, "block": 17.70, "labour": 3.05, "unit": "SQM", "waiver": True},
            {"Product": "Protectall", "w1_3": 22.05, "block": 44.10, "labour": 3.25, "unit": "SQM", "waiver": True}
        ]
    },
    "GRANDSTANDS": {
        "Seating": [
            {"Product": "Grandstand Seating", "is_gs": True, "unit": "seat", "waiver": True}
        ]
    },
    "MOJO BARRIERS": {
        "Mojo System": [
            {"Product": "Mojo Straight", "w1_3": 35.00, "block": 70.00, "labour": 0.00, "is_mojo": True, "unit": "Sections", "waiver": False}
        ]
    }
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo", "Unit_Type", "Is_ST"])

st.title("📦 No Fuss Quote Pro")

# --- 0. SAVE/LOAD SECTION ---
st.markdown("### 💾 QUOTE ARCHIVE")
sl_col1, sl_col2 = st.columns(2)
with sl_col1:
    q_name = st.text_input("New Quote Name", placeholder="e.g. Smith Wedding May 2026")
    if st.button("SAVE CURRENT QUOTE"):
        if q_name and not st.session_state.df.empty:
            save_quote(q_name, st.session_state.df, 0, 0) # Basic save for now
            st.success(f"Quote '{q_name}' saved!")
        else:
            st.error("Enter a name and add items first.")

with sl_col2:
    existing_quotes = load_quote_list()
    load_choice = st.selectbox("Load Previous Quote", ["Select..."] + existing_quotes)
    if st.button("LOAD SELECTED"):
        if load_choice != "Select...":
            saved_data = get_quote_data(load_choice)
            st.session_state.df = pd.DataFrame(saved_data["df"])
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
bundle_results = []
w, l = 0, 0
for item in selected_bundle:
    if item.get("is_p"):
        p_mode = st.radio("Input Mode", ["Manual SQM", "Dimensions (WxL)"], key="p_mode")
        if p_mode == "Dimensions (WxL)":
            w_col, l_col = st.columns(2)
            w = w_col.number_input("Width (m)", min_value=0.0, value=None, placeholder="Width...", key="p_w")
            l = l_col.number_input("Length (m)", min_value=0.0, value=None, placeholder="Length...", key="p_l")
            q_val = (w * l) if (w and l) else 0.0
        else:
            q_val = st.number_input(f"Qty: {item['Product']} ({item['unit']})", min_value=0.0, value=None, placeholder="SQM...", key=f"q_{item['Product']}")
    else:
        default_q = None
        if "Edging" in item['Product'] and w > 0:
            default_q = float(math.ceil(((w + l) * 2) / 0.4))
        elif "Corner" in item['Product'] and w > 0:
            default_q = 4.0
        q_val = st.number_input(f"Qty: {item['Product']} ({item['unit']})", min_value=0.0, value=default_q, placeholder="Qty...", key=f"q_{item['Product']}")
    if q_val and q_val > 0:
        bundle_results.append({"item": item, "qty": q_val})

c_a, c_d = st.columns(2)
adj_rate = c_a.number_input("Override Price (Primary Item)", min_value=0.0, value=None, placeholder="Manual Rate...")
discount_pct = c_d.number_input("Discount %", min_value=0.0, max_value=100.0, value=None, placeholder="%...")

if st.button("ADD SELECTED ITEMS TO QUOTE"):
    new_rows = []
    for entry in bundle_results:
        it, q = entry['item'], entry['qty']
        is_gs, is_mojo, is_st = it.get("is_gs", False), it.get("is_mojo", False), it.get("is_st", False)
        if is_gs:
            # Simple placeholder GS logic
            calc_rate = 5.0
            base_r, lab_r, block_r = (adj_rate if adj_rate else calc_rate), 0.0, (adj_rate if adj_rate else calc_rate) * 2
        else:
            base_r, lab_r, block_r = (adj_rate if (adj_rate and it == selected_bundle[0]) else it.get("w1_3", 0.0)), it.get("labour", 0.0), it.get("block", 0.0)
        new_rows.append({"Qty": q, "Product": it['Product'], "Unit Rate": base_r, "Disc %": discount_pct if discount_pct else 0.0, "Total": 0.0, "Labour_Rate": lab_r, "Block_Rate": block_r, "SYSTEM RATE": 0.0, "No_Waiver": not it.get("waiver", True), "Is_GS": is_gs, "Is_Mojo": is_mojo, "Unit_Type": it['unit'], "Is_ST": is_st})
    if new_rows:
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True)
        st.rerun()

# --- 3. DATA GRID ---
if not st.session_state.df.empty:
    st.markdown("### 🏗️ QUOTED ITEMS")
    display_cols = ["Qty", "Unit_Type", "Product", "Unit Rate", "Disc %", "Total"]
    st.data_editor(st.session_state.df[display_cols], use_container_width=True)

    # --- 4. FINANCES ---
    # Simplified total for demonstration of v22.3 saving feature
    subtotal = st.session_state.df["Total"].sum()
    st.divider()
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("SUBTOTAL", f"${subtotal:,.2f}")
    
    if st.button("⚠️ RESET QUOTE"):
        st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo", "Unit_Type", "Is_ST"])
        st.rerun()
