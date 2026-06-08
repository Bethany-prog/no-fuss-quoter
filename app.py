import streamlit as st
import math
import pandas as pd
from datetime import date, datetime, timedelta
from fpdf import FPDF
import re
import json
import os
import io  # Streamlines memory buffers for native Excel and PDF exports
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# ==============================================================================
# 0. INITIAL GLOBAL CONFIG & LOCAL CLOUD VAULT ARCHITECTURE
# ==============================================================================
st.set_page_config(page_title="Louis Master Quoter", layout="wide")

VAULT_DIR = "cloud_vault"
CATALOG_FILE = "master_catalog.csv"

if not os.path.exists(VAULT_DIR):
    os.makedirs(VAULT_DIR)

# SOURCE FACTORY DEPOT LOCK: 9 Battery Crt, Cranbourne West VIC 3977
DEPOT_LAT = -38.1171
DEPOT_LON = 145.2442

# ==============================================================================
# DATAFRAME PARSING ENGINE: Dynamic linkage to your uploaded marquee testing data
# ==============================================================================
@st.cache_data(ttl=30)  # Re-evaluates for file updates every 30 seconds
def load_external_catalog():
    if os.path.exists(CATALOG_FILE):
        try:
            cat_df = pd.read_csv(CATALOG_FILE)
            # Remove any trailing whitespaces from configuration strings
            if "Configuration" in cat_df.columns:
                cat_df["Configuration"] = cat_df["Configuration"].astype(str).str.strip()
            return cat_df
        except Exception as e:
            st.error(f"Catalog Parse Failure: {str(e)}")
            return None
    return None

catalog_db = load_external_catalog()

def get_item_property(config_name, column_target, fallback_val=0.0):
    if catalog_db is not None:
        matched_row = catalog_db[catalog_db["Configuration"] == str(config_name).strip()]
        if not matched_row.empty:
            val = matched_row.iloc[0].get(column_target, fallback_val)
            try:
                return float(val) if not pd.isna(val) else fallback_val
            except:
                return val if not pd.isna(val) else fallback_val
    return fallback_val

# ==============================================================================
# 1. ACCESS CONTROL TOWER (SECURITY GATE)
# ==============================================================================
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

# ==============================================================================
# 3. PDF AUDIT ENGINE (STRUCTURAL TABLE TIERS WITH UNIVERSAL BYTE STREAM FIX)
# ==============================================================================
def clean_text(txt):
    if not txt: return ""
    replacements = {"®": "(R)", "™": "(TM)", "©": "(C)", "└": "->", "—": "-", "–": "-"}
    cleaned = str(txt)
    for char, rep in replacements.items():
        cleaned = cleaned.replace(char, rep)
    return cleaned.encode('latin-1', 'replace').decode('latin-1')

