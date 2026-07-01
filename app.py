import streamlit as st
import math
import pandas as pd
from datetime import date, datetime, timedelta
from fpdf import FPDF
import re
import time

# ==============================================================================
# 0. NATIVE INTEGRATED MASTER DATA ARCHIVE (ZERO EXTERNAL FILE DEPENDENCY)
# ==============================================================================
st.set_page_config(page_title="Louis Master Quoter", layout="wide")

DEPOT_LAT = -38.1171
DEPOT_LON = 145.2442

NATIVE_STRUCTURES = [
    {"Configuration": "3m x 3m Hi Tops", "Type": "Marquee", "Hire Unit Rate": 198.45, "Labour Total": 350.00, "Total Weight (kg)": 480.0, "Total Number of weights": 16.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "3m x 3m Shade Canopy", "Type": "Marquee", "Hire Unit Rate": 198.45, "Labour Total": 350.00, "Total Weight (kg)": 480.0, "Total Number of weights": 16.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "3m x 6m Shade Canopy", "Type": "Marquee", "Hire Unit Rate": 396.90, "Labour Total": 350.00, "Total Weight (kg)": 720.0, "Total Number of weights": 24.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "4m x 3m", "Type": "Structure", "Hire Unit Rate": 276.00, "Labour Total": 350.00, "Total Weight (kg)": 480.0, "Total Number of weights": 24.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "4m x 6m", "Type": "Structure", "Hire Unit Rate": 436.80, "Labour Total": 350.00, "Total Weight (kg)": 720.0, "Total Number of weights": 36.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "4m x 9m", "Type": "Structure", "Hire Unit Rate": 655.20, "Labour Total": 350.00, "Total Weight (kg)": 1120.0, "Total Number of weights": 48.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "4m x 12m", "Type": "Structure", "Hire Unit Rate": 873.60, "Labour Total": 350.00, "Total Weight (kg)": 1500.0, "Total Number of weights": 60.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "4m x 15m", "Type": "Structure", "Hire Unit Rate": 1092.00, "Labour Total": 436.80, "Total Weight (kg)": 2000.0, "Total Number of weights": 72.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "4m x 18m", "Type": "Structure", "Hire Unit Rate": 1310.40, "Labour Total": 524.16, "Total Weight (kg)": 2400.0, "Total Number of weights": 72.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "4m x 21m", "Type": "Structure", "Hire Unit Rate": 1528.80, "Labour Total": 611.52, "Total Weight (kg)": 2800.0, "Total Number of weights": 96.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "4m x 24m", "Type": "Structure", "Hire Unit Rate": 1747.20, "Labour Total": 698.88, "Total Weight (kg)": 3200.0, "Total Number of weights": 108.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 3m", "Type": "Structure", "Hire Unit Rate": 414.00, "Labour Total": 350.00, "Total Weight (kg)": 480.0, "Total Number of weights": 48.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 4m", "Type": "Structure", "Hire Unit Rate": 436.80, "Labour Total": 350.00, "Total Weight (kg)": 720.0, "Total Number of weights": 48.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 8m", "Type": "Structure", "Hire Unit Rate": 873.60, "Labour Total": 350.00, "Total Weight (kg)": 1120.0, "Total Number of weights": 64.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 12m", "Type": "Structure", "Hire Unit Rate": 1310.40, "Labour Total": 524.16, "Total Weight (kg)": 1500.0, "Total Number of weights": 80.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 16m", "Type": "Structure", "Hire Unit Rate": 1747.20, "Labour Total": 698.88, "Total Weight (kg)": 2000.0, "Total Number of weights": 96.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 20m", "Type": "Structure", "Hire Unit Rate": 2184.00, "Labour Total": 873.60, "Total Weight (kg)": 3375.0, "Total Number of weights": 112.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 24m", "Type": "Structure", "Hire Unit Rate": 2620.80, "Labour Total": 1048.32, "Total Weight (kg)": 4000.0, "Total Number of weights": 128.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 28m", "Type": "Structure", "Hire Unit Rate": 3057.60, "Labour Total": 1223.04, "Total Weight (kg)": 4800.0, "Total Number of weights": 144.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 32m", "Type": "Structure", "Hire Unit Rate": 3494.40, "Labour Total": 1397.76, "Total Weight (kg)": 5400.0, "Total Number of weights": 160.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "9m x 3m", "Type": "Structure", "Hire Unit Rate": 621.00, "Labour Total": 350.00, "Total Weight (kg)": 840.0, "Total Number of weights": 80.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "9m x 6m", "Type": "Structure", "Hire Unit Rate": 982.80, "Labour Total": 393.12, "Total Weight (kg)": 1120.0, "Total Number of weights": 100.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "9m x 9m", "Type": "Structure", "Hire Unit Rate": 1474.20, "Labour Total": 589.68, "Total Weight (kg)": 1500.0, "Total Number of weights": 120.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "15m x 5m", "Type": "Structure", "Hire Unit Rate": 1725.00, "Labour Total": 948.75, "Total Weight (kg)": 5062.5, "Total Number of weights": 4.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "15m x 10m", "Type": "Structure", "Hire Unit Rate": 2317.50, "Labour Total": 927.00, "Total Weight (kg)": 9600.0, "Total Number of weights": 6.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "15m x 15m", "Type": "Structure", "Hire Unit Rate": 3476.25, "Labour Total": 1390.50, "Total Weight (kg)": 9600.0, "Total Number of weights": 8.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "15m x 20m", "Type": "Structure", "Hire Unit Rate": 4635.00, "Labour Total": 1854.00, "Total Weight (kg)": 12000.0, "Total Number of weights": 10.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "15m x 25m", "Type": "Structure", "Hire Unit Rate": 5793.75, "Labour Total": 2317.50, "Total Weight (kg)": 14400.0, "Total Number of weights": 12.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "15m x 30m", "Type": "Structure", "Hire Unit Rate": 6952.50, "Labour Total": 2781.00, "Total Weight (kg)": 16000.0, "Total Number of weights": 14.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "20m x 5m", "Type": "Structure", "Hire Unit Rate": 2300.00, "Labour Total": 1265.00, "Total Weight (kg)": 6000.0, "Total Number of weights": 28.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "20m x 10m", "Type": "Structure", "Hire Unit Rate": 3990.00, "Labour Total": 1596.00, "Total Weight (kg)": 8000.0, "Total Number of weights": 32.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "20m x 15m", "Type": "Structure", "Hire Unit Rate": 5985.00, "Labour Total": 2394.00, "Total Weight (kg)": 10000.0, "Total Number of weights": 36.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "20m x 20m", "Type": "Structure", "Hire Unit Rate": 7980.00, "Labour Total": 3192.00, "Total Weight (kg)": 12000.0, "Total Number of weights": 40.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "20m x 25m", "Type": "Structure", "Hire Unit Rate": 9975.00, "Labour Total": 3990.00, "Total Weight (kg)": 14000.0, "Total Number of weights": 44.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "20m x 30m", "Type": "Structure", "Hire Unit Rate": 11970.00, "Labour Total": 4788.00, "Total Weight (kg)": 16000.0, "Total Number of weights": 48.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "20m x 35m", "Type": "Structure", "Hire Unit Rate": 13965.00, "Labour Total": 5586.00, "Total Weight (kg)": 18000.0, "Total Number of weights": 52.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "20m x 40m", "Type": "Structure", "Hire Unit Rate": 15960.00, "Labour Total": 6384.00, "Total Weight (kg)": 20000.0, "Total Number of weights": 56.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05}
]

NATIVE_GRANDSTANDS = [
    {"Low": 0, "High": 40, "Staff": 2, "Hours": 4.0, "Total": 1760.0},
    {"Low": 41, "High": 100, "Staff": 3, "Hours": 5.0, "Total": 3300.0},
    {"Low": 101, "High": 149, "Staff": 4, "Hours": 5.5, "Total": 4840.0},
    {"Low": 150, "High": 199, "Staff": 5, "Hours": 6.0, "Total": 6600.0},
    {"Low": 200, "High": 249, "Staff": 5, "Hours": 7.0, "Total": 7700.0},
    {"Low": 250, "High": 299, "Staff": 6, "Hours": 8.0, "Total": 10560.0},
    {"Low": 300, "High": 349, "Staff": 6, "Hours": 9.0, "Total": 11880.0},
    {"Low": 350, "High": 400, "Staff": 6, "Hours": 10.0, "Total": 13200.0}
]

NATIVE_FLOORING = [
    {"Product Name": "I-Trac", "1-Week Rate": 23.40, "4-Week Block": 46.80, "Labour": 4.65, "Weight": 15.0},
    {"Product Name": "I-Trac Ramps (1.07 x1.18)", "1-Week Rate": 42.00, "4-Week Block": 84.00, "Labour": 0.00, "Weight": 0.0},
    {"Product Name": "Supa-Trac", "1-Week Rate": 11.55, "4-Week Block": 25.00, "Labour": 4.65, "Weight": 4.5},
    {"Product Name": "Supa-Trac Edging", "1-Week Rate": 6.70, "4-Week Block": 0.00, "Labour": 0.00, "Weight": 0.0},
    {"Product Name": "Plastorip", "1-Week Rate": 10.15, "4-Week Block": 20.30, "Labour": 3.05, "Weight": 4.0},
    {"Product Name": "Plastorip Edging", "1-Week Rate": 1.65, "4-Week Block": 0.00, "Labour": 0.00, "Weight": 0.0},
    {"Product Name": "Plastorip Corner", "1-Week Rate": 0.00, "4-Week Block": 0.00, "Labour": 0.00, "Weight": 0.0},
    {"Product Name": "Rollout Flooring", "1-Week Rate": 7.10, "4-Week Block": 15.00, "Labour": 3.05, "Weight": 0.0},
    {"Product Name": "Rollout Flooring - Ramps", "1-Week Rate": 6.60, "4-Week Block": 0.00, "Labour": 0.00, "Weight": 0.0},
    {"Product Name": "Rollout Flooring - joiners", "1-Week Rate": 6.60, "4-Week Block": 0.00, "Labour": 0.00, "Weight": 0.0},
    {"Product Name": "Trakmats", "1-Week Rate": 23.20, "4-Week Block": 45.00, "Labour": 5.85, "Weight": 35.0}
]

struct_db = pd.DataFrame(NATIVE_STRUCTURES)
flooring_db = pd.DataFrame(NATIVE_FLOORING)

# ==============================================================================
# PERFORMANCE CACHED PROCESSING ENGINES
# ==============================================================================
@st.cache_data(show_spinner=False, ttl=300)
def fetch_depot_distance(address_string):
    from geopy.geocoders import Nominatim
    from geopy.distance import geodesic
    try:
        custom_agent = f"louis_quoter_v87_{int(time.time())}"
        geolocator = Nominatim(user_agent=custom_agent, timeout=10)
        loc_data = geolocator.geocode(address_string + ", Victoria, Australia")
        if loc_data:
            return round(geodesic((DEPOT_LAT, DEPOT_LON), (loc_data.latitude, loc_data.longitude)).kilometers * 1.15, 1)
    except: pass
    return None

@st.cache_data(show_spinner=False)
def cached_pdf_generator(subtotal, labour, waiver, cartage, grand, weeks, final_pdf_items, structural_math_dict, job_name):
    def clean_text(txt):
        if not txt: return ""
        replacements = {"®": "(R)", "™": "(TM)", "©": "(C)", "└": "->", "—": "-", "–": "-"}
        cleaned = str(txt)
        for char, rep in replacements.items(): cleaned = cleaned.replace(char, rep)
        return cleaned.encode('latin-1', 'replace').decode('latin-1')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text("Louis Quoting Tool - Detailed Calculation Audit"), ln=True, align="C")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, clean_text(f"JOB REF NAME: {job_name.upper()} | DURATION: {weeks} Week(s)"), ln=True, align="C")
    pdf.ln(8)

    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, " 1. HIRE CALCULATIONS SCHEDULE", 0, 1, "L", True)
    
    pdf.set_fill_color(240, 242, 245); pdf.set_text_color(50, 50, 50); pdf.set_font("Arial", "B", 9)
    col_w = [75, 15, 22, 18, 20, 40]
    pdf.cell(col_w[0], 8, " Item Description", 1, 0, "L", True)
    pdf.cell(col_w[1], 8, "Qty", 1, 0, "C", True)
    pdf.cell(col_w[2], 8, "Base Rate", 1, 0, "R", True)
    pdf.cell(col_w[3], 8, "Factor", 1, 0, "C", True)
    pdf.cell(col_w[4], 8, "Disc %", 1, 0, "C", True)
    pdf.cell(col_w[5], 8, "Line Total", 1, 1, "R", True)
    
    pdf.set_text_color(0, 0, 0)
    for item in final_pdf_items:
        pdf.set_font("Arial", "", 9)
        pdf.cell(col_w[0], 8, clean_text(f" {item['Product']}"), 1, 0, "L")
        pdf.cell(col_w[1], 8, f"{item['Qty']:,.0f}", 1, 0, "C")
        pdf.cell(col_w[2], 8, f"${item['Unit Rate']:,.2f}", 1, 0, "R")
        pdf.cell(col_w[3], 8, f"{item['Factor']:g}", 1, 0, "C")
        pdf.cell(col_w[4], 8, f"{item['Discount']:.1f}%", 1, 0, "C")
        pdf.cell(col_w[5], 8, f"${item['Line Total']:,.2f}", 1, 1, "R")
        if item.get("Is_Grandstand"):
            pdf.set_font("Arial", "I", 8); pdf.set_text_color(80, 80, 80)
            pdf.cell(sum(col_w), 6, clean_text(f"    ↳ Pricing Breakdown: {item['Lab_Math']}"), 1, 1, "L")
            pdf.set_text_color(0, 0, 0)

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
        raw_pd = pdf.output(dest='S')
        return raw_pd.encode('latin-1', 'replace') if isinstance(raw_pd, str) else bytes(raw_pd)
    except:
        return bytes(pdf.output())

