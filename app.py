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
    
    /* Global labels and headers changed to Bold and White for readability */
    label, p, span, .stMarkdown, .stSubheader, .stHeader, h3, h4 {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }
    
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; }
    div.stMetric { background-color: #1A1D2D; padding: 20px; border-radius: 12px; border: 2px solid #3D5AFE; }
    div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; }
    
    [data-testid="stCheckbox"] { background-color: #1A1D2D; padding: 12px; border-radius: 10px; border: 1px solid #3D5AFE; margin-bottom: 8px; }
    [data-testid="stCheckbox"] label p { font-size: 18px !important; font-weight: bold !important; color: #00E676 !important; }
    .stDataFrame { border: 2px solid #00E676 !important; border-radius: 12px; }
    
    /* Dropdown specific label color override if needed */
    div[data-testid="stSelectbox"] label p { color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. MASTER CATALOG
PRODUCT_CATALOG = {
    "FLOORING": {
        "I-Trac flooring (sqm)": {"w1_3": 23.40, "block": 46.80, "labour": 4.65},
        "I-Trac ramps (ea)": {"w1_3": 42.00, "block": 84.00, "labour": 0.00},
        "Supa-Trac flooring (sqm)": {"w1_3": 11.55, "block": 25.00, "labour": 4.65},
        "Supa-Trac Edging (lm)": {"w1_3": 6.70, "block": 6.70, "labour": 0.00},
        "Trakmats (ea)": {"w1_3": 23.20, "block": 45.00, "labour": 5.85},
        "No Fuss Floor (Grey/Green) (sqm)": {"w1_3": 7.10, "block": 15.00, "labour": 3.05},
        "Plastorip (sqm)": {"w1_3": 10.15, "block": 20.30, "labour": 3.05, "is_plastorip": True},
        "Plastorip Expansion Joiner 1m": {"w1_3": 12.15, "block": 12.15, "labour": 0.00}
    },
    "GRANDSTANDS": {
        "Grandstand Seating (per seat)": {"is_gs": True, "labour": 0.00},
        "Shade Cloth / Scrim (per lm)": {"w1_3": 6.00, "block": 12.00, "labour": 0.00}
    },
    "MOJO BARRIERS": {
        # Changed '1m Bay' to 'Sections' to match Inventory/Labour guide terminology
        "Mojo Straight (Sections)": {"w1_3": 35.00, "block": 70.00, "labour": 8.50, "is_mojo": True},
        "Mojo Corner / Flex (Sections)": {"w1_3": 45.00, "block": 90.00, "labour": 12.00, "is_mojo": True}
    }
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo"])

st.title("📦 No Fuss Quote Pro")

# --- 1. LOGISTICS ---
st.markdown("### 📍 HIRE DATES & DISTANCE")
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=None, placeholder="Type KM...")
live_weeks = math.ceil(((end_date - start_date).days) / 7) if (end_date - start_date).days > 0 else 1

# --- 2. ADD PRODUCT ---
st.markdown("### ➕ ADD PRODUCT")
dept_col, item_col = st.columns(2)
dept_choice = dept_col.selectbox("Department", sorted(PRODUCT_CATALOG.keys()))
item_choice = item_col.selectbox("Product", sorted(PRODUCT_CATALOG[dept_choice].keys()))

# Special Layouts
ref_current = PRODUCT_CATALOG[dept_choice][item_choice]
is_p_sqm = ref_current.get("is_plastorip", False)
w, l = 0.0, 0.0

if is_p_sqm:
    p_col1, p_col2, p_col3 = st.columns([2, 2, 2])
    p_mode = p_col1.radio("Input Mode", ["Manual SQM", "Dimensions (WxL)"])
    if p_mode == "Dimensions (WxL)":
        w = p_col2.number_input("Width (m)", min_value=0.1)
        l = p_col3.number_input("Length (m)", min_value=0.1)
        qty_in = w * l
    else:
        qty_in = p_col2.number_input("Total SQM```python
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
    
    /* Global labels and headers changed to Bold and White for readability */
    label, p, span, .stMarkdown, .stSubheader, .stHeader, h3, h4 {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }
    
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-size: 32px !important; font-weight: bold !important; }
    div.stMetric { background-color: #1A1D2D; padding: 20px; border-radius: 12px; border: 2px solid #3D5AFE; }
    div.stButton > button:first-child { background-color: #3D5AFE; color: white; border-radius: 10px; height: 50px; font-weight: bold; }
    
    [data-testid="stCheckbox"] { background-color: #1A1D2D; padding: 12px; border-radius: 10px; border: 1px solid #3D5AFE; margin-bottom: 8px; }
    [data-testid="stCheckbox"] label p { font-size: 18px !important; font-weight: bold !important; color: #00E676 !important; }
    .stDataFrame { border: 2px solid #00E676 !important; border-radius: 12px; }
    
    /* Dropdown specific label color override if needed */
    div[data-testid="stSelectbox"] label p { color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. MASTER CATALOG
PRODUCT_CATALOG = {
    "FLOORING": {
        "I-Trac flooring (sqm)": {"w1_3": 23.40, "block": 46.80, "labour": 4.65},
        "I-Trac ramps (ea)": {"w1_3": 42.00, "block": 84.00, "labour": 0.00},
        "Supa-Trac flooring (sqm)": {"w1_3": 11.55, "block": 25.00, "labour": 4.65},
        "Supa-Trac Edging (lm)": {"w1_3": 6.70, "block": 6.70, "labour": 0.00},
        "Trakmats (ea)": {"w1_3": 23.20, "block": 45.00, "labour": 5.85},
        "No Fuss Floor (Grey/Green) (sqm)": {"w1_3": 7.10, "block": 15.00, "labour": 3.05},
        "Plastorip (sqm)": {"w1_3": 10.15, "block": 20.30, "labour": 3.05, "is_plastorip": True},
        "Plastorip Expansion Joiner 1m": {"w1_3": 12.15, "block": 12.15, "labour": 0.00}
    },
    "GRANDSTANDS": {
        "Grandstand Seating (per seat)": {"is_gs": True, "labour": 0.00},
        "Shade Cloth / Scrim (per lm)": {"w1_3": 6.00, "block": 12.00, "labour": 0.00}
    },
    "MOJO BARRIERS": {
        # Changed '1m Bay' to 'Sections' to match Inventory/Labour guide terminology
        "Mojo Straight (Sections)": {"w1_3": 35.00, "block": 70.00, "labour": 8.50, "is_mojo": True},
        "Mojo Corner / Flex (Sections)": {"w1_3": 45.00, "block": 90.00, "labour": 12.00, "is_mojo": True}
    }
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo"])

st.title("📦 No Fuss Quote Pro")

# --- 1. LOGISTICS ---
st.markdown("### 📍 HIRE DATES & DISTANCE")
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
end_date = c2.date_input("Hire End", value=date.today(), format="DD/MM/YYYY")
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=None, placeholder="Type KM...")
live_weeks = math.ceil(((end_date - start_date).days) / 7) if (end_date - start_date).days > 0 else 1

# --- 2. ADD PRODUCT ---
st.markdown("### ➕ ADD PRODUCT")
dept_col, item_col = st.columns(2)
dept_choice = dept_col.selectbox("Department", sorted(PRODUCT_CATALOG.keys()))
item_choice = item_col.selectbox("Product", sorted(PRODUCT_CATALOG[dept_choice].keys()))

# Special Layouts
ref_current = PRODUCT_CATALOG[dept_choice][item_choice]
is_p_sqm = ref_current.get("is_plastorip", False)
w, l = 0.0, 0.0

if is_p_sqm:
    p_col1, p_col2, p_col3 = st.columns([2, 2, 2])
    p_mode = p_col1.radio("Input Mode", ["Manual SQM", "Dimensions (WxL)"])
    if p_mode == "Dimensions (WxL)":
        w = p_col2.number_input("Width (m)", min_value=0.1)
        l = p_col3.number_input("Length (m)", min_value=0.1)
        qty_in = w * l
    else:
        qty_in = p_col2.number_input("Total SQM", min_value=0.0)
    
    # Tick box options for Plastorip Accessories
    st.markdown("#### Plastorip Accessories")
    ac_col1, ac_col2 = st.columns(2)
    add_p_edges = ac_col1.checkbox("Add Edging (Automatic Calculation)", value=True)
    add_p_corners = ac_col2.checkbox("Add Corners (4pcs - Free)", value=True)
else:
    # Changed placeholder to reflect the unit (sqm or sections) based on product
    place_text = ref_current.get("input_label", "Qty...")
    qty_in = st.number_input(f"Total Quantity ({place_text})", min_value=0.0, value=None, placeholder=place_text)
    add_p_edges, add_p_corners = False, False

c_a, c_d = st.columns(2)
adj_rate = c_a.number_input("Override Rate", min_value=0.0, value=None)
discount_pct = c_d.number_input("Discount %", min_value=0.0, max_value=100.0, value=None)

if st.button("ADD TO QUOTE ENGINE"):
    if qty_in and qty_in > 0:
        ref = PRODUCT_CATALOG[dept_choice][item_choice]
        is_gs = ref.get("is_gs", False)
        is_mojo = ref.get("is_mojo", False)
        
        # Grandstand Logic
        if is_gs:
            if qty_in <= 40: s, h = 2, 4
            elif qty_in <= 100: s, h = 3, 5
            elif qty_in <= 149: s, h = 4, 5
            elif qty_in <= 199: s, h = 5, 5
            elif qty_in <= 299: s, h = 5, 6
            else: s, h = 6, 10
            calc_rate = (s * h * 55.0 * 4) / qty_in
            base_r, lab_r, block_r = (adj_rate if adj_rate else calc_rate), 0.0, (adj_rate if adj_rate else calc_rate) * 2
        else:
            base_r, lab_r, block_r = (adj_rate if adj_rate else ref["w1_3"]), ref["labour"], ref["block"]

        new_items = [{"Qty": qty_in, "Product": item_choice, "Unit Rate": base_r, "Disc %": discount_pct if discount_pct else 0.0, "Total": 0.0, "Labour_Rate": lab_r, "Block_Rate": block_r, "SYSTEM RATE": 0.0, "No_Waiver": False, "Is_GS": is_gs, "Is_Mojo": is_mojo}]

        # Auto-Add Edging & Corners
        if is_p_sqm:
            if add_p_edges:
                edge_qty = math.ceil(((w + l) * 2) / 0.4) if (w > 0 and l > 0) else 0
                if edge_qty > 0:
                    # Pulling edging rate from catalog, keeping discount consistent
                    new_items.append({"Qty": edge_qty, "Product": "Plastorip Edging (pc)", "Unit Rate": 1.65, "Disc %": discount_pct if discount_pct else 0.0, "Total": 0.0, "Labour_Rate": 0.0, "Block_Rate": 1.65, "SYSTEM RATE": 0.0, "No_Waiver": False, "Is_GS": False, "Is_Mojo": False})
            if add_p_corners:
                new_items.append({"Qty": 4, "Product": "Plastorip Corner (ea)", "Unit Rate": 0.00, "Disc %": 0.0, "Total": 0.0, "Labour_Rate": 0.0, "Block_Rate": 0.0, "SYSTEM RATE": 0.0, "No_Waiver": False, "Is_GS": False, "Is_Mojo": False})
        
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_items)], ignore_index=True)
        st.rerun()

# --- 3. QUOTED ITEMS TABLE ---
if not st.session_state.df.empty:
    st.markdown("### 🏗️ QUOTED ITEMS")
    has_gs = st.session_state.df["Is_GS"].any()
    has_mojo = st.session_state.df["Is_Mojo"].any()

    # Data Editor with Cents formatting
    edited_df = st.data_editor(st.session_state.df[["Qty", "Product", "SYSTEM RATE", "Unit Rate", "Disc %", "Total"]], num_rows="dynamic", use_container_width=True, key="editor",
                               column_config={
                                   "SYSTEM RATE": st.column_config.NumberColumn("🔢 SYSTEM RATE", format="$%.2f"),
                                   "Unit Rate": st.column_config.NumberColumn("Unit Rate* **Department selection:** Filters the product list.
* **Specialized calculations:** For grandstands (labour x4 divided by seats) and Plastorip (dimension to SQM + auto-add edging/corners).
* **Minimum charges:** Hardcoded $2,000 for Grandstands and now $350 for Mojo Barriers.
* **Workflow selectors:** Toggles for labour, cartage, and engineering sign-off located below the quote table.
* **Description blocks:** Intelligent generation of text for the 1-3 week period, handling flat rates and dash notation.