def create_calculation_pdf(name, subtotal, labour, waiver, cartage, grand, weeks, start, end, items_list, structural_math_dict, status):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text("Louis Quoting Tool - Detailed Calculation Audit"), ln=True, align="C")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, clean_text(f"PROJECT: {name} | STATUS: {status.upper()}"), ln=True, align="C")
    pdf.cell(0, 7, f"PERIOD: {start.strftime('%d/%m/%Y')} to {end.strftime('%d/%m/%Y')} ({weeks} Week(s))", ln=True, align="C")
    pdf.ln(8)

    # Section 1: Structured Hire Grid Schedule
    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, " 1. HIRE CALCULATIONS SCHEDULE", 0, 1, "L", True)
    
    pdf.set_fill_color(240, 242, 245); pdf.set_text_color(50, 50, 50); pdf.set_font("Arial", "B", 9)
    col_w = [85, 20, 28, 22, 35]
    
    pdf.cell(col_w[0], 8, " Item Description", 1, 0, "L", True)
    pdf.cell(col_w[1], 8, "Qty", 1, 0, "C", True)
    pdf.cell(col_w[2], 8, "Unit Rate Used", 1, 0, "R", True)
    pdf.cell(col_w[3], 8, "Disc %", 1, 0, "C", True)
    pdf.cell(col_w[4], 8, "Weekly Total", 1, 1, "R", True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    
    for item in items_list:
        dm = (1 - (item.get('Discount', 0.0)/100))
        display_unit_rate = item.get('Override_Rate', 0.0) if item.get('Override_Rate', 0.0) > 0 else item['Unit Rate']
        w1_total = (item['Qty'] * display_unit_rate) * dm
        prod_label = item['Product']
        if item.get('Override_Rate', 0.0) > 0:
            prod_label += f" [Book Price: ${item['Unit Rate']:,.2f}]"
        if 'Anchoring' in item and item['Anchoring']:
            prod_label += f" ({item['Anchoring']})"
            
        pdf.cell(col_w[0], 8, clean_text(f" {prod_label} (Wk 1 Base)"), 1, 0, "L")
        pdf.cell(col_w[1], 8, f"{item['Qty']:,.0f}", 1, 0, "C")
        pdf.cell(col_w[2], 8, f"${display_unit_rate:,.2f}", 1, 0, "R")
        pdf.cell(col_w[3], 8, f"{item.get('Discount', 0.0):.1f}%", 1, 0, "C")
        pdf.cell(col_w[4], 8, f"${w1_total:,.2f}", 1, 1, "R")
        
        if weeks > 1:
            r_rate = display_unit_rate * 0.5 if item['Is_Marquee'] else display_unit_rate
            r_total = (item['Qty'] * r_rate * (weeks-1)) * dm
            
            pdf.cell(col_w[0], 8, clean_text(f"   └ Recurring Hire (x{weeks-1} wks)"), 1, 0, "L")
            pdf.cell(col_w[1], 8, f"{item['Qty']:,.0f}", 1, 0, "C")
            pdf.cell(col_w[2], 8, f"${r_rate:,.2f}", 1, 0, "R")
            pdf.cell(col_w[3], 8, f"{item.get('Discount', 0.0):.1f}%", 1, 0, "C")
            pdf.cell(col_w[4], 8, f"${r_total:,.2f}", 1, 1, "R")

    # Section 2: Pure Calculation Sections
    pdf.ln(5)
    categories = ["LABOUR", "LOGISTICS", "DAMAGE WAIVER"]
    for cat in categories:
        if cat in structural_math_dict and structural_math_dict[cat]:
            pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 9, f" {cat}", 0, 1, "L", True)
            pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 10)
            for line in structural_math_dict[cat]:
                pdf.cell(0, 7, clean_text(f" {line}"), border="B", ln=True)
            pdf.ln(3)

    pdf.ln(5); pdf.set_fill_color(0, 230, 118); pdf.set_text_color(26, 29, 45); pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 14, f" GRAND TOTAL (EX GST): ${grand:,.2f} ", 0, 1, "R", True)
    
    try:
        raw_pdf_data = pdf.output(dest='S')
        if isinstance(raw_pdf_data, str):
            return raw_pdf_data.encode('latin-1', 'replace')
        return bytes(raw_pdf_data)
    except:
        return bytes(pdf.output())

STAGES = ["Quoted", "Accepted", "Paid", "On Hire", "Returned", "Cancelled"]
STAGE_COLORS = {"Quoted": "#FF9100", "Accepted": "#00E676", "Paid": "#00B8D4", "On Hire": "#D500F9", "Returned": "#757575", "Cancelled": "#263238"}

# ==============================================================================
# 5. STREAMLIT INTERNAL STORAGE PERSISTENCE
# ==============================================================================
if 'df' not in st.session_state: 
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount", "Lab_Math", "Lab_Per_Unit", "Base_Hire", "Anchoring", "Override_Rate"])
if 'status' not in st.session_state: st.session_state.status = "Quoted"
if 'proj' not in st.session_state: st.session_state.proj = "New Project"
if 'km' not in st.session_state: st.session_state.km = 0.0
if 'truck_override' not in st.session_state: st.session_state.truck_override = 0
if 'start_date_val' not in st.session_state: st.session_state.start_date_val = date.today()
if 'reset_key_seed' not in st.session_state: st.session_state.reset_key_seed = 0
if 'active_filename' not in st.session_state: st.session_state.active_filename = ""
if 'rename_mode' not in st.session_state: st.session_state.rename_mode = False
if 'site_address_str' not in st.session_state: st.session_state.site_address_str = ""