# ==============================================================================
# SMART LOGIC HOOKS
# ==============================================================================
def matches_smart_query(config_name, query_str):
    if not query_str: return True
    c_clean = str(config_name).lower().replace(" ", "")
    q_clean = str(query_str).lower().replace(" ", "")
    if q_clean in c_clean: return True
    c_norm = re.sub(r'(\d+)m?x(\d+)m?', r'\1x\2', c_clean)
    q_norm = re.sub(r'(\d+)m?x(\d+)m?', r'\1x\2', q_clean)
    if q_norm in c_norm: return True
    q_digits = re.findall(r'\d+', q_clean)
    c_digits = re.findall(r'\d+', c_clean)
    if len(q_digits) >= 2 and len(c_digits) >= 2:
        if q_digits[0] == c_digits[0] and q_digits[1] == c_digits[1]: return True
    return False

def get_item_property(config_name, column_target, fallback_val=0.0):
    matched_row = struct_db[struct_db["Configuration"] == str(config_name).strip()]
    if not matched_row.empty:
        val = matched_row.iloc[0].get(column_target, fallback_val)
        try: return float(val) if not pd.isna(val) else fallback_val
        except: return val if not pd.isna(val) else fallback_val
    return fallback_val

def calculate_dynamic_grandstand_rate(seats_input):
    if seats_input <= 0: return 0.0, "0 seats allocation"
    CHARGE_OUT_RATE = 220.0
    if seats_input <= 50: multiplier = 0.20
    elif seats_input <= 100: multiplier = 0.18
    elif seats_input <= 350: multiplier = 0.16
    else: multiplier = 0.18

    raw_labor_hours = seats_input * multiplier

    if seats_input <= 54: staff = 2
    elif seats_input <= 100: staff = 3
    elif seats_input <= 175: staff = 4
    elif seats_input <= 250: staff = 5
    elif seats_input <= 350: staff = 6
    elif seats_input <= 400: staff = 8
    elif seats_input <= 450: staff = 9
    elif seats_input <= 500: staff = 10
    elif seats_input <= 600: staff = 12
    elif seats_input <= 750: staff = 14
    elif seats_input <= 850: staff = 8
    elif seats_input <= 950: staff = 9
    else: staff = 10

    days = 2 if seats_input >= 800 else 1
    shift_length = math.ceil(((raw_labor_hours / staff) / (2 if days==2 else 1)) * 2) / 2
    total_price = staff * shift_length * days * CHARGE_OUT_RATE
    per_seat_rate = total_price / seats_input

    if days > 1: math_desc = f"{staff} Crew x {shift_length:g} Hrs/Day ({days} Days) @ Base Total ${total_price:,.2f}"
    else: math_desc = f"{staff} Crew x {shift_length:g} Hrs @ Base Total ${total_price:,.2f}"
    return round(per_seat_rate, 2), math_desc

