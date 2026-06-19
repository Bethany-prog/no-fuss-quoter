import streamlit as st
import math
import pandas as pd
from datetime import date, datetime, timedelta
from fpdf import FPDF
import re
import json
import io

# ==============================================================================
# 0. NATIVE INTEGRATED MASTER DATA ARCHIVE (ZERO EXTERNAL FILE DEPENDENCY)
# ==============================================================================
st.set_page_config(page_title="Louis Master Quoter", layout="wide")

DEPOT_LAT = -38.1171
DEPOT_LON = 145.2442

# Embedded structures data dictionary framework
NATIVE_STRUCTURES = [
    {"Configuration": "3m x 3m Hi Tops", "Type": "Marquee", "Hire Unit Rate": 198.45, "Labour Total": 350.0, "Total Weight (kg)": 480.0, "Total Number of weights": 16.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "3m x 3m Shade Canopy", "Type": "Marquee", "Hire Unit Rate": 198.45, "Labour Total": 350.0, "Total Weight (kg)": 480.0, "Total Number of weights": 16.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "3m x 6m Shade Canopy", "Type": "Marquee", "Hire Unit Rate": 396.90, "Labour Total": 350.0, "Total Weight (kg)": 720.0, "Total Number of weights": 24.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "4m x 3m", "Type": "Marquee", "Hire Unit Rate": 264.60, "Labour Total": 350.0, "Total Weight (kg)": 480.0, "Total Number of weights": 16.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 3m", "Type": "Marquee", "Hire Unit Rate": 396.90, "Labour Total": 350.0, "Total Weight (kg)": 480.0, "Total Number of weights": 16.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 6m", "Type": "Marquee", "Hire Unit Rate": 793.80, "Labour Total": 450.0, "Total Weight (kg)": 840.0, "Total Number of weights": 24.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "6m x 9m", "Type": "Marquee", "Hire Unit Rate": 1190.70, "Labour Total": 550.0, "Total Weight (kg)": 1120.0, "Total Number of weights": 32.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "10m x 10m", "Type": "Structure", "Hire Unit Rate": 1820.00, "Labour Total": 728.0, "Total Weight (kg)": 3375.0, "Total Number of weights": 32.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "10m x 15m", "Type": "Structure", "Hire Unit Rate": 2730.00, "Labour Total": 1092.0, "Total Weight (kg)": 5062.5, "Total Number of weights": 40.0, "Weight Size (KG)": 30.0, "Cost per weight": 6.60, "Labour Per Weight": 1.65},
    {"Configuration": "15m x 15m", "Type": "Structure", "Hire Unit Rate": 3476.25, "Labour Total": 1390.5, "Total Weight (kg)": 9600.0, "Total Number of weights": 8.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05},
    {"Configuration": "15m x 20m", "Type": "Structure", "Hire Unit Rate": 4635.00, "Labour Total": 1854.0, "Total Weight (kg)": 12000.0, "Total Number of weights": 10.0, "Weight Size (KG)": 1200.0, "Cost per weight": 88.20, "Labour Per Weight": 22.05}
]

NATIVE_GRANDSTANDS = [
    {"Low": 0, "High": 40, "Total": 880.0},
    {"Low": 41, "High": 100, "Total": 1650.0},
    {"Low": 101, "High": 149, "Total": 2420.0},
    {"Low": 150, "High": 199, "Total": 3300.0},
    {"Low": 200, "High": 249, "Total": 3850.0},
    {"Low": 250, "High": 299, "Total": 5280.0},
    {"Low": 300, "High": 349, "Total": 5940.0},
    {"Low": 350, "High": 400, "Total": 6600.0}
]

NATIVE_FLOORING = [
    {"Product Name": "I-Trac", "1-Week Rate": 23.40, "4-Week Block": 46.80, "Labour": 4.65, "Weight": 15.0},
    {"Product Name": "Supa-Trac", "1-Week Rate": 11.55, "4-Week Block": 25.00, "Labour": 4.65, "Weight": 4.5},
    {"Product Name": "Plastorip", "1-Week Rate": 10.15, "4-Week Block": 20.30, "Labour": 3.05, "Weight": 4.0},
    {"Product Name": "Trakmats", "1-Week Rate": 23.20, "4-Week Block": 45.00, "Labour": 5.85, "Weight": 35.0}
]