if 'saved_cartage_mode' not in st.session_state: st.session_state.saved_cartage_mode = "Charge"
if 'saved_labour_mode' not in st.session_state: st.session_state.saved_labour_mode = "Separate"
if 'saved_waiver_mode' not in st.session_state: st.session_state.saved_waiver_mode = "Charge"
if 'overrides_dict' not in st.session_state: st.session_state.overrides_dict = {}

def pull_vault_archive_list():
    try:
        return sorted([f.replace(".json", "") for f in os.listdir(VAULT_DIR) if f.endswith(".json")])
    except: return []

def load_project_from_vault(label_name):
    try:
        with open(f"{VAULT_DIR}/{label_name}.json", "r") as f:
            d = json.load(f)
            st.session_state.status = d.get("status", "Quoted")
            st.session_state.proj = str(d.get("proj", label_name)).strip()
            st.session_state.active_filename = str(d.get("proj", label_name)).strip()
            st.session_state.rename_mode = False
            st.session_state.km = float(d.get("km", 0.0))
            st.session_state.truck_override = int(d.get("truck_override", 0))
            st.session_state.site_address_str = d.get("site_address", "")
            st.session_state.saved_cartage_mode = d.get("cartage_mode", "Charge")
            st.session_state.saved_labour_mode = d.get("labour_mode", "Separate")
            st.session_state.saved_waiver_mode = d.get("waiver_mode", "Charge")
            st.session_state.overrides_dict = d.get("overrides_dict", {})
            st.session_state.df = pd.DataFrame(d.get("items", []))
            st.session_state.reset_key_seed += 1
            st.rerun()
    except Exception as e: st.error(f"Vault Load Failure: {str(e)}")

# ==============================================================================
# 7. MAIN INTERFACE WORKSPACE MOUNTING MATRIX
# ==============================================================================
vault_jobs = pull_vault_archive_list()

st.sidebar.title("📁 PROJECT ARCHIVE")
if st.sidebar.button("➕ START NEW", use_container_width=True):
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount", "Lab_Math", "Lab_Per_Unit", "Base_Hire", "Anchoring", "Override_Rate"])
    st.session_state.km, st.session_state.truck_override, st.session_state.proj = 0.0, 0, "New Project"
    st.session_state.active_filename, st.session_state.rename_mode, st.session_state.status = "", False, "Quoted"
    st.session_state.site_address_str, st.session_state.overrides_dict = "", {}
    st.session_state.reset_key_seed += 1
    st.rerun()

if vault_jobs:
    load_choice = st.sidebar.selectbox("Stored Projects", ["-- Choose Project --"] + vault_jobs)
    if st.sidebar.button("📂 LOAD PROJECT") and load_choice != "-- Choose Project --":
        load_project_from_vault(load_choice)