# ==============================================================================
# 5. STREAMLIT INTERNAL STORAGE PERSISTENCE
# ==============================================================================
if 'df' not in st.session_state: 
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount", "Lab_Math", "Lab_Per_Unit", "Base_Hire", "Anchoring", "Override_Rate", "Is_Flooring", "Base_1Wk_Rate", "Base_Block_Rate", "Is_Grandstand"])
if 'km' not in st.session_state: st.session_state.km = 0.0
if 'start_date_val' not in st.session_state: st.session_state.start_date_val = date.today()
if 'reset_key_seed' not in st.session_state: st.session_state.reset_key_seed = 0
if 'site_address_str' not in st.session_state: st.session_state.site_address_str = ""

if 'saved_cartage_mode' not in st.session_state: st.session_state.saved_cartage_mode = "Charge"
if 'saved_labour_mode' not in st.session_state: st.session_state.saved_labour_mode = "Separate"
if 'saved_waiver_mode' not in st.session_state: st.session_state.saved_waiver_mode = "Charge"
if 'overrides_dict' not in st.session_state: st.session_state.overrides_dict = {}

# ==============================================================================
# 6. GLOBAL BASE CONTROLS MOUNT
# ==============================================================================
job_name_input = st.text_input("📝 Active Project / Job Name Reference", value=None, placeholder="Type reference label name...")

