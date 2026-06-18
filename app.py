import streamlit as st
import math
import pandas as pd
from fpdf import FPDF
import re
import json
import os
import io  # Streamlines memory buffers for native Excel and PDF exports
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# ==============================================================================
# 0. INITIAL CONFIG & LOCAL DATA VAULT ARCHITECTURE
# ==============================================================================
st.set_page_config(page_title="Louis Master Quoter", layout="wide")

DEFAULT_EXCEL = "No_Fuss_Master_Rate_Template.xlsx"
DEPOT_LAT = -38.1171
DEPOT_LON = -145.2442

# ==============================================================================
# SMART RE REGEX DIMENSION MATCHING HOOK
# ==============================================================================
def matches_smart_query(config_name, query_str):
    if not query_str:
        return True
    c_clean = str(config_name).lower().replace(" ", "")
    q_clean = str(query_str).lower().replace(" ", "")
    
    if q_clean in c_clean:
        return True
        
    c_norm = re.sub(r'(\d+)m?x(\d+)m?', r'\1x\2', c_clean)
    q_norm = re.sub(r'(\d+)m?x(\d+)m?', r'\1x\2', q_clean)
    
    if q_norm in c_norm:
        return True
        
    q_digits = re.findall(r'\d+', q_clean)
    c_digits = re.findall(r'\d+', c_clean)
    if len(q_digits) >= 2 and len(c_digits) >= 2:
        if q_digits[0] == c_digits[0] and q_digits[1] == c_digits[1]:
            return True
            
    return False

# ==============================================================================
# UNIFIED EXCEL LOADER: Scans single workbook tabs by keyword look-ups
# ==============================================================================
st.sidebar.markdown("### 📊 MASTER EXCEL DATABASE")
uploaded_excel = st.sidebar.file_uploader("Upload Master Rate Excel Document", type=["xlsx", "xlsm"])

@st.cache_data(ttl=5)
def parse_unified_database(uploaded_file):
    db_out = {"structures": None, "grandstands": None, "flooring": None, "logistics": None}
    target_file = uploaded_file if uploaded_file is not None else (DEFAULT_EXCEL if os.path.exists(DEFAULT_EXCEL) else None)
    
    if target_file is not None:
        try:
            xl = pd.ExcelFile(target_file)
            sheets = xl.sheet_names
            
            s_sheet = [s for s in sheets if "structure" in s.lower() or "4." in s.lower()]
            g_sheet = [s for s in sheets if "grandstand" in s.lower() or "5." in s.lower()]
            f_sheet = [s for s in sheets if "floor" in s.lower() or "2." in s.lower()]
            l_sheet = [s for s in sheets if "logis" in s.lower() or "1." in s.lower()]
            
            if s_sheet:
                df = xl.parse(s_sheet[0])
                df.columns = [c.strip() for c in df.columns]
                if "Configuration" in df.columns:
                    df["Configuration"] = df["Configuration"].astype(str).str.strip()
                db_out["structures"] = df
                
            if g_sheet:
                df = xl.parse(g_sheet[0])
                df.columns = [c.strip() for c in df.columns]
                db_out["grandstands"] = df
                
            if f_sheet:
                df = xl.parse(f_sheet[0])
                df.columns = [c.strip() for c in df.columns]
                db_out["flooring"] = df
                
            if l_sheet:
                df = xl.parse(l_sheet[0])
                df.columns = [c.strip() for c in df.columns]
                db_out["logistics"] = df
                
            return db_out
        except Exception as e:
            st.sidebar.error(f"Excel Parse Bypass Error: {str(e)}")
            
    return db_out

master_db = parse_unified_database(uploaded_excel)
struct_db = master_db["structures"]
grandstand_db = master_db["grandstands"]
flooring_db = master_db["flooring"]

def get_item_property(config_name, column_target, fallback_val=0.0):
    if struct_db is not None and "Configuration" in struct_db.columns:
        matched_row = struct_db[struct_db["Configuration"] == str(config_name).strip()]
        if not matched_row.empty:
            val = matched_row.iloc[0].get(column_target, fallback_val)
            try:
                return float(val) if not pd.isna(val) else fallback_val
            except:
                return val if not pd.isna(val) else fallback_val
    return fallback_val