# Convert internal dictionaries directly to clean tracking pandas DataFrames
struct_db = pd.DataFrame(NATIVE_STRUCTURES)
grandstand_db = pd.DataFrame(NATIVE_GRANDSTANDS)
flooring_db = pd.DataFrame(NATIVE_FLOORING)

# ==============================================================================
# SMART FUZZY DIMENSION MATCHING ENGINE
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

def get_item_property(config_name, column_target, fallback_val=0.0):
    matched_row = struct_db[struct_db["Configuration"] == str(config_name).strip()]
    if not matched_row.empty:
        val = matched_row.iloc[0].get(column_target, fallback_val)
        return float(val) if not pd.isna(val) else fallback_val
    return fallback_val

def calculate_dynamic_grandstand_rate(seats_input):
    if seats_input <= 0:
        return 0.0, "0 seats allocation"
    for idx, row in grandstand_db.iterrows():
        if int(row["Low"]) <= seats_input <= int(row["High"]):
            total_labour_cost = float(row["Total"])
            return round(total_labour_cost / seats_input, 2), f"Seating Matrix Flat Booking: ${total_labour_cost:,.2f} / {seats_input} seats"
    return 19.19, f"Standard base per-seat fallback calculation applied"

# ==============================================================================
# 3. PDF AUDIT ENGINE
# ==============================================================================
def clean_text(txt):
    if not txt: return ""
    replacements = {"®": "(R)", "™": "(TM)", "©": "(C)", "└": "->", "—": "-", "–": "-"}
    cleaned = str(txt)
    for char, rep in replacements.items():
        cleaned = cleaned.replace(char, rep)
    return cleaned.encode('latin-1', 'replace').decode('latin-1')

def create_calculation_pdf(subtotal, labour, waiver, cartage, grand, weeks, item_items_list, structural_math_dict, job_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text(f"Louis Quoting Tool - Calculation Audit Summary"), ln=True, align="C")
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, clean_text(f"JOB TARGET NAME: {job_name.upper()} | DURATION: {weeks} Week(s)"), ln=True, align="C")
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
    for cat in ["LABOUR", "LOGISTICS", "DAMAGE WAIVER"]:
        if cat in structural_math_dict and structural_math_dict[cat]:
            pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 9, f" {cat}", 0, 1, "L", True)
            pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 10)
            for line in structural_math_dict[cat]:
                pdf.cell(0, 7, clean_text(f" {line}"), border="B", ln=True)
            pdf.ln(3)

    pdf.ln(5); pdf.set_fill_color(0, 230, 118); pdf.set_text_color(26, 29, 45); pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 14, f" GRAND TOTAL (EX GST): ${grand:,.2f} ", 0, 1, "R", True)
    
    return bytes(pdf.output(dest='S')) if isinstance(pdf.output(dest='S'), bytes) else pdf.output(dest='S').encode('latin-1', 'replace')

# ==============================================================================
# 5. STREAMLIT INTERNAL STORAGE PERSISTENCE
# ==============================================================================
if 'df' not in st.session_state: 
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount", "Lab_Math", "Lab_Per_Unit", "Base_Hire", "Anchoring", "Override_Rate", "Is_Flooring", "Base_1Wk_Rate", "Base_Block_Rate"])
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
# UPGRADE v65.0: JOB LABEL FIELD HEADER (REPLACED STAGE SELECTOR DROPDOWN)
# ==============================================================================
job_name_input = st.text_input("📝 Active Project / Job Name", value="New Project Estimate", placeholder="Type client reference or project code here...")

c_dt1, c_km_sep = st.columns([1, 1])
start_d = c_dt1.date_input("Start Date", value=st.session_state.start_date_val, key=f"sd_base_{st.session_state.reset_key_seed}")
st.session_state.start_date_val = start_d
end_d = c_km_sep.date_input("End Date", value=start_d, key=f"ed_base_{st.session_state.reset_key_seed}")
weeks = math.ceil(((end_d - start_d).days) / 7) or 1

# Transport Routing Modules
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
c_km2.info(f"Routing evaluations active at **{st.session_state.km} One-Way KM** from depot. Duration: {weeks} Week(s).")

l1, l2, l3 = st.columns(3)
cartage_mode = l1.segmented_control("Cartage Math", ["Charge", "Free"], default=st.session_state.saved_cartage_mode)
labour_mode = l2.segmented_control("Labour Math", ["Separate", "Include in Hire", "Free"], default=st.session_state.saved_labour_mode)
waiver_mode = l3.segmented_control("Damage Waiver", ["Charge", "Free"], default=st.session_state.saved_waiver_mode)