c_dt1, c_km_sep = st.columns([1, 1])
start_d = c_dt1.date_input("Start Date", value=st.session_state.start_date_val, format="DD/MM/YYYY", key=f"sd_base_{st.session_state.reset_key_seed}")
st.session_state.start_date_val = start_d
end_d = c_km_sep.date_input("End Date", value=start_d, format="DD/MM/YYYY", key=f"ed_base_{st.session_state.reset_key_seed}")
weeks = math.ceil(((end_d - start_d).days) / 7) or 1

# UPGRADED v87.0: Spinner execution with exception fallback handling so UI never locks up on timeout
input_addr = st.text_input("🏠 Delivery Site Address", placeholder="Type venue address or suburb (e.g. Cranbourne, Victoria)...", key="address_input_box")
if input_addr and input_addr.strip() != st.session_state.site_address_str:
    with st.spinner("🛰️ Pinging routing satellite..."):
        new_dist = fetch_depot_distance(input_addr.strip())
        
    if new_dist is not None:
        st.session_state.km = new_dist
        st.session_state.site_address_str = input_addr.strip()
        st.toast(f"📍 Target verified: {st.session_state.km} KM", icon="✅")
        st.rerun()
    else:
        st.error("⚠️ **Satellite Lookup Failed:** The free mapping server is currently busy or rate-limiting your connection. Please type the distance into the **One-Way KM** box below manually to continue.")
        st.session_state.site_address_str = input_addr.strip() 

st.markdown("**🚛 Active Transport Routing Distance**")
c_km1, c_km2 = st.columns([1, 4])
new_manual_km = c_km1.number_input("One-Way KM", min_value=0.0, value=float(st.session_state.km) if st.session_state.km > 0 else None, placeholder="0.0")
if new_manual_km is not None and new_manual_km != float(st.session_state.km): 
    st.session_state.km = new_manual_km
    st.session_state.site_address_str = "Custom Set Coordinate"
c_km2.info(f"Routing evaluations active at **{st.session_state.km} One-Way KM** tracing from source depot. Duration: {weeks} Week(s).")

l1, l2, l3 = st.columns(3)
cartage_mode = l1.segmented_control("Cartage Math", ["Charge", "Free"], default=st.session_state.saved_cartage_mode)
labour_mode = l2.segmented_control("Labour Math", ["Separate", "Include in Hire", "Free"], default=st.session_state.saved_labour_mode)
waiver_mode = l3.segmented_control("Damage Waiver", ["Charge", "Free"], default=st.session_state.saved_waiver_mode)

# ==============================================================================
# 7. SINGLE HUB COMPONENT WORKSPACE
# ==============================================================================
st.divider()
st.markdown("### ➕ CATALOG COMPONENT HUB")

selected_cat = st.selectbox("Choose Category to Load", ["Marquees", "Flooring", "Grandstands"])

