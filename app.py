import streamlit as st
import math
import pandas as pd
from datetime import date, datetime
from fpdf import FPDF
import re
import json
import os

# --- PERSISTENT CONFIG LOADING ---
CONFIG_FILE = "master_config.json"

DEFAULT_PRODUCTS = [
    {"Category": "Flooring", "Product": "I-Trac®", "Weekly": 23.40, "Block": 46.80, "Lab_Fix": 4.65, "KG": 15.0},
    {"Category": "Flooring", "Product": "Supa-Trac®", "Weekly": 11.55, "Block": 25.00, "Lab_Fix": 4.65, "KG": 4.5},
    {"Category": "Flooring", "Product": "Trakmat", "Weekly": 22.05, "Block": 44.10, "Lab_Fix": 5.00, "KG": 35.0},
    {"Category": "Barriers", "Product": "MOJO Barrier", "Weekly": 70.00, "Block": 0.0, "Lab_Fix": 28.00, "KG": 60.0},
    {"Category": "Accessories", "Product": "30kg Weights", "Weekly": 6.60, "Block": 0.0, "Lab_Fix": 1.65, "KG": 30.0},
]

# Load or Create Config
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        saved_config = json.load(f)
        MASTER_CATALOG = pd.DataFrame(saved_config["catalog"])
        GLOBAL_LOGIC = saved_config["logic"]
else:
    MASTER_CATALOG = pd.DataFrame(DEFAULT_PRODUCTS)
    GLOBAL_LOGIC = {"km_rate": 3.50, "waiver_pct": 7.0, "payload_kg": 6000}

# 1. ACCESS CONTROL
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        st.title("🔒 Louis Quoting Tool Access")
        password = st.text_input("Access Code", type="password")
        if st.button("Unlock Engine"):
            if password == "NoFuss2026":
                st.session_state.password_correct = True
                st.rerun()
        return False
    return True

if not check_password():
    st.stop()

# --- STYLING ---
st.set_page_config(page_title="Louis Master Quoter", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #F4F7F9 !important; }
    h1 { color: #1A1D2D !important; font-size: 42px !important; font-weight: 900 !important; }
    .gt-banner { background: #1A1D2D; color: #00E676; padding: 30px; border-radius: 20px; text-align: right; font-size: 40px !important; font-weight: 900; border: 5px solid #00E676; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ADMIN PANEL ---
with st.sidebar:
    st.title("🛠️ ADMIN DASHBOARD")
    with st.expander("💰 UPDATE PRODUCT CATALOG"):
        edited_catalog = st.data_editor(MASTER_CATALOG, num_rows="dynamic", use_container_width=True, key="catalog_editor")
        
    with st.expander("⚙️ LOGISTICS & GLOBAL RATES"):
        g_km = st.number_input("KM Rate ($)", value=GLOBAL_LOGIC["km_rate"])
        g_wav = st.number_input("Waiver (%)", value=GLOBAL_LOGIC["waiver_pct"])
        g_pay = st.number_input("Truck Payload (KG)", value=GLOBAL_LOGIC["payload_kg"])
    
    if st.button("💾 SAVE GLOBAL SETTINGS"):
        new_config = {
            "catalog": edited_catalog.to_dict(orient="records"),
            "logic": {"km_rate": g_km, "waiver_pct": g_wav, "payload_kg": g_pay}
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(new_config, f)
        st.success("Master Rates Updated!")
        st.rerun()

    st.divider()
    st.title("📁 PROJECT ARCHIVE")
    # ... (Archive Load/Save code remains standard here)

# --- WORKSPACE ---
st.title("⚡ Louis Master Quoter")

# (Input logic for Start/End Dates and One-Way KM)
c1, c2, c3 = st.columns(3)
st.session_state.start_d = c1.date_input("Start", value=date.today())
st.session_state.end_d = c2.date_input("End", value=date.today())
st.session_state.km = c3.number_input("One-Way KM", min_value=0.0, value=0.0)

weeks = math.ceil(((st.session_state.end_d - st.session_state.start_d).days) / 7) or 1

# --- DYNAMIC PRODUCT PICKER ---
st.divider()
st.markdown("### 🪵 ADD PRODUCTS")
cat_filter = st.selectbox("Category", MASTER_CATALOG["Category"].unique())
prod_options = MASTER_CATALOG[MASTER_CATALOG["Category"] == cat_filter]
p_sel = st.selectbox("Select Product", prod_options["Product"])

p_qty = st.number_input("Quantity", min_value=0.0, value=0.0)

if st.button("Add to Quote") and p_qty > 0:
    row = prod_options[prod_options["Product"] == p_sel].iloc[0]
    
    # Block Rate Logic
    is_block = weeks >= 4 and row["Block"] > 0
    final_rate = row["Block"] / 4 if is_block else row["Weekly"]
    
    new_item = {
        "Qty": p_qty,
        "Product": p_sel,
        "Unit Rate": final_rate,
        "Raw_Lab": p_qty * row["Lab_Fix"],
        "KG": p_qty * row["KG"],
        "Discount": 0.0
    }
    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_item])], ignore_index=True)
    st.rerun()

# --- QUOTE SUMMARY ---
if not st.session_state.df.empty:
    st.divider()
    st.subheader("📝 QUOTE SUMMARY")
    # (Display Table & Calculations as per previous stable version)
    
    # Calculate Totals using GLOBAL_LOGIC
    trks = math.ceil(st.session_state.df["KG"].sum() / GLOBAL_LOGIC["payload_kg"]) or 1
    crt = trks * st.session_state.km * 4 * GLOBAL_LOGIC["km_rate"]
    # ...
