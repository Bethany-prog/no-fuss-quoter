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
if not os.path.exists(VAULT_DIR):
    os.makedirs(VAULT_DIR)

# SOURCE FACTORY DEPOT LOCK: 9 Battery Crt, Cranbourne West VIC 3977
DEPOT_LAT = -38.1171
DEPOT_LON = 145.2442

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
# 2. SEATING BRACKETS & FORMULAS (BACK-END LOGIC)
# ==============================================================================
GRAND_LOGIC = [
    {"max": 42, "staff": 2, "hrs": 2},
    {"max": 50, "staff": 2, "hrs": 3},
    {"max": 100, "staff": 4, "hrs": 4},
    {"max": 150, "staff": 6, "hrs": 4},
    {"max": 200, "staff": 6, "hrs": 6},
    {"max": 250, "staff": 8, "hrs": 6},
    {"max": 300, "staff": 10, "hrs": 6},
    {"max": 1000, "staff": 12, "hrs": 8},
]

def get_gs_per_seat_labour(seats):
    if seats <= 0: return 0, ""
    rate = 55.00
    for b in GRAND_LOGIC:
        if seats <= b["max"]:
            total_pool = (b["staff"] * b["hrs"] * rate) * 2 * 2
            per_seat = total_pool / seats
            desc = f"Standard Seating: {seats:,.0f} seats -> Base Labour Allocations Matrix applied"
            return round(per_seat, 2), desc
    return 0, ""

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

# ==============================================================================
# 4. MASTER FLOORING PRODUCT CATALOG LIST
# ==============================================================================
FLOORING_CATALOG = {
    "I-Trac®": {"rate": 23.40, "block": 46.80, "lab_fix": 4.65, "kg": 15.0},
    "Supa-Trac®": {"rate": 11.55, "block": 25.00, "lab_fix": 4.65, "kg": 4.5, "sheet_sqm": 3.13},
    "Plastorip": {"rate": 10.15, "block": 20.30, "lab_fix": 3.05, "kg": 4.0},
    "Trakmat": {"rate": 23.20, "block": 45.00, "lab_fix": 5.85, "kg": 35.0}
}
STRUCT_LOGIC = {span: {"bay": (5 if span >= 10 else 3), "s_rate": 23.0, "m_rate": 18.20, "s_lab": 0.40} for span in [3, 4, 6, 9, 10, 12, 15, 20]}
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
        files = [f.replace(".json", "") for f in os.listdir(VAULT_DIR) if f.endswith(".json")]
        return sorted(files)
    except:
        return []

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
            
            if "start_date" in d and d["start_date"]:
                try:
                    st.session_state.start_date_val = datetime.strptime(d["start_date"], "%Y-%m-%d").date()
                except:
                    st.session_state.start_date_val = date.today()
            else:
                st.session_state.start_date_val = date.today()
            
            items_list = d.get("items", [])
            for item in items_list:
                if "Override_Rate" not in item:
                    item["Override_Rate"] = 0.0
                if "Discount" not in item:
                    item["Discount"] = 0.0
                    
            st.session_state.df = pd.DataFrame(items_list)
            st.session_state.reset_key_seed += 1
            st.rerun()
    except Exception as e:
        st.error(f"Vault Load Bypass Error: {str(e)}")

# ==============================================================================
# 6. VISUAL CSS LOOK & FEEL (FRONT-OF-HOUSE)
# ==============================================================================
st.markdown("""<style>
    .main { background-color: #F4F7F9 !important; }
    .stAppDeployButton { display:none !important; }
    h1 { color: #1A1D2D !important; font-size: 52px !important; font-weight: 900 !important; }
    h3 { color: #FFFFFF !important; border-left: 10px solid #00E676; padding: 40px; background-color: #1A1D2D; border-radius: 0 12px 12px 0; font-size: 24px !important; margin-bottom: 15px; }
    div.stMetric { background-color: #FFFFFF !important; padding: 15px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    div[data-testid="stMetricValue"] { color: #3D5AFE !important; font-size: 30px !important; font-weight: 800 !important; }
    .item-text { font-size: 20px !important; font-weight: 700 !important; color: #1A1D2D; margin-top: 10px; }
    .sub-math-hint { font-size: 13px !important; color: #5C6BC0 !important; font-style: italic; font-weight: 600; display: block; margin-top: -4px; margin-bottom: 8px; }
    .gt-banner { background: #1A1D2D; color: #00E676; padding: 40px; border-radius: 20px; text-align: right; font-size: 44px !important; font-weight: 900; margin-top: 30px; border: 6px solid #00E676; box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
    .summary-hdr { font-weight: 800 !important; color: #1A1D2D !important; font-size: 15px !important; text-transform: uppercase !important; border-bottom: 2px solid #1A1D2D; padding-bottom: 5px; }
</style>""", unsafe_allow_html=True)

# ==============================================================================
# 7. MAIN INTERFACE WORKSPACE MOUNTING MATRIX
# ==============================================================================
st.title("Louis Master Quoter")

vault_jobs = pull_vault_archive_list()