# CORE ROUTING DISTANCE TIERS
st.markdown(f"### 📍 Active Workspace: {st.session_state.proj}")
st.session_state.status = st.selectbox("Stage", STAGES, index=STAGES.index(st.session_state.status) if st.session_state.status in STAGES else 0)
st.markdown(f"<div style='height: 14px; background-color: {STAGE_COLORS[st.session_state.status]}; border-radius: 6px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
start_d = c1.date_input("Start Date", value=st.session_state.start_date_val, key=f"sd_{st.session_state.reset_key_seed}")
st.session_state.start_date_val = start_d
end_d = c2.date_input("End Date", value=start_d, key=f"ed_{st.session_state.reset_key_seed}")
weeks = math.ceil(((end_d - start_d).days) / 7) or 1

input_addr = c3.text_input("🏠 Delivery Site Address", value=st.session_state.site_address_str, placeholder="Type full address or suburb...")
if input_addr.strip() != st.session_state.site_address_str:
    st.session_state.site_address_str = input_addr.strip()
    try:
        geolocator = Nominatim(user_agent="louis_quoter_v55", timeout=5)
        loc_data = geolocator.geocode(input_addr.strip() + ", Victoria, Australia")
        if loc_data:
            st.session_state.km = round(geodesic((DEPOT_LAT, DEPOT_LON), (loc_data.latitude, loc_data.longitude)).kilometers * 1.15, 1)
            st.toast(f"📍 Location verified: {st.session_state.km} KM", icon="✅")
            st.rerun()
    except: pass

st.markdown("**🚛 Active Routing Distance**")
c_km1, c_km2 = st.columns([1, 4])
new_manual_km = c_km1.number_input("One-Way KM", min_value=0.0, value=float(st.session_state.km))
if new_manual_km != float(st.session_state.km):
    st.session_state.km = new_manual_km
c_km2.info(f"Routing calculations locked at **{st.session_state.km} One-Way KM** from Cranbourne West depot.")

# Multi-Segment Toggle Rules
l1, l2, l3 = st.columns(3)
cartage_mode = l1.segmented_control("Cartage Math", ["Charge", "Free"], default=st.session_state.saved_cartage_mode)
labour_mode = l2.segmented_control("Labour Math", ["Separate", "Include in Hire", "Free"], default=st.session_state.saved_labour_mode)
waiver_mode = l3.segmented_control("Damage Waiver", ["Charge", "Free"], default=st.session_state.saved_waiver_mode)

st.divider(); col1, col2 = st.columns(2)
with col1:
    st.markdown("### ⚡ Dynamic Configuration Catalog")
    if catalog_db is not None:
        options_list = catalog_db["Configuration"].tolist()
        selected_item = st.selectbox("Select Structure Size / Component", options_list)
        qty_input = st.number_input("Quantity", min_value=1, value=1)
        anchoring_type = st.segmented_control("Anchoring Method", ["Pegged", "Weighted"], default="Pegged")
        
        if st.button("Add Item Configuration") and selected_item:
            b_hire = get_item_property(selected_item, "Hire_Unit_Rate")
            b_type = get_item_property(selected_item, "Type")
            b_is_marquee = (str(b_type).lower() in ["marquee", "structure"])
            
            # Extract weight parameters natively
            total_w = get_item_property(selected_item, "Total_Weight", 0.0)
            if total_w <= 0:
                area = get_item_property(selected_item, "Area", 0.0)
                total_w = (area * 15.0) if b_is_marquee else 0.0
                
            raw_labour_pool = get_item_property(selected_item, "Labour_Total", 0.0)
            if raw_labour_pool <= 0:
                raw_labour_pool = b_hire * get_item_property(selected_item, "Labour_Rate", 0.40)

            new_df = pd.DataFrame([{
                "Qty": qty_input, "Product": selected_item, "Unit Rate": b_hire, "Min_Lab": 350,
                "Raw_Lab": raw_lab_pool * qty_input, "Lab_Math": f"{selected_item}: Base Matrix allocation applied",
                "KG": total_w * qty_input, "Is_Marquee": b_is_marquee, "Discount": 0.0, "Lab_Per_Unit": raw_lab_pool,
                "Base_Hire": b_hire, "Anchoring": anchoring_type if b_is_marquee else "", "Override_Rate": 0.0
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
            
            # Automate weight addition links if weighted anchoring signature is triggered
            if b_is_marquee and anchoring_type == "Weighted":
                num_weights = get_item_property(selected_item, "Total_Number_of_weights", 0.0)
                w_size = get_item_property(selected_item, "Weight_Size", 30.0)
                w_cost = get_item_property(selected_item, "Cost_per_weight", 6.60)
                w_lab = get_item_property(selected_item, "Labour_Per_Weight", 1.65)
                
                calculated_weights = int(num_weights * qty_input) if num_weights > 0 else 16
                
                weight_item_df = pd.DataFrame([{
                    "Qty": calculated_weights, "Product": f"{int(w_size)}kg Weights", "Unit Rate": w_cost, "Min_Lab": 0,
                    "Raw_Lab": calculated_weights * w_lab, "Lab_Math": f"{w_size}kg Weights: {calculated_weights} units x ${w_lab:.2f}",
                    "KG": calculated_weights * w_size, "Is_Marquee": False, "Discount": 0.0, "Lab_Per_Unit": w_lab,
                    "Base_Hire": w_cost, "Anchoring": "", "Override_Rate": 0.0
                }])
                st.session_state.df = pd.concat([st.session_state.df, weight_item_df], ignore_index=True)
            st.rerun()
    else:
        st.info("Please upload your 'master_catalog.csv' data file to GitHub to use the dropdown selector interface.")

with col2:
    st.markdown("### 🪵 Core Flooring Components")
    f_sel = st.selectbox("Flooring Selection Options", list(FLOORING_CATALOG.keys()))
    f_qty = st.number_input("Square Metre Coverage Count", min_value=1.0)
    if st.button("Add Flooring Component") and f_qty:
        fd = FLOORING_CATALOG[f_sel]
        base_h = fd['block'] if (weeks >= 4 and fd.get('block', 0) > 0) else fd['rate']
        new_f_df = pd.DataFrame([{
            "Qty": f_qty, "Product": f_sel, "Unit Rate": base_h, "Min_Lab": 0, "Raw_Lab": f_qty * fd['lab_fix'],
            "Lab_Math": f"{f_sel}: {f_qty:,.0f} sqm x ${fd['lab_fix']:.2f}", "KG": f_qty * fd['kg'], "Is_Marquee": False,
            "Discount": 0.0, "Lab_Per_Unit": 0, "Base_Hire": base_h, "Anchoring": "", "Override_Rate": 0.0
        }])
        st.session_state.df = pd.concat([st.session_state.df, new_f_df], ignore_index=True)
        st.rerun()

# ==============================================================================
# 8. LIVE DATA SCHEDULE BUILDER ZONE
# ==============================================================================
if st.session_state.df is not None and not st.session_state.df.empty:
    st.divider(); st.subheader("📝 QUOTE SUMMARY")
    h_col0, h_col1, h_col2, h_col3, h_col4, h_col4b, h_col5 = st.columns([0.4, 3.2, 1.0, 1.2, 1.2, 1.2, 1.4])
    h_col1.markdown("<div class='summary-hdr'>Item Description</div>", unsafe_allow_html=True)
    h_col2.markdown("<div class='summary-hdr'>Qty (Editable)</div>", unsafe_allow_html=True)
    h_col3.markdown("<div class='summary-hdr'>Gross Unit</div>", unsafe_allow_html=True)
    h_col4.markdown("<div class='summary-hdr'>Disc %</div>", unsafe_allow_html=True)
    h_col4b.markdown("<div class='summary-hdr'>Override Rate</div>", unsafe_allow_html=True)
    h_col5.markdown("<div class='summary-hdr' style='text-align: right;'>Subtotal</div>", unsafe_allow_html=True)

    h_tot_c, h_wk1_gear, total_kg, itrac_sqm, has_itrac = 0.0, 0.0, 0.0, 0.0, False
    for idx, row in st.session_state.df.iterrows():
        override = row.get("Override_Rate", 0.0)
        active_base = override if override > 0 else row["Unit Rate"]
        active_hire_base = override if override > 0 else row["Base_Hire"]
        
        qty, brate, dm = row["Qty"], active_base, (1 - (row["Discount"]/100))
        total_kg += row["KG"]
        h_wk1_gear += (qty * active_hire_base)
        if row["Product"] == "I-Trac®": itrac_sqm, has_itrac = itrac_sqm + qty, True
            
        wk1_t = (qty * brate + row["Raw_Lab"]) * dm if labour_mode == "Include in Hire" else (qty * brate) * dm
        h_tot_c += wk1_t
        
        c0, c1, c2, c3, c4, c4b, c5 = st.columns([0.4, 3.2, 1.0, 1.2, 1.2, 1.2, 1.4])
        if c0.button("🗑️", key=f"sdel_{idx}"):
            st.session_state.df.drop(idx, inplace=True); st.session_state.df.reset_index(drop=True, inplace=True); st.rerun()
            
        c1.markdown(f"<div class='item-text'>{row['Product']}</div>", unsafe_allow_html=True)
        new_qty = c2.number_input("QtyBox", min_value=0.0, value=float(qty), key=f"sqty_{idx}", label_visibility="collapsed")
        if new_qty != float(qty): st.session_state.df.at[idx, "Qty"] = new_qty; st.rerun()
            
        c3.write(f"${row['Unit Rate']:,.2f}")
        new_disc = c4.number_input("Disc %", 0.0, 100.0, float(row["Discount"]), key=f"sd_{idx}", label_visibility="collapsed")
        if new_disc != row["Discount"]: st.session_state.df.at[idx, "Discount"] = new_disc; st.rerun()
            
        new_override = c4b.number_input("Override", 0.0, 5000.0, float(row.get("Override_Rate", 0.0)), key=f"so_{idx}", label_visibility="collapsed")
        if new_override != row.get("Override_Rate", 0.0): st.session_state.df.at[idx, "Override_Rate"] = new_override; st.rerun()
        c5.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700;'>${wk1_t:,.2f}</div>", unsafe_allow_html=True)

    # Automated logistics loops anchors 
    min_trucks = math.ceil(itrac_sqm / 288) if has_itrac else math.ceil(total_kg / 6000) or 1
    saved_trk_count = st.session_state.overrides_dict.get("logistics_truck_allocation_count_scalar", float(min_trucks))
    trks = int(saved_trk_count)

    raw_lab_pool = st.session_state.df["Raw_Lab"].sum()
    auto_cartage_total = trks * st.session_state.km * 4 * 3.50 if cartage_mode == "Charge" else 0
    auto_waiver_total = h_wk1_gear * 0.07 if waiver_mode == "Charge" else 0

    # ==============================================================================
    # 9. LIVE ON-SCREEN INTERACTIVE OVERRIDES SECTION
    # ==============================================================================
    st.divider(); st.markdown("### 🛠️ MANUAL LOGISTICS OVERRIDES")
    h_adj0, h_adj1, h_adj2, h_adj3 = st.columns([0.4, 3.2, 2.2, 1.4])
    h_adj1.markdown("<div class='summary-hdr'>Item Description</div>", unsafe_allow_html=True)
    h_adj2.markdown("<div class='summary-hdr'>Override Rate (Editable)</div>", unsafe_allow_html=True)
    h_adj3.markdown("<div class='summary-hdr' style='text-align: right;'>Subtotal</div>", unsafe_allow_html=True)
    
    final_labour_pool_sum = 0.0
    has_changes_detected = False

    if labour_mode == "Separate":
        for idx, row in st.session_state.df.iterrows():
            if row.get('Raw_Lab', 0.0) > 0.0:
                p_label = row['Product']
                lbl_key = f"lab_ovr_{p_label}_{idx}"
                auto_val = float(row['Raw_Lab'])
                math_hint_str = row['Lab_Math']
                
                saved_override_val = st.session_state.overrides_dict.get(lbl_key, -1.0)
                active_display_val = saved_override_val if saved_override_val >= 0 else auto_val
                
                r_c0, r_c1, r_c2, r_c3 = st.columns([0.4, 3.2, 2.2, 1.4])
                r_c1.markdown(f"<div class='item-text'>Labour: {p_label}</div><div class='sub-math-hint'>{math_hint_str.lower()}</div>", unsafe_allow_html=True)
                new_input_val = r_c2.number_input("InputL", min_value=0.0, value=float(active_display_val), key=f"f_l_{idx}", label_visibility="collapsed")
                r_c3.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700;'>${new_input_val:,.2f}</div>", unsafe_allow_html=True)
                
                final_labour_pool_sum += new_input_val
                if new_input_val != active_display_val:
                    st.session_state.overrides_dict[lbl_key] = new_input_val; has_changes_detected = True

        if final_labour_pool_sum < 350.00 and final_labour_pool_sum > 0:
            floor_topup = 350.00 - final_labour_pool_sum
            r_f0, r_f1, r_f2, r_f3 = st.columns([0.4, 3.2, 2.2, 1.4])
            r_f1.markdown("<div class='item-text'>Labour Minimum Floor Buffer</div>", unsafe_allow_html=True)
            r_f3.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700; color: grey;'>${floor_topup:,.2f}</div>", unsafe_allow_html=True)
            final_labour_pool_sum = 350.00
    else: final_labour_pool_sum = 0.0

    r_trk0, r_trk1, r_trk2, r_trk3 = st.columns([0.4, 3.2, 2.2, 1.4])
    r_trk1.markdown(f"<div class='item-text'>Logistics: Active Truck Count</div><div class='sub-math-hint'>calculated requirement: {min_trucks} truck(s)</div>", unsafe_allow_html=True)
    new_trk_count = r_trk2.number_input("TruckInputBox", min_value=float(min_trucks), step=1.0, value=float(trks), key="f_trk_scalar_cell", label_visibility="collapsed")
    r_trk3.markdown(f"<div style='text-align: right; font-size: 16px; font-weight: 600; color: grey; margin-top: 14px;'>{int(new_trk_count)} Truck(s)</div>", unsafe_allow_html=True)
    if new_trk_count != float(trks):
        st.session_state.overrides_dict["logistics_truck_allocation_count_scalar"] = new_trk_count; has_changes_detected = True

    cart_key = "logistics_cartage_freight_global"
    saved_cart_override = st.session_state.overrides_dict.get(cart_key, -1.0)
    active_cart_display = saved_cart_override if saved_cart_override >= 0 else auto_cartage_total
    r_t0, r_t1, r_t2, r_t3 = st.columns([0.4, 3.2, 2.2, 1.4])
    r_t1.markdown(f"<div class='item-text'>Logistics: Cartage Freight Fee</div><div class='sub-math-hint'>default: {trks} trucks x {st.session_state.km}km x 4 x $3.50</div>", unsafe_allow_html=True)
    new_cart_val = r_t2.number_input("InputC", min_value=0.0, value=float(active_cart_display), key="f_c_global", label_visibility="collapsed")
    r_t3.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700;'>${new_cart_val:,.2f}</div>", unsafe_allow_html=True)
    final_cartage_sum = new_cart_val
    if new_cart_val != active_cart_display: st.session_state.overrides_dict[cart_key] = new_cart_val; has_changes_detected = True

    waiv_key = "damage_waiver_insurance_global"
    saved_waiv_override = st.session_state.overrides_dict.get(waiv_key, -1.0)
    active_waiv_display = saved_waiv_override if saved_waiv_override >= 0 else auto_waiver_total
    r_w0, r_w1, r_w2, r_w3 = st.columns([0.4, 3.2, 2.2, 1.4])
    r_w1.markdown(f"<div class='item-text'>Waiver: Equipment Damage Indemnity</div><div class='sub-math-hint'>default: ${h_wk1_gear:,.2f} gear x 7%</div>", unsafe_allow_html=True)
    new_waiv_val = r_w2.number_input("InputW", min_value=0.0, value=float(active_waiv_display), key="f_w_global", label_visibility="collapsed")
    r_w3.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700;'>${new_waiv_val:,.2f}</div>", unsafe_allow_html=True)
    final_waiver_sum = new_waiv_val
    if new_waiv_val != active_waiv_display: st.session_state.overrides_dict[waiv_key] = new_waiv_val; has_changes_detected = True

    if has_changes_detected: st.rerun()

    # Footer metrics displays dashboards 
    st.divider(); m = st.columns(6)
    m[0].metric("HIRE COST", f"${round(h_tot_c, 2):,}")
    m[1].metric("LABOUR", f"${round(final_labour_pool_sum, 2):,}")
    m[2].metric("WAIVER", f"${round(final_waiver_sum, 2):,}")
    m[3].metric("CARTAGE", f"${round(final_cartage_sum, 2):,}")
    m[4].metric("WEIGHT", f"{round(total_kg, 0):}kg")
    m[5].metric("TRUCKS", f"{trks}")
    
    grand_total_calc = h_tot_c + final_labour_pool_sum + final_waiver_sum + final_cartage_sum
    st.markdown(f"<div class='gt-banner'>GRAND TOTAL (EX GST): ${grand_total_calc:,.2f}</div>", unsafe_allow_html=True)
    
    # Compile strings parameters targeting the clean PDF black-header generation rows
    structural_math_dict = {"LABOUR": [], "LOGISTICS": [], "DAMAGE WAIVER": []}
    for idx, row in st.session_state.df.iterrows():
        if row.get('Raw_Lab', 0.0) > 0.0:
            structural_math_dict["LABOUR"].append(f"{row['Product']} = ${row['Raw_Lab']:,.2f}")
    structural_math_dict["LABOUR"].append(f"Total Applied = ${final_labour_pool_sum:,.2f}")
    structural_math_dict["LOGISTICS"].append(f"{trks} Trucks x {st.session_state.km}km x 4 x $3.50 = ${final_cartage_sum:,.2f}")
    structural_math_dict["DAMAGE WAIVER"].append(f"${h_wk1_gear:,.2f} value * 7% = ${final_waiver_sum:,.2f}")

# ==============================================================================
# 10. SAVE & DOWNLOAD INTERACTION ZONE
# ==============================================================================
    st.markdown("")  
    action_col_1, action_col_2, action_col_3 = st.columns(3)
    
    if action_col_1.button("💾 SAVE PROJECT TO CLOUD", use_container_width=True):
        try:
            target_label = st.session_state.proj.strip()
            payload = {
                "proj": target_label, "status": st.session_state.status, "km": st.session_state.km,
                "truck_override": st.session_state.truck_override, "start_date": st.session_state.start_date_val.strftime("%Y-%m-%d"),
                "cartage_mode": cartage_mode, "labour_mode": labour_mode, "waiver_mode": waiver_mode,
                "site_address": st.session_state.site_address_str, "items": st.session_state.df.to_dict(orient="records"),
                "overrides_dict": st.session_state.overrides_dict
            }
            with open(f"{VAULT_DIR}/{target_label}.json", "w") as f: json.dump(payload, f)
            st.success(f"🎉 Updated quote options parameters for: '{target_label}' in cloud storage!"); st.rerun()
        except Exception as e: st.error(f"Save error: {str(e)}")
            
    cleaned_pdf_items = st.session_state.df.to_dict('records')
    pdf_b = create_calculation_pdf(st.session_state.proj, h_tot_c, final_labour_pool_sum, final_waiver_sum, final_cartage_sum, grand_total_calc, weeks, start_d, end_d, cleaned_pdf_items, structural_math_dict, st.session_state.status)
    action_col_2.download_button("📥 DOWNLOAD DETAILED AUDIT PDF", pdf_b, file_name=f"{st.session_state.proj}_Analysis.pdf", mime="application/pdf", use_container_width=True)

    # --- NATIVE FILE TEMPLATE EXPORTER ---
    excel_df = catalog_db.copy() if catalog_db is not None else pd.DataFrame([{"System Status": "Catalog Empty"}])
    try:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            excel_df.to_excel(writer, index=False, sheet_name='Audit_Database_Matrix')
        excel_data_bytes, ext, mt = excel_buffer.getvalue(), "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except:
        excel_data_bytes, ext, mt = excel_df.to_csv(index=False).encode('utf-8'), "csv", "text/csv"

    action_col_3.download_button(label="📊 DOWNLOAD ACTIVE DATA BACKUP", data=excel_data_bytes, file_name=f"Louis_Current_Database_Template.{ext}", mime=mt, use_container_width=True)