# ==============================================================================
# 7. MAIN INTERACTION COMPONENT CORE ENTRY HUB
# ==============================================================================
st.divider()
st.markdown("### ➕ CATALOG COMPONENT HUB")

selected_cat = st.selectbox("Choose Category to Load", ["marquees", "flooring", "grandstands"])

if selected_cat == "marquees":
    search_query = st.text_input("🔍 Smart Search Marquee Size (e.g. 4x3, 6x3, 15x15):", placeholder="Type dimensions...", key="marq_search_box")
    filtered_df = struct_db.copy()
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
                b_hire = get_item_property(target_item, "Hire Unit Rate")
                raw_labour_pool = get_item_property(target_item, "Labour Total")
                total_w = get_item_property(target_item, "Total Weight (kg)")
                
                new_df = pd.DataFrame([{
                    "Qty": qty_input, "Product": target_item, "Unit Rate": b_hire, "Min_Lab": 350,
                    "Raw_Lab": raw_labour_pool * qty_input, "Lab_Math": f"{target_item}: Setup labor applied",
                    "KG": total_w * qty_input, "Is_Marquee": True, "Discount": 0.0, "Lab_Per_Unit": raw_labour_pool,
                    "Base_Hire": b_hire, "Anchoring": anch_type, "Override_Rate": 0.0, "Is_Flooring": False,
                    "Base_1Wk_Rate": b_hire, "Base_Block_Rate": b_hire
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
                
                if anch_type == "Weighted":
                    num_weights = get_item_property(target_item, "Total Number of weights ")
                    w_size = get_item_property(target_item, "Weight Size (KG) ")
                    w_cost = get_item_property(target_item, "Cost per weight ")
                    w_lab = get_item_property(target_item, "Labour Per Weight ")
                    
                    calc_w = int(num_weights * qty_input)
                    weight_df = pd.DataFrame([{
                        "Qty": calc_w, "Product": f"{int(w_size)}kg Weights", "Unit Rate": w_cost, "Min_Lab": 0,
                        "Raw_Lab": calc_w * w_lab, "Lab_Math": f"Ballast weights stacking: {calc_w} units x ${w_lab:.2f}",
                        "KG": calc_w * w_size, "Is_Marquee": False, "Discount": 0.0, "Lab_Per_Unit": w_lab,
                        "Base_Hire": w_cost, "Anchoring": "", "Override_Rate": 0.0, "Is_Flooring": False,
                        "Base_1Wk_Rate": w_cost, "Base_Block_Rate": w_cost
                    }])
                    st.session_state.df = pd.concat([st.session_state.df, weight_df], ignore_index=True)
                st.rerun()

elif selected_cat == "flooring":
    floor_options = flooring_db["Product Name"].tolist()
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
            st.error("Please input metrics first.")
        else:
            match_f = flooring_db[flooring_db["Product Name"] == target_item]
            f_rate = float(match_f.iloc[0]["1-Week Rate"])
            f_block = float(match_f.iloc[0]["4-Week Block"])
            f_lab = float(match_f.iloc[0]["Labour"])
            f_kg = float(match_f.iloc[0]["Weight"])
            
            final_item_label_name = target_item
            final_billing_qty = cov_input
            
            if "supa" in target_item.lower():
                num_sheets_needed = math.ceil(cov_input / 3.0)
                final_billing_qty = num_sheets_needed * 3.0  
                final_item_label_name = f"{target_item} [{num_sheets_needed:,.0f} Sheets of 3 SQM]"
                lab_desc = f"Supa-Trac Sheet Matrix: {num_sheets_needed:,.0f} Sheets ({final_billing_qty:,.0f} SQM total) x ${f_lab:.2f}"
            else:
                lab_desc = f"{target_item}: {cov_input:,.0f} SQM area x ${f_lab:.2f}"
                
            new_f_df = pd.DataFrame([{
                "Qty": final_billing_qty, "Product": final_item_label_name, "Unit Rate": f_rate, "Min_Lab": 0, "Raw_Lab": final_billing_qty * f_lab,
                "Lab_Math": lab_desc, "KG": final_billing_qty * f_kg, "Is_Marquee": False,
                "Discount": 0.0, "Lab_Per_Unit": 0, "Base_Hire": f_rate, "Anchoring": "", "Override_Rate": 0.0, "Is_Flooring": True,
                "Base_1Wk_Rate": f_rate, "Base_Block_Rate": f_block
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_f_df], ignore_index=True)
            st.rerun()

elif selected_cat == "grandstands":
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
                "Base_1Wk_Rate": per_seat_rate, "Base_Block_Rate": per_seat_rate
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
            st.rerun()

# ==============================================================================
# QUOTE SUMMARY GRID ENGINE 
# ==============================================================================
if st.session_state.df is not None and not st.session_state.df.empty:
    st.divider()
    st.subheader("📝 QUOTE SUMMARY")
    
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
        qty, dm = row["Qty"], (1 - (row["Discount"]/100))
        total_kg += row["KG"]
        
        # Long term duration calculations matrix engine
        if override > 0:
            active_base_rate = override
            wk1_t = (qty * override) * dm
        elif row.get("Is_Flooring") and weeks >= 4 and row.get("Base_Block_Rate", 0) > 0:
            block_multiplier = weeks / 4.0
            active_base_rate = row["Base_Block_Rate"]
            wk1_t = (qty * row["Base_Block_Rate"] * block_multiplier) * dm
        else:
            active_base_rate = row["Unit Rate"]
            if row["Is_Marquee"] and weeks > 1:
                wk1_t = (qty * row["Unit Rate"] + (qty * (row["Unit Rate"] * 0.5) * (weeks - 1))) * dm
            else:
                wk1_t = (qty * row["Unit Rate"] * weeks) * dm

        h_wk1_gear += (qty * active_base_rate)
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
                        num_weights_factor = get_item_property(row["Product"], "Total Number of weights ")
                        st.session_state.df.at[w_idx, "Qty"] = int(num_weights_factor * new_qty)
            st.rerun()
            
        c3.write(f"${active_base_rate:,.2f}")
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

    # Metrics Display Dashboard Cards
    st.divider(); m = st.columns(6)
    m[0].metric("HIRE COST", f"${round(h_tot_c, 2):,}")
    m[1].metric("LABOUR", f"${round(final_labour_pool_sum, 2):,}")
    m[2].metric("WAIVER", f"${round(final_waiver_sum, 2):,}")
    m[3].metric("CARTAGE", f"${round(final_cartage_sum, 2):,}")
    m[4].metric("WEIGHT", f"{round(total_kg, 0):}kg")
    m[5].metric("TRUCKS", f"{trks}")
    
    grand_total_calc = h_tot_c + final_labour_pool_sum + final_waiver_sum + final_cartage_sum
    st.markdown(f"<div class='gt-banner'>GRAND TOTAL (EX GST): ${grand_total_calc:,.2f}</div>", unsafe_allow_html=True)
    
    # Audit log strings lines map references
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
    structural_math_dict["DAMAGE WAIVER"].append(f"${h_tot_c:,.2f} total product hire cost x 7% = ${final_waiver_sum:,.2f}")

# ==============================================================================
# 10. DOWNLOAD ENGINE PIOK ZONE (UPGRADED JOB REF LINKAGE)
# ==============================================================================
    st.markdown("")  
    action_col_1, action_col_2 = st.columns(2)
            
    cleaned_pdf_items = st.session_state.df.to_dict('records')
    # UPGRADE v65.0: Job name input maps securely to the native audit PDF stream target
    pdf_b = create_calculation_pdf(h_tot_c, final_labour_pool_sum, final_waiver_sum, final_cartage_sum, grand_total_calc, weeks, cleaned_pdf_items, structural_math_dict, job_name_input)
    action_col_1.download_button("📥 DOWNLOAD DETAILED AUDIT PDF", pdf_b, file_name=f"{job_name_input.replace(' ', '_')}_Analysis.pdf", mime="application/pdf", use_container_width=True)

    excel_df = struct_db.copy()
    try:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            excel_df.to_excel(writer, index=False, sheet_name='Database_Backup')
        excel_data_bytes, ext, mt = excel_buffer.getvalue(), "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except:
        excel_data_bytes, ext, mt = excel_df.to_csv(index=False).encode('utf-8'), "csv", "text/csv"

    action_col_2.download_button(label="📊 DOWNLOAD ACTIVE DATA BACKUP", data=excel_data_bytes, file_name="Louis_Current_Database_Template.xlsx", mime=mt, use_container_width=True)