if selected_cat == "Marquees":
    search_query = st.text_input("🔍 Smart Search Marquee Size (e.g. 4x3, 6x3, 15x15):", placeholder="Type structure dimensions here...", key="marq_search_box")
    filtered_df = struct_db.copy()
    if search_query: filtered_df = filtered_df[filtered_df["Configuration"].apply(lambda x: matches_smart_query(x, search_query))]
        
    if not filtered_df.empty:
        target_item = st.selectbox("Discovered configuration options:", filtered_df["Configuration"].tolist(), key="marq_res")
        qty_input = st.number_input("Structure Quantity Count", min_value=1, value=None, placeholder="Type quantity...", key="marq_qty")
        anch_type = st.segmented_control("Anchoring Method Selection", ["Pegged", "Weighted"], default="Pegged", key="marq_anch")
        
        if st.button("Add Structural Configuration") and target_item:
            if qty_input is None:
                st.error("Please insert a target quantity first.")
            else:
                b_hire = get_item_property(target_item, "Hire Unit Rate")
                raw_labour_pool = get_item_property(target_item, "Labour Total")
                total_w = get_item_property(target_item, "Total Weight (kg)")
                
                new_df = pd.DataFrame([{
                    "Qty": qty_input, "Product": target_item, "Unit Rate": b_hire, "Min_Lab": 350,
                    "Raw_Lab": raw_labour_pool * qty_input, "Lab_Math": f"{target_item}: Layout installation setup matrix",
                    "KG": total_w * qty_input, "Is_Marquee": True, "Discount": 0.0, "Lab_Per_Unit": raw_labour_pool,
                    "Base_Hire": b_hire, "Anchoring": anch_type, "Override_Rate": 0.0, "Is_Flooring": False,
                    "Base_1Wk_Rate": b_hire, "Base_Block_Rate": b_hire, "Is_Grandstand": False
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
                
                if anch_type == "Weighted":
                    num_weights = get_item_property(target_item, "Total Number of weights")
                    w_size = get_item_property(target_item, "Weight Size (KG)")
                    w_cost = get_item_property(target_item, "Cost per weight")
                    w_lab = get_item_property(target_item, "Labour Per Weight")
                    calc_w = int(num_weights * qty_input)
                    weight_df = pd.DataFrame([{
                        "Qty": calc_w, "Product": f"{int(w_size)}kg Weights", "Unit Rate": w_cost, "Min_Lab": 0,
                        "Raw_Lab": calc_w * w_lab, "Lab_Math": f"Ballast weights stacking: {calc_w} units x ${w_lab:.2f}",
                        "KG": calc_w * w_size, "Is_Marquee": False, "Discount": 0.0, "Lab_Per_Unit": w_lab,
                        "Base_Hire": w_cost, "Anchoring": "", "Override_Rate": 0.0, "Is_Flooring": False,
                        "Base_1Wk_Rate": w_cost, "Base_Block_Rate": w_cost, "Is_Grandstand": False
                    }])
                    st.session_state.df = pd.concat([st.session_state.df, weight_df], ignore_index=True)
                st.rerun()
    else: st.info("No matching configuration marquee sizes found.")

elif selected_cat == "Flooring":
    floor_options = flooring_db["Product Name"].tolist()
    target_item = st.selectbox("Select Flooring Type Options:", floor_options, key="floor_res")
    f_input_method = st.radio("Input Calculation Method", ["Enter Dimensions (Width x Length)", "Enter Total SQM Directly"], horizontal=True)
    
    f_w_input = 0.0
    if f_input_method == "Enter Dimensions (Width x Length)":
        f_w_input = st.number_input("Width (m)", min_value=0.0, value=None, placeholder="Type width in meters...", key="f_width_cell")
        f_l_input = st.number_input("Length (m)", min_value=0.0, value=None, placeholder="Type length in meters...", key="f_length_cell")
        calculated_sqm = (f_w_input * f_l_input) if (f_w_input and f_l_input) else None
        if calculated_sqm: st.caption(f"💡 Calculated Area Coverage Target = **{calculated_sqm:,.2f} SQM**")
        cov_input = calculated_sqm
    else:
        cov_input = st.number_input("Total Area Square Metres Coverage", min_value=0.0, value=None, placeholder="Type raw SQM area metric...", key="floor_raw_sqm")

    if st.button("Add Flooring Component") and target_item:
        if cov_input is None or cov_input <= 0:
            st.error("Please input metrics first.")
        else:
            match_f = flooring_db[flooring_db["Product Name"] == target_item]
            f_rate = float(match_f.iloc[0]["1-Week Rate"])
            f_block = float(match_f.iloc[0]["4-Week Block"])
            f_lab = float(match_f.iloc[0]["Labour"])
            f_kg = float(match_f.iloc[0]["Weight"])
            
            if "supa" in target_item.lower() and "edging" not in target_item.lower():
                num_sheets_needed = math.ceil(cov_input / 3.0)
                actual_supplied_sqm = num_sheets_needed * 3.0  
                per_sheet_1wk = (actual_supplied_sqm * f_rate) / num_sheets_needed
                per_sheet_block = (actual_supplied_sqm * f_block) / num_sheets_needed
                per_sheet_lab = (actual_supplied_sqm * f_lab) / num_sheets_needed
                per_sheet_kg = (actual_supplied_sqm * f_kg) / num_sheets_needed
                
                new_f_df = pd.DataFrame([{
                    "Qty": num_sheets_needed, "Product": f"{target_item} (3 SQM Sheets)", "Unit Rate": per_sheet_1wk, "Min_Lab": 0, "Raw_Lab": num_sheets_needed * per_sheet_lab,
                    "Lab_Math": f"Supa-Trac Matrix: {num_sheets_needed:,.0f} Sheets (supplying {actual_supplied_sqm:,.2f} SQM) x ${per_sheet_lab:.2f}/sheet", 
                    "KG": num_sheets_needed * per_sheet_kg, "Is_Marquee": False,
                    "Discount": 0.0, "Lab_Per_Unit": 0, "Base_Hire": per_sheet_1wk, "Anchoring": "", "Override_Rate": 0.0, "Is_Flooring": True,
                    "Base_1Wk_Rate": per_sheet_1wk, "Base_Block_Rate": per_sheet_block, "Is_Grandstand": False
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_f_df], ignore_index=True)
                
                if f_input_method == "Enter Dimensions (Width x Length)" and f_w_input and f_w_input > 0:
                    match_e = flooring_db[flooring_db["Product Name"] == "Supa-Trac Edging"]
                    if not match_e.empty:
                        e_rate_per_m = float(match_e.iloc[0]["1-Week Rate"])
                        e_block_per_m = float(match_e.iloc[0]["4-Week Block"])
                        e_lab_per_m = float(match_e.iloc[0]["Labour"])
                        e_kg_per_m = float(match_e.iloc[0]["Weight"])
                        
                        num_e_pieces = math.ceil(f_w_input / 0.22)
                        e_actual_lm = num_e_pieces * 0.22
                        per_pce_1wk = e_rate_per_m * 0.22
                        per_pce_block = e_block_per_m * 0.22
                        per_pce_lab = e_lab_per_m * 0.22
                        per_pce_kg = e_kg_per_m * 0.22
                        
                        e_df = pd.DataFrame([{
                            "Qty": num_e_pieces, "Product": f"Supa-Trac Edging ({num_e_pieces:,.0f} Pieces)", "Unit Rate": per_pce_1wk, "Min_Lab": 0, "Raw_Lab": num_e_pieces * per_pce_lab,
                            "Lab_Math": f"Front Width Edging: {num_e_pieces:,.0f} Pieces ({e_actual_lm:,.2f} L/M) x ${e_rate_per_m:.2f}/m", 
                            "KG": num_e_pieces * per_pce_kg, "Is_Marquee": False,
                            "Discount": 0.0, "Lab_Per_Unit": 0, "Base_Hire": per_pce_1wk, "Anchoring": "", "Override_Rate": 0.0, "Is_Flooring": True,
                            "Base_1Wk_Rate": per_pce_1wk, "Base_Block_Rate": per_pce_block, "Is_Grandstand": False
                        }])
                        st.session_state.df = pd.concat([st.session_state.df, e_df], ignore_index=True)

            else:
                new_f_df = pd.DataFrame([{
                    "Qty": cov_input, "Product": target_item, "Unit Rate": f_rate, "Min_Lab": 0, "Raw_Lab": cov_input * f_lab,
                    "Lab_Math": f"{target_item}: {cov_input:,.0f} SQM area x ${f_lab:.2f}", "KG": cov_input * f_kg, "Is_Marquee": False,
                    "Discount": 0.0, "Lab_Per_Unit": 0, "Base_Hire": f_rate, "Anchoring": "", "Override_Rate": 0.0, "Is_Flooring": True,
                    "Base_1Wk_Rate": f_rate, "Base_Block_Rate": f_block, "Is_Grandstand": False
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_f_df], ignore_index=True)
            st.rerun()

elif selected_cat == "Grandstands":
    seats_input = st.number_input("Total Seat Capacity Requirements Count", min_value=1, value=None, placeholder="Type total quantity of seats...", key="gs_qty")
    
    if st.button("Add Grandstand Configuration Layout"):
        if seats_input is None or seats_input <= 0:
            st.error("Please supply a valid seat capacity count first.")
        else:
            per_seat_rate, math_desc_str = calculate_dynamic_grandstand_rate(seats_input)
            new_df = pd.DataFrame([{
                "Qty": seats_input, "Product": f"Standard Seating Grandstand ({seats_input} Seats)", "Unit Rate": per_seat_rate, "Min_Lab": 0,
                "Raw_Lab": 0.0, "Lab_Math": math_desc_str, "KG": seats_input * 25.0, "Is_Marquee": False,
                "Discount": 0.0, "Lab_Per_Unit": 0.0, "Base_Hire": per_seat_rate, "Anchoring": "", "Override_Rate": 0.0, "Is_Flooring": False,
                "Base_1Wk_Rate": per_seat_rate, "Base_Block_Rate": per_seat_rate, "Is_Grandstand": True
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
            st.rerun()

# ==============================================================================
# QUOTE SUMMARY ENGINE RENDER DATA LOOPS 
# ==============================================================================
if st.session_state.df is not None and not st.session_state.df.empty:
    st.divider()
    st.subheader("📝 QUOTE SUMMARY")
    
    st.session_state.df.reset_index(drop=True, inplace=True)
    
    h_col0, h_col1, h_col2, h_col3, h_col_f, h_col4, h_col4b, h_col5 = st.columns([0.4, 2.6, 0.9, 1.1, 0.8, 1.0, 1.1, 1.3])
    h_col1.markdown("<div class='summary-hdr'>Item Description</div>", unsafe_allow_html=True)
    h_col2.markdown("<div class='summary-hdr'>Qty (Editable)</div>", unsafe_allow_html=True)
    h_col3.markdown("<div class='summary-hdr'>Base Rate</div>", unsafe_allow_html=True)
    h_col_f.markdown("<div class='summary-hdr'>Factor</div>", unsafe_allow_html=True)
    h_col4.markdown("<div class='summary-hdr'>Disc %</div>", unsafe_allow_html=True)
    h_col4b.markdown("<div class='summary-hdr'>Override Rate</div>", unsafe_allow_html=True)
    h_col5.markdown("<div class='summary-hdr' style='text-align: right;'>Subtotal</div>", unsafe_allow_html=True)

    h_tot_c, total_kg = 0.0, 0.0
    waiver_eligible_total = 0.0
    final_pdf_items = []
    
    for idx, row in st.session_state.df.iterrows():
        override = row.get("Override_Rate", 0.0)
        qty, dm = row["Qty"], (1 - (row["Discount"]/100))
        total_kg += row["KG"]
        
        if row.get("Is_Flooring"):
            if weeks >= 4 and row.get("Base_Block_Rate", 0) > 0:
                factor = float(math.ceil(weeks / 4.0)); display_rate = row["Base_Block_Rate"]
            else:
                factor = float(weeks); display_rate = row["Base_1Wk_Rate"]
        elif row.get("Is_Marquee", False):
            display_rate = row["Unit Rate"]
            factor = 1.0 + 0.5 * (weeks - 1) if weeks > 1 else 1.0
        elif row.get("Is_Grandstand", False):
            display_rate = row["Unit Rate"]
            factor = 1.0 + 0.5 * (weeks - 2) if weeks > 2 else 1.0
        else:
            display_rate = row["Unit Rate"]; factor = float(weeks)

        if override > 0:
            display_rate = override; factor = 1.0

        wk1_t = qty * display_rate * factor * dm
        h_tot_c += wk1_t
        
        if not row.get("Is_Grandstand", False):
            waiver_eligible_total += wk1_t
            
        prod_display = str(row['Product'])
        if row.get('Anchoring'): prod_display += f" ({row['Anchoring']})"
        
        final_pdf_items.append({
            "Product": prod_display, "Qty": qty, "Unit Rate": display_rate,
            "Factor": factor, "Discount": row["Discount"], "Line Total": wk1_t,
            "Is_Grandstand": row.get("Is_Grandstand", False), "Lab_Math": row.get("Lab_Math", "")
        })
        
        c0, c1, c2, c3, c_f, c4, c4b, c5 = st.columns([0.4, 2.6, 0.9, 1.1, 0.8, 1.0, 1.1, 1.3])
        if c0.button("🗑️", key=f"sdel_{idx}"):
            st.session_state.df.drop(idx, inplace=True)
            st.session_state.df.reset_index(drop=True, inplace=True)
            st.rerun()
            
        c1.markdown(f"<div class='item-text'>{prod_display}</div>", unsafe_allow_html=True)
        
        col_has_changes = False
        new_qty = c2.number_input("QtyBox", min_value=0.0, value=float(qty), key=f"sqty_{idx}", label_visibility="collapsed")
        c3.write(f"${display_rate:,.2f}")
        c_f.write(f"{factor:g}")
        
        new_disc = c4.number_input("Disc %", 0.0, 100.0, value=None if float(row["Discount"]) == 0.0 else float(row["Discount"]), placeholder="0%", key=f"sd_{idx}", label_visibility="collapsed")
        new_override = c4b.number_input("Override", 0.0, 5000.0, value=None if float(row.get("Override_Rate", 0.0)) == 0.0 else float(row.get("Override_Rate", 0.0)), placeholder="Override...", key=f"so_{idx}", label_visibility="collapsed")
        c5.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700;'>${wk1_t:,.2f}</div>", unsafe_allow_html=True)

        if new_qty != float(qty):
            st.session_state.df.at[idx, "Qty"] = new_qty
            if row.get("Is_Marquee"):
                for w_idx, w_row in st.session_state.df.iterrows():
                    if "Weights" in w_row["Product"]:
                        st.session_state.df.at[w_idx, "Qty"] = int(get_item_property(row["Product"], "Total Number of weights") * new_qty)
            col_has_changes = True

        eval_disc = new_disc if new_disc is not None else 0.0
        if eval_disc != row["Discount"]:
            st.session_state.df.at[idx, "Discount"] = eval_disc
            col_has_changes = True
            
        eval_ovr = new_override if new_override is not None else 0.0
        if eval_ovr != row.get("Override_Rate", 0.0):
            st.session_state.df.at[idx, "Override_Rate"] = eval_ovr
            col_has_changes = True
            
        if col_has_changes: st.rerun()

    min_trucks = math.ceil(total_kg / 6000) or 1
    saved_trk_count = st.session_state.overrides_dict.get("logistics_truck_allocation_count_scalar", float(min_trucks))
    trks = int(saved_trk_count)

    raw_lab_pool = st.session_state.df["Raw_Lab"].sum()
    auto_cartage_total = trks * st.session_state.km * 4 * 3.50 if cartage_mode == "Charge" else 0
    auto_waiver_total = waiver_eligible_total * 0.07 if waiver_mode == "Charge" else 0

    # ==============================================================================
    # 9. MANUAL OVERRIDES GRID
    # ==============================================================================
    st.divider(); st.markdown("### 🛠️ MANUAL LOGISTICS OVERRIDES")
    
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
                
                with st.container(border=True):
                    r_c1, r_c2, r_c3 = st.columns([3, 1.5, 1.5])
                    r_c1.markdown(f"**👷 Labour: {p_label}**<br><span style='color:gray; font-size:14px;'>{math_hint_str}</span>", unsafe_allow_html=True)
                    new_input_val = r_c2.number_input("Override", min_value=0.0, value=None if saved_override_val < 0 else float(saved_override_val), placeholder=f"Auto: ${auto_val:,.2f}", key=f"f_l_{idx}", label_visibility="collapsed")
                    actual_l_val = new_input_val if new_input_val is not None else auto_val
                    r_c3.markdown(f"<h3 style='text-align: right; margin-top: 0; color: #1E88E5;'>${actual_l_val:,.2f}</h3>", unsafe_allow_html=True)
                    
                    final_labour_pool_sum += actual_l_val
                    target_saved_flag = new_input_val if new_input_val is not None else -1.0
                    if target_saved_flag != saved_override_val:
                        st.session_state.overrides_dict[lbl_key] = target_saved_flag; has_changes_detected = True

        if final_labour_pool_sum < 350.00 and final_labour_pool_sum > 0:
            floor_topup = 350.00 - final_labour_pool_sum
            with st.container(border=True):
                r_f1, r_f2, r_f3 = st.columns([3, 1.5, 1.5])
                r_f1.markdown("**🛡️ Labour Minimum Floor Buffer**<br><span style='color:gray; font-size:14px;'>Automatic margin top-up</span>", unsafe_allow_html=True)
                r_f3.markdown(f"<h3 style='text-align: right; margin-top: 0; color: #757575;'>${floor_topup:,.2f}</h3>", unsafe_allow_html=True)
            final_labour_pool_sum = 350.00

        lab_global_key = "labour_total_global_override"
        saved_lab_global = st.session_state.overrides_dict.get(lab_global_key, -1.0)
        with st.container(border=True):
            rl1, rl2, rl3 = st.columns([3, 1.5, 1.5])
            rl1.markdown(f"**🏗️ Total Master Labour Override**<br><span style='color:gray; font-size:14px;'>Overrides all item labour & minimum floors. Default: ${final_labour_pool_sum:,.2f}</span>", unsafe_allow_html=True)
            new_lab_global = rl2.number_input("InputLabGlobal", min_value=0.0, value=None if saved_lab_global < 0 else float(saved_lab_global), placeholder=f"Auto: ${final_labour_pool_sum:,.2f}", key="f_lab_global", label_visibility="collapsed")
            if new_lab_global is not None:
                final_labour_pool_sum = new_lab_global
            rl3.markdown(f"<h3 style='text-align: right; margin-top: 0; color: #1E88E5;'>${final_labour_pool_sum:,.2f}</h3>", unsafe_allow_html=True)
            target_lab_global = new_lab_global if new_lab_global is not None else -1.0
            if target_lab_global != saved_lab_global:
                st.session_state.overrides_dict[lab_global_key] = target_lab_global; has_changes_detected = True

    else: final_labour_pool_sum = 0.0

    with st.container(border=True):
        r_trk1, r_trk2, r_trk3 = st.columns([3, 1.5, 1.5])
        r_trk1.markdown(f"**🚛 Logistics: Active Truck Count**<br><span style='color:gray; font-size:14px;'>Calculated spatial requirement: {min_trucks} truck(s)</span>", unsafe_allow_html=True)
        new_trk_count = r_trk2.number_input("TruckInputBox", min_value=float(min_trucks), step=1.0, value=None if saved_trk_count == float(min_trucks) else float(trks), placeholder=f"Auto: {min_trucks}", key="f_trk_scalar_cell", label_visibility="collapsed")
        eval_trks = new_trk_count if new_trk_count is not None else float(min_trucks)
        r_trk3.markdown(f"<h3 style='text-align: right; margin-top: 0; color: #1E88E5;'>{int(eval_trks)} Truck(s)</h3>", unsafe_allow_html=True)
        if eval_trks != float(trks):
            st.session_state.overrides_dict["logistics_truck_allocation_count_scalar"] = eval_trks; has_changes_detected = True

    cart_key = "logistics_cartage_freight_global"
    saved_cart_override = st.session_state.overrides_dict.get(cart_key, -1.0)
    with st.container(border=True):
        r_t1, r_t2, r_t3 = st.columns([3, 1.5, 1.5])
        r_t1.markdown(f"**📦 Logistics: Cartage Freight Fee**<br><span style='color:gray; font-size:14px;'>Base rate: {trks} trucks x {st.session_state.km}km x 4 trips x $3.50/km</span>", unsafe_allow_html=True)
        new_cart_val = r_t2.number_input("InputC", min_value=0.0, value=None if saved_cart_override < 0 else float(saved_cart_override), placeholder=f"Auto: ${auto_cartage_total:,.2f}", key="f_c_global", label_visibility="collapsed")
        final_cartage_sum = new_cart_val if new_cart_val is not None else auto_cartage_total
        r_t3.markdown(f"<h3 style='text-align: right; margin-top: 0; color: #1E88E5;'>${final_cartage_sum:,.2f}</h3>", unsafe_allow_html=True)
        target_cart_flag = new_cart_val if new_cart_val is not None else -1.0
        if target_cart_flag != saved_cart_override: st.session_state.overrides_dict[cart_key] = target_cart_flag; has_changes_detected = True

    waiv_key = "damage_waiver_insurance_global"
    saved_waiv_override = st.session_state.overrides_dict.get(waiv_key, -1.0)
    with st.container(border=True):
        r_w1, r_w2, r_w3 = st.columns([3, 1.5, 1.5])
        r_w1.markdown(f"**🛡️ Waiver: Equipment Damage Indemnity**<br><span style='color:gray; font-size:14px;'>Default: ${waiver_eligible_total:,.2f} eligible product hire x 7%</span>", unsafe_allow_html=True)
        new_waiv_val = r_w2.number_input("InputW", min_value=0.0, value=None if saved_waiv_override < 0 else float(saved_waiv_override), placeholder=f"Auto: ${auto_waiver_total:,.2f}", key="f_w_global", label_visibility="collapsed")
        final_waiver_sum = new_waiv_val if new_waiv_val is not None else auto_waiver_total
        r_w3.markdown(f"<h3 style='text-align: right; margin-top: 0; color: #1E88E5;'>${final_waiver_sum:,.2f}</h3>", unsafe_allow_html=True)
        target_waiv_flag = new_waiv_val if new_waiv_val is not None else -1.0
        if target_waiv_flag != saved_waiv_override: st.session_state.overrides_dict[waiv_key] = target_waiv_flag; has_changes_detected = True

    if has_changes_detected: st.rerun()

    # Footer metric cards Display
    st.divider(); m = st.columns(6)
    m[0].metric("HIRE COST", f"${round(h_tot_c, 2):,}")
    m[1].metric("LABOUR", f"${round(final_labour_pool_sum, 2):,}")
    m[2].metric("WAIVER", f"${round(final_waiver_sum, 2):,}")
    m[3].metric("CARTAGE", f"${round(final_cartage_sum, 2):,}")
    m[4].metric("WEIGHT", f"{round(total_kg, 0):}kg")
    m[5].metric("TRUCKS", f"{trks}")
    
    grand_total_calc = h_tot_c + final_labour_pool_sum + final_waiver_sum + final_cartage_sum
    st.markdown(f"<div class='gt-banner'>GRAND TOTAL (EX GST): ${grand_total_calc:,.2f}</div>", unsafe_allow_html=True)
    
    structural_math_dict = {"LABOUR": [], "LOGISTICS": [], "DAMAGE WAIVER": []}
    
    if st.session_state.overrides_dict.get("labour_total_global_override", -1.0) >= 0:
        structural_math_dict["LABOUR"].append("Custom Master Labour Override Applied")
        structural_math_dict["LABOUR"].append(f"Total Applied = ${final_labour_pool_sum:,.2f}")
    else:
        for idx, row in st.session_state.df.iterrows():
            if row.get('Raw_Lab', 0.0) > 0.0:
                lbl_key = f"lab_ovr_{row['Product']}_{idx}"
                saved_val = st.session_state.overrides_dict.get(lbl_key, -1.0)
                l_val = saved_val if saved_val >= 0 else float(row['Raw_Lab'])
                math_hint = row.get("Lab_Math", "")
                if math_hint: structural_math_dict["LABOUR"].append(f"{row['Product']} | {math_hint} = ${l_val:,.2f}")
                else: structural_math_dict["LABOUR"].append(f"{row['Product']} = ${l_val:,.2f}")
                    
        if final_labour_pool_sum == 350.00 and raw_lab_pool < 350.00:
            structural_math_dict["LABOUR"].append("Minimum Floor Buffer Adjustment top-up applied")
        structural_math_dict["LABOUR"].append(f"Total Applied = ${final_labour_pool_sum:,.2f}")
        
    structural_math_dict["LOGISTICS"].append(f"{trks} Trucks x {st.session_state.km}km x 4 x $3.50 = ${final_cartage_sum:,.2f}")
    structural_math_dict["DAMAGE WAIVER"].append(f"${waiver_eligible_total:,.2f} x 7% = ${final_waiver_sum:,.2f}")

# ==============================================================================
# 10. DOWNLOAD ZONE
# ==============================================================================
    st.markdown("")  
    pdf_b = cached_pdf_generator(h_tot_c, final_labour_pool_sum, final_waiver_sum, final_cartage_sum, grand_total_calc, weeks, final_pdf_items, structural_math_dict, job_name_input or "Project_Quote")
    st.download_button("📥 DOWNLOAD DETAILED AUDIT PDF", pdf_b, file_name=f"{(job_name_input or 'Quote').replace(' ', '_')}_Analysis.pdf", mime="application/pdf", use_container_width=True)