# ==============================================================================
# 2. SEATING BRACKET ENGINE: Total Labour / Capacity Cost-Per-Seat Allocator
# ==============================================================================
def calculate_dynamic_grandstand_rate(seats_input):
    if seats_input <= 0:
        return 0.0, "0 seats allocation"
        
    if grandstand_db is not None and "Max_Seats" in grandstand_db.columns:
        tot_col = [c for c in grandstand_db.columns if "total" in c.lower() or "labour" in c.lower() or "cost" in c.lower()]
        target_col = tot_col[0] if tot_col else grandstand_db.columns[3]
        
        for idx, row in grandstand_db.iterrows():
            try:
                bracket_str = str(row["Max_Seats"]).strip()
                if '-' in bracket_str:
                    low, high = map(int, bracket_str.split('-'))
                    if low <= seats_input <= high:
                        total_labour_cost = float(row[target_col])
                        per_seat_rate = total_labour_cost / seats_input
                        return round(per_seat_rate, 2), f"Seating Matrix: ${total_labour_cost:,.2f} / {seats_input} seats"
            except: pass
            
    fallback_matrix = [(0, 40, 880.0), (41, 100, 1650.0), (101, 149, 2420.0), (150, 199, 3300.0), (200, 249, 3850.0), (250, 299, 5280.0), (300, 349, 5940.0), (350, 400, 6600.0)]
    for low, high, total_lab in fallback_matrix:
        if low <= seats_input <= high:
            return round(total_lab / seats_input, 2), f"Backup Matrix Bracket {low}-{high}: ${total_lab:,.2f} / {seats_input} seats"
            
    return 16.50, f"Standard base per-seat matrix fallback rate calculation applied"

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

def create_calculation_pdf(subtotal, labour, waiver, cartage, grand, weeks, item_items_list, structural_math_dict, status):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text("Louis Quoting Tool - Detailed Calculation Audit"), ln=True, align="C")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, clean_text(f"STATUS: {status.upper()} | DURATION: {weeks} Week(s)"), ln=True, align="C")
    pdf.ln(8)

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
    for item in item_items_list:
        dm = (1 - (item.get('Discount', 0.0)/100))
        display_unit_rate = item.get('Override_Rate', 0.0) if item.get('Override_Rate', 0.0) > 0 else item['Unit Rate']
        w1_total = (item['Qty'] * display_unit_rate) * dm
        pdf.cell(col_w[0], 8, clean_text(f" {item['Product']} (Wk 1 Base)"), 1, 0, "L")
        pdf.cell(col_w[1], 8, f"{item['Qty']:,.0f}", 1, 0, "C")
        pdf.cell(col_w[2], 8, f"${display_unit_rate:,.2f}", 1, 0, "R")
        pdf.cell(col_w[3], 8, f"{item.get('Discount', 0.0):.1f}%", 1, 0, "C")
        pdf.cell(col_w[4], 8, f"${w1_total:,.2f}", 1, 1, "R")

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

FLOORING_CATALOG_FALLBACK = {
    "I-Trac": {"rate": 23.40, "block": 46.80, "lab_fix": 4.65, "kg": 15.0},
    "Supa-Trac": {"rate": 11.55, "block": 25.00, "lab_fix": 4.65, "kg": 4.5},
    "Plastorip": {"rate": 10.15, "block": 20.30, "lab_fix": 3.05, "kg": 4.0},
    "Trakmats": {"rate": 23.20, "block": 45.00, "lab_fix": 5.85, "kg": 35.0}
}
STAGES = ["Quoted", "Accepted", "Paid", "On Hire", "Returned", "Cancelled"]
STAGE_COLORS = {"Quoted": "#FF9100", "Accepted": "#00E676", "Paid": "#00B8D4", "On Hire": "#D500F9", "Returned": "#757575", "Cancelled": "#263238"}