# THE CONTROL TOWER DEED MATRIX: Top Bulletin Dashboard Alert Scanner
global_warnings = []
if vault_jobs:
    for job in vault_jobs:
        try:
            with open(f"{VAULT_DIR}/{job}.json", "r") as f:
                job_data = json.load(f)
                j_status = job_data.get("status", "Quoted")
                if j_status in ["Quoted", None, "", "quoted"]:
                    if "start_date" in job_data and job_data["start_date"]:
                        j_start = datetime.strptime(job_data["start_date"], "%Y-%m-%d").date()
                        days_remaining = (j_start - date.today()).days
                        if days_remaining <= 14:
                            global_warnings.append(f"• **'{job_data.get('proj', job)}'** starts in **{days_remaining} days** (Setup Date: {j_start.strftime('%d/%m/%Y')})")
        except:
            pass

if global_warnings:
    st.markdown(
        """
        <div style="background-color: #FFEBEE; border-left: 8px solid #D50000; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
            <h4 style="color: #D50000; margin-top:0; font-weight:800; font-family:sans-serif;">🚨 CONTROL TOWER: TIME-SENSITIVE PIPELINE ALERT</h4>
            <p style="color: #1A1D2D; font-size:15px; font-weight:600; margin-bottom:10px;">The following stored projects are still marked as 'Quoted' but are starting inside your critical 2-week deadline window:</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    for warn in global_warnings:
        st.markdown(f"<div style='padding-left:15px; font-weight:700; color:#B71C1C; font-family:sans-serif; margin-bottom:4px;'>{warn}</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 13px; color: #555; margin-top: 15px; font-style:italic;'>Action Required: Re-validate booking confirmations or adjust the project stage fields in the selector workspace below to clear these flags.</div><hr style='border:1px solid #FFCDD2;'>", unsafe_allow_html=True)

# SIDEBAR PANEL
st.sidebar.title("📁 PROJECT ARCHIVE")
st.sidebar.markdown("---")

if st.sidebar.button("➕ START NEW", use_container_width=True):
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount", "Lab_Math", "Lab_Per_Unit", "Base_Hire", "Anchoring", "Override_Rate"])
    st.session_state.km = 0.0
    st.session_state.proj = "New Project"
    st.session_state.active_filename = ""
    st.session_state.rename_mode = False
    st.session_state.status = "Quoted"
    st.session_state.start_date_val = date.today()
    st.session_state.truck_override = 0
    st.session_state.site_address_str = ""
    st.session_state.saved_cartage_mode = "Charge"
    st.session_state.saved_labour_mode = "Separate"
    st.session_state.saved_waiver_mode = "Charge"
    st.session_state.overrides_dict = {}
    st.session_state.reset_key_seed += 1
    st.rerun()

st.sidebar.markdown("---")

if st.session_state.active_filename and not st.session_state.rename_mode:
    st.sidebar.markdown(f"**📌 File Target:** `{st.session_state.active_filename}`")
    if st.sidebar.button("✏️ Rename / Duplicate Project", use_container_width=True):
        st.session_state.rename_mode = True
        st.rerun()
else:
    ui_proj_name = st.sidebar.text_input("Project Label", value=st.session_state.proj, key=f"pname_box_{st.session_state.reset_key_seed}")
    st.session_state.proj = ui_proj_name.strip()
    if st.session_state.active_filename and st.session_state.rename_mode:
        if st.sidebar.button("🔒 Keep Current Name", use_container_width=True):
            st.session_state.rename_mode = False
            st.session_state.proj = st.session_state.active_filename
            st.rerun()

if vault_jobs:
    load_choice = st.sidebar.selectbox("Cloud Retrieval Menus", ["-- Choose Project --"] + vault_jobs)
    if st.sidebar.button("📂 LOAD PROJECT") and load_choice != "-- Choose Project --":
        load_project_from_vault(load_choice)
        
    st.sidebar.markdown("---")
    if st.sidebar.button("❌ DELETE SELECTED PROJECT", use_container_width=True):
        if load_choice != "-- Choose Project --":
            target_path = f"{VAULT_DIR}/{load_choice}.json"
            if os.path.exists(target_path):
                os.remove(target_path)
                st.sidebar.success(f"Deleted '{load_choice}' completely.")
                st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount", "Lab_Math", "Lab_Per_Unit", "Base_Hire", "Anchoring", "Override_Rate"])
                st.session_state.km = 0.0
                st.session_state.proj = "New Project"
                st.session_state.active_filename = ""
                st.session_state.rename_mode = False
                st.session_state.status = "Quoted"
                st.session_state.start_date_val = date.today()
                st.session_state.truck_override = 0
                st.session_state.site_address_str = ""
                st.session_state.saved_cartage_mode = "Charge"
                st.session_state.saved_labour_mode = "Separate"
                st.session_state.saved_waiver_mode = "Charge"
                st.session_state.overrides_dict = {}
                st.session_state.reset_key_seed += 1
                st.rerun()
else:
    st.sidebar.info("No Projects Saved In Cloud Yet")

# CORE DATA INPUTS
st.markdown(f"### 📍 Active Workspace: {st.session_state.proj}")
st.session_state.status = st.selectbox("Stage", STAGES, index=STAGES.index(st.session_state.status) if st.session_state.status in STAGES else 0, key=f"stage_select_{st.session_state.reset_key_seed}")
st.markdown(f"<div style='height: 14px; background-color: {STAGE_COLORS[st.session_state.status]}; border-radius: 6px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
start_d = c1.date_input("Start Date", value=st.session_state.start_date_val, key=f"sd_pick_{st.session_state.reset_key_seed}")
st.session_state.start_date_val = start_d
end_d = c2.date_input("End Date", value=start_d, key=f"ed_pick_{st.session_state.reset_key_seed}")
weeks = math.ceil(((end_d - start_d).days) / 7) or 1

# UPGRADE v55.0: Geocoding Map Offline Resilience Core
input_addr = c3.text_input("🏠 Delivery Site Address", value=st.session_state.site_address_str, placeholder="Type full address or suburb...", key=f"addr_field_{st.session_state.reset_key_seed}")

if input_addr.strip() != st.session_state.site_address_str:
    st.session_state.site_address_str = input_addr.strip()
    if input_addr.strip() != "":
        try:
            # Bump server connection patience to a stable 5-second max retries limit
            geolocator = Nominatim(user_agent="louis_quoter_engine_v55", timeout=5)
            loc_data = geolocator.geocode(input_addr.strip() + ", Victoria, Australia")
            
            if loc_data:
                target_coords = (loc_data.latitude, loc_data.longitude)
                depot_coords = (DEPOT_LAT, DEPOT_LON)
                
                calculated_raw_km = geodesic(depot_coords, target_coords).kilometers
                final_buffered_km = round(calculated_raw_km * 1.15, 1)
                
                st.session_state.km = final_buffered_km
                st.toast(f"📍 Location verified: {loc_data.address[:45]}... Linked as {final_buffered_km} KM", icon="✅")
            else:
                st.sidebar.error("Address lookup timeout or not found. Use manual KM box below.")
        except Exception as maps_err:
            # Catch network timeout errors gracefully without crashing or zeroing parameters out
            st.sidebar.warning("🗺️ Map API timeout or offline. Enter the route distance manually below.")

# UPGRADE v55.0: Editable backup input block for one-way distance parameter management
st.markdown("**🚛 Active Routing Distance**")
c_km1, c_km2 = st.columns([1, 4])
new_manual_km = c_km1.number_input("One-Way KM", min_value=0.0, step=0.5, value=float(st.session_state.km), key="manual_km_override_box")
if new_manual_km != float(st.session_state.km):
    st.session_state.km = new_manual_km

c_km2.info(f"**Configuration Active:** Job site location calculations locked at **{st.session_state.km} One-Way KM** (Origin Depot: Cranbourne West)")

# Multi-Segment Toggle Rules
l1, l2, l3 = st.columns(3)

c_opts = ["Charge", "Free"]
cartage_mode = l1.segmented_control("Cartage Math", c_opts, default=st.session_state.saved_cartage_mode, key=f"cart_toggle_{st.session_state.reset_key_seed}")
st.session_state.saved_cartage_mode = cartage_mode

lab_opts = ["Separate", "Include in Hire", "Free"]
labour_mode = l2.segmented_control("Labour Math", lab_opts, default=st.session_state.saved_labour_mode, key=f"lab_toggle_{st.session_state.reset_key_seed}")
st.session_state.saved_labour_mode = labour_mode

w_opts = ["Charge", "Free"]
waiver_mode = l3.segmented_control("Damage Waiver", w_opts, default=st.session_state.saved_waiver_mode, key=f"waiv_toggle_{st.session_state.reset_key_seed}")
st.session_state.saved_waiver_mode = waiver_mode

st.divider(); col1, col2 = st.columns(2)
with col1:
    st.markdown("### ⚡ Structures & Seating Systems")
    s_type = st.selectbox("Product Line Type", ["Standard Frame Marquee", "WOW Marquee", "Grandstand Seating Tier"], key=f"str_type_{st.session_state.reset_key_seed}")
    
    if s_type == "WOW Marquee":
        st.caption("WOW Marquee rules enabled ($1,029.00 Base / Adaptive Setup Matrix).")
        m_in = "6x3" 
        m_q = st.number_input("Structure Count Qty", min_value=1, value=1, key=f"str_qty_{st.session_state.reset_key_seed}")
        anchoring_type = st.segmented_control("Anchoring Method", ["Pegged", "Weighted"], default="Pegged", key=f"anch_tog_{st.session_state.reset_key_seed}")
        
    elif s_type == "Grandstand Seating Tier":
        st.caption("Grandstand Tier rules active (Variable matrix labour pooling distribution system).")
        m_in = "Seating System"
        m_q = st.number_input("Total Seat Capacity Count", min_value=1, value=50, key=f"str_qty_{st.session_state.reset_key_seed}")
        anchoring_type = "" 
        
    else:
        m_in = st.text_input("Size (e.g. 10x15)", key=f"str_sz_{st.session_state.reset_key_seed}")
        m_q = st.number_input("Structure Count Qty", min_value=1, value=None, key=f"str_qty_{st.session_state.reset_key_seed}")
        anchoring_type = st.segmented_control("Anchoring Method", ["Pegged", "Weighted"], default="Pegged", key=f"anch_tog_{st.session_state.reset_key_seed}")
        
    if st.button("Add Structural System") and m_in and m_q:
        if s_type == "WOW Marquee":
            brate = 1029.00
            new_struct_df = pd.DataFrame([{
                "Qty": m_q, "Product": "WOW Marquee 6x3m", "Unit Rate": brate, "Min_Lab": 0, 
                "Raw_Lab": 0.0, "Lab_Math": "WOW Engine Logic Triggered", "KG": 450.0 * m_q, 
                "Is_Marquee": True, "Discount": 0.0, "Lab_Per_Unit": 0, "Base_Hire": brate, "Anchoring": anchoring_type, "Override_Rate": 0.0
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_struct_df], ignore_index=True)
            
            if anchoring_type == "Weighted":
                calculated_weights = 128 if m_q == 2 else math.ceil((4 * m_q * 500.0) / 30.0)
                w_lab_cost = calculated_weights * 1.65
                new_weight_df = pd.DataFrame([{
                    "Qty": calculated_weights, "Product": "30kg Weights", "Unit Rate": 6.60, "Min_Lab": 0, 
                    "Raw_Lab": w_lab_cost, "Lab_Math": f"30kg Weights: {calculated_weights:,.0f} units x $1.65", 
                    "KG": calculated_weights * 30.0, "Is_Marquee": False, "Discount": 0.0, "Lab_Per_Unit": 1.65, "Base_Hire": 6.60, "Anchoring": "", "Override_Rate": 0.0
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_weight_df], ignore_index=True)
            st.rerun()
            
        elif s_type == "Grandstand Seating Tier":
            lab_per_seat, lab_desc = get_gs_per_seat_labour(m_q)
            base_seat_hire = 15.00 if weeks < 4 else 7.50
            combined_unit_rate = base_seat_hire + lab_per_seat
            
            new_gs_df = pd.DataFrame([{
                "Qty": m_q, "Product": "Standard Seating Grandstand", "Unit Rate": combined_unit_rate, "Min_Lab": 0, 
                "Raw_Lab": 0.0, "Lab_Math": lab_desc, "KG": m_q * 25.0, "Is_Marquee": False, "Discount": 0.0, 
                "Lab_Per_Unit": lab_per_seat, "Base_Hire": base_seat_hire, "Anchoring": "", "Override_Rate": 0.0
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_gs_df], ignore_index=True)
            st.rerun()
            
        else:
            nums = re.findall(r'\d+', m_in)
            if len(nums) >= 2:
                span, length = int(nums[0]), int(nums[1])
                logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
                sqm = span*length; hire_rate = logic['s_rate'] if (length/3) <= 1 else logic['m_rate']
                brate = sqm * hire_rate; lab_cost = brate * logic['s_lab']
                
                new_struct_df = pd.DataFrame([{
                    "Qty": m_q, "Product": f"Structure {span}x{length}m", "Unit Rate": brate, "Min_Lab": 350, 
                    "Raw_Lab": lab_cost, "Lab_Math": f"Structure {span}x{length} ({anchoring_type}): ${brate:,.2f} x {logic['s_lab']:.2f}", "KG": (sqm*15)*m_q, 
                    "Is_Marquee": True, "Discount": 0.0, "Lab_Per_Unit": 0, "Base_Hire": brate, "Anchoring": anchoring_type, "Override_Rate": 0.0
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_struct_df], ignore_index=True)
                
                if anchoring_type == "Weighted":
                    bay_len = logic.get('bay', 3)
                    num_bays = math.ceil(length / bay_len)
                    legs_per_structure = (num_bays + 1) * 2
                    total_legs = legs_per_structure * m_q
                    weights_per_leg = 2 if span <= 6 else (4 if span <= 9 else (6 if span <= 12 else (8 if span <= 15 else 10)))
                        
                    calculated_weights = total_legs * weights_per_leg
                    w_lab_cost = calculated_weights * 1.65
                    new_weight_df = pd.DataFrame([{
                        "Qty": calculated_weights, "Product": "30kg Weights", "Unit Rate": 6.60, "Min_Lab": 0, 
                        "Raw_Lab": w_lab_cost, "Lab_Math": f"30kg Weights: {calculated_weights:,.0f} units x $1.65", 
                        "KG": calculated_weights * 30.0, "Is_Marquee": False, "Discount": 0.0, "Lab_Per_Unit": 1.65, "Base_Hire": 6.60, "Anchoring": "", "Override_Rate": 0.0
                    }])
                    st.session_state.df = pd.concat([st.session_state.df, new_weight_df], ignore_index=True)
                st.rerun()

with col2:
    st.markdown("### 🪵 Flooring Catalog")
    f_sel = st.selectbox("Flooring Type Options", list(FLOORING_CATALOG.keys()), key=f"f_pick_{st.session_state.reset_key_seed}")
    f_qty = st.number_input("Square Metre Coverage / Count", min_value=0.0, value=None, key=f"f_qty_{st.session_state.reset_key_seed}")
    if st.button("Add Flooring Component") and f_qty:
        data = FLOORING_CATALOG[f_sel]
        base_h = (data['block']/4) if (weeks >= 4 and 'block' in data) else data['rate']
        raw_lab_pool = f_qty * data.get('lab_fix', 0)
        lab_desc = f"{f_sel}: {f_qty:,.0f} sqm x ${data.get('lab_fix', 0):,.2f}"
        eff_qty = (math.ceil(f_qty / data["sheet_sqm"]) * data["sheet_sqm"]) if "sheet_sqm" in data else f_qty
        
        new_item_df = pd.DataFrame([{
            "Qty": f_qty, "Product": f_sel, "Unit Rate": base_h, "Min_Lab": 0, "Raw_Lab": raw_lab_pool, 
            "Lab_Math": lab_desc, "KG": eff_qty * data['kg'], "Is_Marquee": False, "Discount": 0.0, 
            "Lab_Per_Unit": 0, "Base_Hire": base_h, "Anchoring": "", "Override_Rate": 0.0
        }])
        st.session_state.df = pd.concat([st.session_state.df, new_item_df], ignore_index=True)
        st.rerun()

# ==============================================================================
# 8. LIVE CALCULATION DATA VIEWER
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
    
    # Run dynamic parsing checks safely
    other_products_count = 0
    wow_marquee_qty = 0
    for idx, row in st.session_state.df.iterrows():
        p_name = row["Product"]
        if p_name != "30kg Weights" and "WOW Marquee" not in p_name:
            other_products_count += 1
        if "WOW Marquee" in p_name:
            wow_marquee_qty += int(row["Qty"])
            
    for idx, row in st.session_state.df.iterrows():
        if "WOW Marquee" in row["Product"]:
            st.session_state.df.at[idx, "Raw_Lab"] = 1411.00
            st.session_state.df.at[idx, "Lab_Math"] = f"WOW Marquee: {row['Qty']:.0f} x $706 = $1,441.00"

    h_tot_c, h_wk1_gear, total_kg, itrac_sqm = 0.0, 0.0, 0.0, 0.0
    has_itrac = False

    for idx, row in st.session_state.df.iterrows():
        override = row.get("Override_Rate", 0.0)
        active_base = override if override > 0 else row["Unit Rate"]
        active_hire_base = override if override > 0 else row["Base_Hire"]
        
        qty, brate, dm = row["Qty"], active_base, (1 - (row["Discount"]/100))
        total_kg += row["KG"]
        h_wk1_gear += (qty * active_hire_base)
        
        if row["Product"] == "I-Trac®":
            itrac_sqm += qty
            has_itrac = True
            
        wk1_t = (qty * brate + row["Raw_Lab"]) * dm if labour_mode == "Include in Hire" else (qty * brate) * dm
        h_tot_c += wk1_t
        
        c0, c1, c2, c3, c4, c4b, c5 = st.columns([0.4, 3.2, 1.0, 1.2, 1.2, 1.2, 1.4])
        if c0.button("🗑️", key=f"sdel_{idx}"):
            st.session_state.df.drop(idx, inplace=True)
            st.session_state.df.reset_index(drop=True, inplace=True)
            st.rerun()
        
        prod_display = row['Product']
        if 'Anchoring' in row and row['Anchoring']:
            prod_display += f" ({row['Anchoring']})"
            
        c1.markdown(f"<div class='item-text'>{prod_display} - Wk 1</div>", unsafe_allow_html=True)
        
        new_qty = c2.number_input("QtyBox", min_value=0.0, step=1.0, value=float(qty), key=f"sqty_{idx}", label_visibility="collapsed")
        if new_qty != float(qty):
            st.session_state.df.at[idx, "Qty"] = new_qty
            if "WOW Marquee" in row["Product"]:
                for w_idx, w_row in st.session_state.df.iterrows():
                    if w_row["Product"] == "30kg Weights":
                        st.session_state.df.at[w_idx, "Qty"] = 128 if new_qty == 2 else math.ceil((4 * new_qty * 500.0) / 30.0)
            st.rerun()
            
        c3.write(f"${row['Unit Rate']:,.2f}")
        
        new_disc = c4.number_input("Disc %", 0.0, 100.0, float(row["Discount"]), 1.0, key=f"sd_{idx}", label_visibility="collapsed")
        if new_disc != row["Discount"]:
            st.session_state.df.at[idx, "Discount"] = new_disc
            st.rerun()
            
        new_override = c4b.number_input("Rate Override", 0.0, 5000.0, float(row.get("Override_Rate", 0.0)), 0.5, key=f"so_{idx}", label_visibility="collapsed")
        if new_override != row.get("Override_Rate", 0.0):
            st.session_state.df.at[idx, "Override_Rate"] = new_override
            st.rerun()
            
        c5.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700; color: #1A1D2D; margin-top: 10px;'>${wk1_t:,.2f}</div>", unsafe_allow_html=True)
        
        if weeks > 1:
            r_rate = (active_hire_base * 0.5 if row["Is_Marquee"] else active_hire_base)
            r_tot = qty * r_rate * (weeks-1) * dm
            h_tot_c += r_tot
            cb = st.columns([0.4, 3.2, 1.0, 1.2, 1.2, 1.2, 1.4])
            cb[1].markdown(f"<div style='color:grey; font-style:italic; font-size:18px;'>└ Recurring (x{weeks-1} wks)</div>", unsafe_allow_html=True)
            cb[2].write(f"{qty:,.0f}")
            standard_r_rate = (row["Base_Hire"] * 0.5 if row["Is_Marquee"] else row["Base_Hire"])
            cb[3].write(f"${standard_r_rate:,.2f}")
            cb[6].markdown(f"<div style='text-align: right; color: grey; font-style: italic;'>${r_tot:,.2f}</div>", unsafe_allow_html=True)

    # Core background transport variables engine 
    if has_itrac:
        min_trucks = math.ceil(itrac_sqm / 288) or 1
    else:
        min_trucks = math.ceil(total_kg / 6000) or 1
        
    truck_input_key = "logistics_truck_allocation_count_scalar"
    saved_trk_count = st.session_state.overrides_dict.get(truck_input_key, float(min_trucks))
    trks = int(saved_trk_count)

    raw_lab_pool = st.session_state.df["Raw_Lab"].sum()
    auto_cartage_total = trks * st.session_state.km * 4 * 3.50 if cartage_mode == "Charge" else 0
    auto_waiver_total = h_wk1_gear * 0.07 if waiver_mode == "Charge" else 0

    # ==============================================================================
    # 9. MANUAL LOGISTICS OVERRIDES WORKSPACE GRID
    # ==============================================================================
    st.divider()
    st.markdown("### 🛠️ MANUAL LOGISTICS OVERRIDES")
    
    h_adj0, h_adj1, h_adj2, h_adj3 = st.columns([0.4, 3.2, 2.2, 1.4])
    h_adj1.markdown("<div class='summary-hdr'>Item Description</div>", unsafe_allow_html=True)
    h_adj2.markdown("<div class='summary-hdr'>Override Rate / Allocation Field (Editable)</div>", unsafe_allow_html=True)
    h_adj3.markdown("<div class='summary-hdr' style='text-align: right;'>Subtotal</div>", unsafe_allow_html=True)
    
    final_labour_pool_sum = 0.0
    has_changes_detected = False

    # A. LABOUR OVERRIDES
    if labour_mode == "Separate":
        for idx, row in st.session_state.df.iterrows():
            if row.get('Raw_Lab', 0.0) > 0.0 or "WOW Marquee" in row['Product']:
                p_label = row['Product']
                lbl_key = f"lab_ovr_{p_label}_{idx}"
                
                auto_val = 1411.00 if "WOW Marquee" in p_label else float(row['Raw_Lab'])
                
                if "WOW Marquee" in p_label:
                    math_hint_str = row['Lab_Math']
                elif "Trakmat" in p_label:
                    math_hint_str = f"default book: {row['Qty']:,.0f} units x $5.85 = ${auto_val:,.2f}"
                else:
                    math_hint_str = f"default book: {row['Qty']:,.0f} units x $1.65 = ${auto_val:,.2f}"
                
                saved_override_val = st.session_state.overrides_dict.get(lbl_key, -1.0)
                active_display_val = saved_override_val if saved_override_val >= 0 else auto_val
                
                r_c0, r_c1, r_c2, r_c3 = st.columns([0.4, 3.2, 2.2, 1.4])
                r_c1.markdown(f"<div class='item-text'>Labour: {p_label}</div><div class='sub-math-hint'>{math_hint_str.lower()}</div>", unsafe_allow_html=True)
                
                new_input_val = r_c2.number_input("InputL", min_value=0.0, value=float(active_display_val), key=f"f_l_{idx}", label_visibility="collapsed")
                r_c3.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700; color: #1A1D2D; margin-top: 10px;'>${new_input_val:,.2f}</div>", unsafe_allow_html=True)
                
                final_labour_pool_sum += new_input_val
                if new_input_val != active_display_val:
                    st.session_state.overrides_dict[lbl_key] = new_input_val
                    has_changes_detected = True

        if final_labour_pool_sum < 350.00 and final_labour_pool_sum > 0:
            floor_topup = 350.00 - final_labour_pool_sum
            r_f0, r_f1, r_f2, r_f3 = st.columns([0.4, 3.2, 2.2, 1.4])
            r_f1.markdown("<div class='item-text'>Labour Minimum Floor Buffer</div><div class='sub-math-hint'>default minimum baseline threshold target = $350.00</div>", unsafe_allow_html=True)
            r_f3.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700; color: grey; margin-top: 10px;'>${floor_topup:,.2f}</div>", unsafe_allow_html=True)
            final_labour_pool_sum = 350.00
    else:
        final_labour_pool_sum = 0.0

    # B. TRUCK COUNTS OVERRIDE
    r_trk0, r_trk1, r_trk2, r_trk3 = st.columns([0.4, 3.2, 2.2, 1.4])
    r_trk1.markdown(f"<div class='item-text'>Logistics: Active Truck Allocation Count</div><div class='sub-math-hint'>default calculated configuration requirement = {min_trucks} truck(s)</div>", unsafe_allow_html=True)
    new_trk_count = r_trk2.number_input("TruckInputBox", min_value=float(min_trucks), step=1.0, value=float(trks), key="f_trk_scalar_cell", label_visibility="collapsed")
    r_trk3.markdown(f"<div style='text-align: right; font-size: 16px; font-weight: 600; color: grey; margin-top: 14px;'>{int(new_trk_count)} Truck(s)</div>", unsafe_allow_html=True)
    if new_trk_count != float(trks):
        st.session_state.overrides_dict[truck_input_key] = new_trk_count
        st.session_state.truck_override = int(new_trk_count)
        has_changes_detected = True

    # C. CARTAGE FREIGHT LOGISTICS
    cart_key = "logistics_cartage_freight_global"
    saved_cart_override = st.session_state.overrides_dict.get(cart_key, -1.0)
    active_cart_display = saved_cart_override if saved_cart_override >= 0 else auto_cartage_total
    cart_hint_str = f"default book: {trks} trucks x {st.session_state.km}km x 4 x $3.50 = ${auto_cartage_total:,.2f}"

    r_t0, r_t1, r_t2, r_t3 = st.columns([0.4, 3.2, 2.2, 1.4])
    r_t1.markdown(f"<div class='item-text'>Logistics: Cartage Freight Fee</div><div class='sub-math-hint'>{cart_hint_str.lower()}</div>", unsafe_allow_html=True)
    new_cart_val = r_t2.number_input("InputC", min_value=0.0, value=float(active_cart_display), key="f_c_global", label_visibility="collapsed")
    r_t3.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700; color: #1A1D2D; margin-top: 10px;'>${new_cart_val:,.2f}</div>", unsafe_allow_html=True)
    
    final_cartage_sum = new_cart_val
    if new_cart_val != active_cart_display:
        st.session_state.overrides_dict[cart_key] = new_cart_val
        has_changes_detected = True

    # D. DAMAGE WAIVER
    waiv_key = "damage_waiver_insurance_global"
    saved_waiv_override = st.session_state.overrides_dict.get(waiv_key, -1.0)
    active_waiv_display = saved_waiv_override if saved_waiv_override >= 0 else auto_waiver_total
    waiv_hint_str = f"default book: ${h_wk1_gear:,.2f} gross gear value x 7% = ${auto_waiver_total:,.2f}"

    r_w0, r_w1, r_w2, r_w3 = st.columns([0.4, 3.2, 2.2, 1.4])
    r_w1.markdown(f"<div class='item-text'>Waiver: Equipment Damage Indemnity</div><div class='sub-math-hint'>{waiv_hint_str.lower()}</div>", unsafe_allow_html=True)
    new_waiv_val = r_w2.number_input("InputW", min_value=0.0, value=float(active_waiv_display), key="f_w_global", label_visibility="collapsed")
    r_w3.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700; color: #1A1D2D; margin-top: 10px;'>${new_waiv_val:,.2f}</div>", unsafe_allow_html=True)
    
    final_waiver_sum = new_waiv_val
    if new_waiv_val != active_waiv_display:
        st.session_state.overrides_dict[waiv_key] = new_waiv_val
        has_changes_detected = True

    if has_changes_detected:
        st.rerun()

    # Dashboard Metrics status summaries layout footer
    st.divider()
    m = st.columns(6)
    m[0].metric("HIRE COST", f"${round(h_tot_c, 2):,}")
    m[1].metric("LABOUR", f"${round(final_labour_pool_sum, 2):,}")
    m[2].metric("WAIVER", f"${round(final_waiver_sum, 2):,}")
    m[3].metric("CARTAGE", f"${round(final_cartage_sum, 2):,}")
    m[4].metric("WEIGHT", f"{round(total_kg, 0):}kg")
    m[5].metric("TRUCKS", f"{trks}")
    
    grand_total_calc = h_tot_c + final_labour_pool_sum + final_waiver_sum + final_cartage_sum
    st.markdown(f"<div class='gt-banner'>GRAND TOTAL (EX GST): ${grand_total_calc:,.2f}</div>", unsafe_allow_html=True)
    
    # Compile text strings matrix fields targeting clean PDF templates
    structural_math_dict = {"LABOUR": [], "LOGISTICS": [], "DAMAGE WAIVER": []}
    
    if labour_mode == "Separate":
        for idx, row in st.session_state.df.iterrows():
            if row.get('Raw_Lab', 0.0) > 0.0 or "WOW Marquee" in row['Product']:
                p_label = row['Product']
                lbl_key = f"lab_ovr_{p_label}_{idx}"
                if lbl_key in st.session_state.overrides_dict:
                    structural_math_dict["LABOUR"].append(f"{p_label} = ${st.session_state.overrides_dict[lbl_key]:,.2f} (Manual Override)")
                else:
                    structural_math_dict["LABOUR"].append(f"{row['Lab_Math']}")
        if raw_lab_pool < 350.00:
            structural_math_dict["LABOUR"].append(f"Minimum Floor Buffer Top-up applied = ${350.00 - raw_lab_pool:,.2f}")
        structural_math_dict["LABOUR"].append(f"Total = ${final_labour_pool_sum:,.2f}")
    else:
        structural_math_dict["LABOUR"].append(f"Labour Included / Free = ${final_labour_pool_sum:,.2f}")
        
    if cart_key in st.session_state.overrides_dict or truck_input_key in st.session_state.overrides_dict:
        structural_math_dict["LOGISTICS"].append(f"Cartage Freight = ${final_cartage_sum:,.2f} (Manual Override | {trks} Truck Allocation)")
    else:
        structural_math_dict["LOGISTICS"].append(f"{trks} Trucks x {st.session_state.km}km x 4 x 3.50 = ${final_cartage_sum:,.2f}")
        
    if waiv_key in st.session_state.overrides_dict:
        structural_math_dict["DAMAGE WAIVER"].append(f"Damage Waiver = ${final_waiver_sum:,.2f} (Manual Override)")
    else:
        structural_math_dict["DAMAGE WAIVER"].append(f"{h_wk1_gear:,.2f} * 7% = ${final_waiver_sum:,.2f}")

# ==============================================================================
# 10. SAVE & DOWNLOAD INTERACTION ZONE (WITH NATIVE EXPORT STREAMS FIXED)
# ==============================================================================
    st.markdown("")  
    action_col_1, action_col_2, action_col_3 = st.columns(3)
    
    if action_col_1.button("💾 SAVE PROJECT TO CLOUD", use_container_width=True):
        if st.session_state.df is not None and not st.session_state.df.empty:
            try:
                target_label = st.session_state.active_filename.strip() if st.session_state.active_filename else st.session_state.proj.strip()
                payload = {
                    "proj": target_label, "status": st.session_state.status, "km": st.session_state.km,
                    "truck_override": st.session_state.truck_override, "start_date": st.session_state.start_date_val.strftime("%Y-%m-%d"),
                    "cartage_mode": cartage_mode, "labour_mode": labour_mode, "waiver_mode": waiver_mode,
                    "site_address": st.session_state.site_address_str, "items": st.session_state.df.to_dict(orient="records"),
                    "overrides_dict": st.session_state.overrides_dict
                }
                with open(f"{VAULT_DIR}/{target_label}.json", "w") as f:
                    json.dump(payload, f)
                    
                st.session_state.active_filename = target_label
                st.session_state.proj = target_label
                st.session_state.rename_mode = False
                st.success(f"🎉 Parameters Synchronized. Successfully updated project options file: '{target_label}' inside cloud storage!")
                st.rerun()
            except Exception as e:
                st.error(f"Internal file sync error: {str(e)}")
        else:
            st.error("Cannot sync data tables because workspace is empty.")
            
    cleaned_pdf_items = st.session_state.df.to_dict('records')
    pdf_b = create_calculation_pdf(st.session_state.proj, h_tot_c, final_labour_pool_sum, final_waiver_sum, final_cartage_sum, grand_total_calc, weeks, start_d, end_d, cleaned_pdf_items, structural_math_dict, st.session_state.status)
    action_col_2.download_button("📥 DOWNLOAD DETAILED AUDIT PDF", pdf_b, file_name=f"{st.session_state.proj}_Analysis.pdf", mime="application/pdf", use_container_width=True)

    # --- DYNAMIC MEMORY EXCEL TEMPLATE EXPORTER MATRIX HOOK ---
    excel_catalog_data = {
        "Product Group": ["Structures", "Structures", "Structures", "Flooring", "Flooring", "Flooring", "Flooring", "Ballast Accessories"],
        "Product Name": ["Standard Frame Marquee", "WOW Marquee 6x3m", "Standard Seating Grandstand", "I-Trac (R)", "Supa-Trac (R)", "Plastorip", "Trakmat", "30kg Weights"],
        "Quantity to Fill": ["", "", "", "", "", "", "", ""],
        "Base Hire Rate Used ($)": ["Dynamic Sqm Logic", 1029.00, "15.00 (Wks 1-3)", 23.40, 11.55, 10.15, 23.20, 6.60],
        "Multi-Week Block Rate ($)": ["Dynamic Sqm Logic", 1029.00, "7.50 (Wks 4+)", "46.80 (4-Wk Block)", "25.00 (4-Wk Block)", "20.30 (4-Wk Block)", "45.00 (4-Wk Block)", 6.60],
        "Handling Weight (KG)": ["15.0 kg/sqm", "450.0 kg total", "25.0 kg/seat", "15.0 kg/sqm", "4.5 kg/sqm", "4.0 kg/sqm", "35.0 kg/sheet", "30.0 kg/block"],
        "Default Labour Rate ($)": ["40% of Base Hire", 1441.00, "Variable Matrix", 4.65, 4.65, 3.05, 5.85, 1.65]
    }
    
    excel_df = pd.DataFrame(excel_catalog_data)
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        excel_df.to_excel(writer, index=False, sheet_name='Audit Product Matrix')
    excel_data_bytes = excel_buffer.getvalue()

    action_col_3.download_button(
        label="📊 DOWNLOAD EXCEL SHEET TEMPLATE",
        data=excel_data_bytes,
        file_name="Louis_Master_Quoter_Audit_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