# ==============================================================================
# 5. STREAMLIT INTERNAL STORAGE PERSISTENCE
# ==============================================================================
if 'df' not in st.session_state: 
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount", "Lab_Math", "Lab_Per_Unit", "Base_Hire", "Anchoring", "Override_Rate"])
if 'status' not in st.session_state: st.session_state.status = "Quoted"
if 'km' not in st.session_state: st.session_state.km = 0.0
if 'truck_override' not in st.session_state: st.session_state.truck_override = 0
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
st.session_state.status = st.selectbox("Stage", STAGES, index=STAGES.index(st.session_state.status) if st.session_state.status in STAGES else 0)
st.markdown(f"<div style='height: 14px; background-color: {STAGE_COLORS[st.session_state.status]}; border-radius: 6px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

c_dt1, c_km_sep = st.columns([1, 1])
start_d = c_dt1.date_input("Start Date", value=st.session_state.start_date_val, key=f"sd_base_{st.session_state.reset_key_seed}")
st.session_state.start_date_val = start_d
end_d = c_km_sep.date_input("End Date", value=start_d, key=f"ed_base_{st.session_state.reset_key_seed}")
weeks = math.ceil(((end_d - start_d).days) / 7) or 1

input_addr = st.text_input("🏠 Delivery Site Address", value=st.session_state.site_address_str, placeholder="Type venue address or suburb...")
if input_addr.strip() != st.session_state.site_address_str:
    st.session_state.site_address_str = input_addr.strip()
    try:
        geolocator = Nominatim(user_agent="louis_quoter_v57", timeout=5)
        loc_data = geolocator.geocode(input_addr.strip() + ", Victoria, Australia")
        if loc_data:
            st.session_state.km = round(geodesic((DEPOT_LAT, DEPOT_LON), (loc_data.latitude, loc_data.longitude)).kilometers * 1.15, 1)
            st.toast(f"📍 Target verified: {st.session_state.km} KM", icon="✅")
            st.rerun()
    except: pass

st.markdown("**🚛 Active Transport Routing Distance**")
c_km1, c_km2 = st.columns([1, 4])
new_manual_km = c_km1.number_input("One-Way KM", min_value=0.0, value=float(st.session_state.km))
if new_manual_km != float(st.session_state.km): st.session_state.km = new_manual_km
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

selected_cat = st.selectbox("Choose Category to Load", ["marquees", "flooring", "grandstands"])

if selected_cat == "marquees":
    if struct_db is not None:
        search_query = st.text_input("🔍 Smart Search Marquee Size (e.g. 4x3, 6x3, 15x15):", placeholder="Type structure dimensions here...", key="marq_search_box")
        filtered_df = struct_db[struct_db["Type"].str.lower().str.contains("marquee", na=False) | struct_db["Type"].str.lower().str.contains("structure", na=False)]
        
        if search_query:
            filtered_df = filtered_df[filtered_df["Configuration"].apply(lambda x: matches_smart_query(x, search_query))]
            
        if not filtered_df.empty:
            target_item = st.selectbox("Discovered configuration options:", filtered_df["Configuration"].tolist(), key="marq_res")
            qty_input = st.number_input("Structure Quantity Count", min_value=1, value=None, placeholder="Type quantity...", key="marq_qty")
            anch_type = st.segmented_control("Anchoring Method Selection", ["Pegged", "Weighted"], default="Pegged", key="marq_anch")
            
            if st.button("Add Structural Configuration") and target_item:
                if qty_input is None:
                    st.error("Please insert a target quantity first.")
                else:
                    b_hire = get_item_property(target_item, "Hire Unit Rate", fallback_val=0.0)
                    if b_hire <= 0: b_hire = get_item_property(target_item, "Total Hire Rate", fallback_val=198.45)
                    raw_labour_pool = get_item_property(target_item, "Labour Total ", fallback_val=350.0)
                    total_w = get_item_property(target_item, "Total Weight (kg)", fallback_val=480.0)
                    
                    new_df = pd.DataFrame([{
                        "Qty": qty_input, "Product": target_item, "Unit Rate": b_hire, "Min_Lab": 350,
                        "Raw_Lab": raw_labour_pool * qty_input, "Lab_Math": f"{target_item}: Layout installation setup matrix",
                        "KG": total_w * qty_input, "Is_Marquee": True, "Discount": 0.0, "Lab_Per_Unit": raw_labour_pool,
                        "Base_Hire": b_hire, "Anchoring": anch_type, "Override_Rate": 0.0
                    }])
                    st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
                    
                    if anch_type == "Weighted":
                        num_weights = get_item_property(target_item, "Total Number of weights ", fallback_val=16.0)
                        w_size = get_item_property(target_item, "Weight Size (KG) ", fallback_val=30.0)
                        w_cost = get_item_property(target_item, "Cost per weight ", fallback_val=6.60)
                        w_lab = get_item_property(target_item, "Labour Per Weight ", fallback_val=1.65)
                        
                        calc_w = int(num_weights * qty_input)
                        weight_df = pd.DataFrame([{
                            "Qty": calc_w, "Product": f"{int(w_size)}kg Weights", "Unit Rate": w_cost, "Min_Lab": 0,
                            "Raw_Lab": calc_w * w_lab, "Lab_Math": f"Ballast weights stacking: {calc_w} units x ${w_lab:.2f}",
                            "KG": calc_w * w_size, "Is_Marquee": False, "Discount": 0.0, "Lab_Per_Unit": w_lab,
                            "Base_Hire": w_cost, "Anchoring": "", "Override_Rate": 0.0
                        }])
                        st.session_state.df = pd.concat([st.session_state.df, weight_df], ignore_index=True)
                    st.rerun()
        else: st.info("No matching configuration rows found.")
    else: st.info("Structures master sheet catalog missing from environment context.")

elif selected_cat == "flooring":
    if flooring_db is not None and "Product Name" in flooring_db.columns:
        floor_options = flooring_db["Product Name"].dropna().tolist()
    else:
        floor_options = list(FLOORING_CATALOG_FALLBACK.keys())
        
    target_item = st.selectbox("Select Flooring Type Options:", floor_options, key="floor_res")
    f_input_method = st.radio("Input Calculation Method", ["Enter Dimensions (Width x Length)", "Enter Total SQM Directly"], horizontal=True)
    
    if f_input_method == "Enter Dimensions (Width x Length)":
        f_w_input = st.number_input("Width (m)", min_value=0.0, value=None, placeholder="Type width in meters...", key="f_width_cell")
        f_l_input = st.number_input("Length (m)", min_value=0.0, value=None, placeholder="Type length in meters...", key="f_length_cell")
        calculated_sqm = (f_w_input * f_l_input) if (f_w_input and f_l_input) else None
        if calculated_sqm:
            st.caption(f"💡 Calculated Area Coverage Target = **{calculated_sqm:,.2f} SQM**")
        cov_input = calculated_sqm
    else:
        cov_input = st.number_input("Total Area Square Metres Coverage", min_value=0.0, value=None, placeholder="Type raw SQM area metric...", key="floor_raw_sqm")

    if st.button("Add Flooring Component") and target_item:
        if cov_input is None or cov_input <= 0:
            st.error("Please input width/length metrics or total SQM figures first.")
        else:
            if flooring_db is not None:
                match_f = flooring_db[flooring_db["Product Name"] == target_item]
                f_rate = float(match_f.iloc[0].get("1-Week Rate ($/sqm)", 11.55))
                f_block = float(match_f.iloc[0].get("4-Week Block ($)", 25.00))
                f_lab = float(match_f.iloc[0].get("Labour ($/sqm)", 4.65))
                f_kg = float(match_f.iloc[0].get("Weight (kg/sqm)", 4.5))
                if math.isnan(f_kg): f_kg = FLOORING_CATALOG_FALLBACK.get(target_item, {}).get("kg", 4.5)
            else:
                fd = FLOORING_CATALOG_FALLBACK.get(target_item, {"rate": 11.55, "block": 25.00, "lab_fix": 4.65, "kg": 4.5})
                f_rate, f_block, f_lab, f_kg = fd["rate"], fd.get("block", 0), fd["lab_fix"], fd["kg"]
                
            base_h = f_block if (weeks >= 4 and f_block > 0) else f_rate
            
            final_item_label_name = target_item
            final_billing_qty = cov_input
            
            if "supa-tr" in target_item.lower() or "supat_r" in target_item.lower():
                num_sheets_needed = math.ceil(cov_input / 3.0)
                final_billing_qty = num_sheets_needed * 3.0  
                final_item_label_name = f"{target_item} [{num_sheets_needed:,.0f} Sheets of 3 SQM]"
                lab_desc = f"Supa-Trac Sheet Matrix: {num_sheets_needed:,.0f} Sheets ({final_billing_qty:,.0f} SQM total) x ${f_lab:.2f}"
            else:
                lab_desc = f"{target_item}: {cov_input:,.0f} SQM area x ${f_lab:.2f}"
                
            new_f_df = pd.DataFrame([{
                "Qty": final_billing_qty, "Product": final_item_label_name, "Unit Rate": base_h, "Min_Lab": 0, "Raw_Lab": final_billing_qty * f_lab,
                "Lab_Math": lab_desc, "KG": final_billing_qty * f_kg, "Is_Marquee": False,
                "Discount": 0.0, "Lab_Per_Unit": 0, "Base_Hire": base_h, "Anchoring": "", "Override_Rate": 0.0
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_f_df], ignore_index=True)
            st.rerun()

elif selected_cat == "grandstands":
    seats_input = st.number_input("Total Seat Capacity Requirements Count", min_value=1, value=None, placeholder="Type total quantity of seats...", key="gs_qty")
    
    if st.button("Add Grandstand Configuration Layout"):
        if seats_input is None or seats_input <= 0:
            st.error("Please supply a valid seat capacity count first.")
        else:
            per_seat_labour, math_desc_str = calculate_dynamic_grandstand_rate(seats_input)
            base_seat_hire = 15.00 if weeks < 4 else 7.50
            combined_unit_rate = base_seat_hire + per_seat_labour
            
            # FIXED v62.0: Set Raw_Lab and Lab_Per_Unit to 0.0 because labor is completely built into the seat rate
            new_df = pd.DataFrame([{
                "Qty": seats_input, "Product": f"Standard Seating Grandstand ({seats_input} Seats)", "Unit Rate": combined_unit_rate, "Min_Lab": 0,
                "Raw_Lab": 0.0, "Lab_Math": math_desc_str, "KG": seats_input * 25.0, "Is_Marquee": False,
                "Discount": 0.0, "Lab_Per_Unit": 0.0, "Base_Hire": combined_unit_rate, "Anchoring": "", "Override_Rate": 0.0
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
            st.rerun()

# ==============================================================================
# QUOTE SUMMARY ENGINE RENDER DATA LOOPS 
# ==============================================================================
if st.session_state.df is not None and not st.session_state.df.empty:
    st.divider()
    st.subheader("📝 QUOTE SUMMARY")
    
    # CRITICAL BUG FIX v61.5: Enforce index clean slate mapping to completely remove collision exceptions
    st.session_state.df.reset_index(drop=True, inplace=True)
    
    h_col0, h_col1, h_col2, h_col3, h_col4, h_col4b, h_col5 = st.columns([0.4, 3.2, 1.0, 1.2, 1.2, 1.2, 1.4])
    h_col1.markdown("<div class='summary-hdr'>Item Description</div>", unsafe_allow_html=True)
    h_col2.markdown("<div class='summary-hdr'>Qty (Editable)</div>", unsafe_allow_html=True)
    h_col3.markdown("<div class='summary-hdr'>Gross Unit</div>", unsafe_allow_html=True)
    h_col4.markdown("<div class='summary-hdr'>Disc %</div>", unsafe_allow_html=True)
    h_col4b.markdown("<div class='summary-hdr'>Override Rate</div>", unsafe_allow_html=True)
    h_col5.markdown("<div class='summary-hdr' style='text-align: right;'>Subtotal</div>", unsafe_allow_html=True)

    h_tot_c, h_wk1_gear, total_kg = 0.0, 0.0, 0.0
    for idx, row in st.session_state.df.iterrows():
        override = row.get("Override_Rate", 0.0)
        active_base = override if override > 0 else row["Unit Rate"]
        active_hire_base = override if override > 0 else row["Base_Hire"]
        
        qty, brate, dm = row["Qty"], active_base, (1 - (row["Discount"]/100))
        total_kg += row["KG"]
        h_wk1_gear += (qty * active_hire_base)
            
        wk1_t = (qty * brate + row["Raw_Lab"]) * dm if labour_mode == "Include in Hire" else (qty * brate) * dm
        h_tot_c += wk1_t
        
        c0, c1, c2, c3, c4, c4b, c5 = st.columns([0.4, 3.2, 1.0, 1.2, 1.2, 1.2, 1.4])
        if c0.button("🗑️", key=f"sdel_{idx}"):
            st.session_state.df.drop(idx, inplace=True)
            st.session_state.df.reset_index(drop=True, inplace=True)
            st.rerun()
            
        prod_display = str(row['Product'])
        if row.get('Anchoring'): prod_display += f" ({row['Anchoring']})"
        c1.markdown(f"<div class='item-text'>{prod_display}</div>", unsafe_allow_html=True)
        
        new_qty = c2.number_input("QtyBox", min_value=0.0, value=float(qty), key=f"sqty_{idx}", label_visibility="collapsed")
        if new_qty != float(qty):
            st.session_state.df.at[idx, "Qty"] = new_qty
            if row["Is_Marquee"]:
                for w_idx, w_row in st.session_state.df.iterrows():
                    if "Weights" in w_row["Product"]:
                        num_weights_factor = get_item_property(row["Product"], "Total Number of weights ", fallback_val=16.0)
                        st.session_state.df.at[w_idx, "Qty"] = int(num_weights_factor * new_qty)
            st.rerun()
            
        c3.write(f"${row['Unit Rate']:,.2f}")
        new_disc = c4.number_input("Disc %", 0.0, 100.0, float(row["Discount"]), key=f"sd_{idx}", label_visibility="collapsed")
        if new_disc != row["Discount"]: st.session_state.df.at[idx, "Discount"] = new_disc; st.rerun()
            
        new_override = c4b.number_input("Override", 0.0, 5000.0, value=None if float(row.get("Override_Rate", 0.0)) == 0.0 else float(row.get("Override_Rate", 0.0)), placeholder="Override...", key=f"so_{idx}", label_visibility="collapsed")
        if (new_override or 0.0) != row.get("Override_Rate", 0.0): st.session_state.df.at[idx, "Override_Rate"] = new_override or 0.0; st.rerun()
        c5.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700;'>${wk1_t:,.2f}</div>", unsafe_allow_html=True)

    min_trucks = math.ceil(total_kg / 6000) or 1
    saved_trk_count = st.session_state.overrides_dict.get("logistics_truck_allocation_count_scalar", float(min_trucks))
    trks = int(saved_trk_count)

    raw_lab_pool = st.session_state.df["Raw_Lab"].sum()
    auto_cartage_total = trks * st.session_state.km * 4 * 3.50 if cartage_mode == "Charge" else 0
    
    # FIXED v62.0: Damage waiver is now derived directly from h_tot_c (the final progressive true product hire total)
    auto_waiver_total = h_tot_c * 0.07 if waiver_mode == "Charge" else 0

    # ==============================================================================
    # 9. MANUAL OVERRIDES GRID
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
            # FIXED v62.0: Checking strictly for non-zero separate Raw_Lab costs skips grandstands cleanly
            if row.get('Raw_Lab', 0.0) > 0.0:
                p_label = row['Product']
                lbl_key = f"lab_ovr_{p_label}_{idx}"
                auto_val = float(row['Raw_Lab'])
                math_hint_str = row['Lab_Math']
                
                saved_override_val = st.session_state.overrides_dict.get(lbl_key, -1.0)
                
                r_c0, r_c1, r_c2, r_c3 = st.columns([0.4, 3.2, 2.2, 1.4])
                r_c1.markdown(f"<div class='item-text'>Labour: {p_label}</div><div class='sub-math-hint'>{math_hint_str.lower()}</div>", unsafe_allow_html=True)
                
                new_input_val = r_c2.number_input("InputL", min_value=0.0, value=None if saved_override_val < 0 else float(saved_override_val), placeholder=f"book: ${auto_val:,.2f}", key=f"f_l_{idx}", label_visibility="collapsed")
                actual_l_val = new_input_val if new_input_val is not None else auto_val
                r_c3.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700;'>${actual_l_val:,.2f}</div>", unsafe_allow_html=True)
                
                final_labour_pool_sum += actual_l_val
                target_saved_flag = new_input_val if new_input_val is not None else -1.0
                if target_saved_flag != saved_override_val:
                    st.session_state.overrides_dict[lbl_key] = target_saved_flag; has_changes_detected = True

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
    r_t0, r_t1, r_t2, r_t3 = st.columns([0.4, 3.2, 2.2, 1.4])
    r_t1.markdown(f"<div class='item-text'>Logistics: Cartage Freight Fee</div><div class='sub-math-hint'>default: {trks} trucks x {st.session_state.km}km x 4 x $3.50</div>", unsafe_allow_html=True)
    new_cart_val = r_t2.number_input("InputC", min_value=0.0, value=None if saved_cart_override < 0 else float(saved_cart_override), placeholder=f"book: ${auto_cartage_total:,.2f}", key="f_c_global", label_visibility="collapsed")
    final_cartage_sum = new_cart_val if new_cart_val is not None else auto_cartage_total
    r_t3.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700;'>${final_cartage_sum:,.2f}</div>", unsafe_allow_html=True)
    target_cart_flag = new_cart_val if new_cart_val is not None else -1.0
    if target_cart_flag != saved_cart_override: st.session_state.overrides_dict[cart_key] = target_cart_flag; has_changes_detected = True

    waiv_key = "damage_waiver_insurance_global"
    saved_waiv_override = st.session_state.overrides_dict.get(waiv_key, -1.0)
    r_w0, r_w1, r_w2, r_w3 = st.columns([0.4, 3.2, 2.2, 1.4])
    r_w1.markdown(f"<div class='item-text'>Waiver: Equipment Damage Indemnity</div><div class='sub-math-hint'>default: ${h_tot_c:,.2f} total product hire value x 7%</div>", unsafe_allow_html=True)
    new_waiv_val = r_w2.number_input("InputW", min_value=0.0, value=None if saved_waiv_override < 0 else float(saved_waiv_override), placeholder=f"book: ${auto_waiver_total:,.2f}", key="f_w_global", label_visibility="collapsed")
    final_waiver_sum = new_waiv_val if new_waiv_val is not None else auto_waiver_total
    r_w3.markdown(f"<div style='text-align: right; font-size: 20px; font-weight: 700;'>${final_waiver_sum:,.2f}</div>", unsafe_allow_html=True)
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
    
    # Document compilation lines text mapping for black header PDF logs
    structural_math_dict = {"LABOUR": [], "LOGISTICS": [], "DAMAGE WAIVER": []}
    for idx, row in st.session_state.df.iterrows():
        if row.get('Raw_Lab', 0.0) > 0.0:
            lbl_key = f"lab_ovr_{row['Product']}_{idx}"
            saved_val = st.session_state.overrides_dict.get(lbl_key, -1.0)
            l_val = saved_val if saved_val >= 0 else float(row['Raw_Lab'])
            structural_math_dict["LABOUR"].append(f"{row['Product']} = ${l_val:,.2f}")
    if final_labour_pool_sum == 350.00 and raw_lab_pool < 350.00:
        structural_math_dict["LABOUR"].append("Minimum Floor Buffer Adjustment top-up applied")
    structural_math_dict["LABOUR"].append(f"Total Applied = ${final_labour_pool_sum:,.2f}")
    structural_math_dict["LOGISTICS"].append(f"{trks} Trucks x {st.session_state.km}km x 4 x $3.50 = ${final_cartage_sum:,.2f}")
    
    # FIXED v62.0: Audit text output logs updated to capture total product hire base explicitly
    structural_math_dict["DAMAGE WAIVER"].append(f"${h_tot_c:,.2f} total product hire cost x 7% = ${final_waiver_sum:,.2f}")

# ==============================================================================
# 10. DOWNLOAD ZONE (FULLY POSITIONALLY ALIGNED v62.0)
# ==============================================================================
    st.markdown("")  
    action_col_1, action_col_2 = st.columns(2)
            
    # FIXED v62.0: Positional variables completely matched to eliminate freevar runtime mismatch crashes
    cleaned_pdf_items = st.session_state.df.to_dict('records')
    pdf_b = create_calculation_pdf(h_tot_c, final_labour_pool_sum, final_waiver_sum, final_cartage_sum, grand_total_calc, weeks, cleaned_pdf_items, structural_math_dict, st.session_state.status)
    action_col_1.download_button("📥 DOWNLOAD DETAILED AUDIT PDF", pdf_b, file_name="Louis_Analysis.pdf", mime="application/pdf", use_container_width=True)

    excel_df = struct_db.copy() if struct_db is not None else pd.DataFrame([{"System Status": "Catalog Empty"}])
    try:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            excel_df.to_excel(writer, index=False, sheet_name='Database_Backup')
        excel_data_bytes, ext, mt = excel_buffer.getvalue(), "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except:
        excel_data_bytes, ext, mt = excel_df.to_csv(index=False).encode('utf-8'), "csv", "text/csv"

    action_col_2.download_button(label="📊 DOWNLOAD ACTIVE DATA BACKUP", data=excel_data_bytes, file_name=f"Louis_Current_Database_Template.{ext}", mime=mt, use_container_width=True)
