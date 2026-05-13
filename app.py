import streamlit as st
import math
import pandas as pd
from datetime import date
from fpdf import FPDF
import re

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
            else: st.error("❌ Incorrect Code")
        return False
    return True

if not check_password():
    st.stop()

# --- RE-ALIGNED MASTER CATALOG (v29.6) ---

STRUCT_LOGIC = {
    3:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    4:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    6:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    9:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    10: {"bay": 5, "s_rate": 23.00, "m_rate": 16.55, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    12: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 1500.00},
    15: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 1500.00},
    20: {"bay": 5, "s_rate": 19.95, "m_rate": 19.95, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 0.00},
}

MARQUEE_UNITS = {
    "3x3 Hi Top": {"rate": 198.45, "lab_perc": 0.55, "min_lab": 350.00, "legs": 4, "kg": 50},
    "3x3 Shade": {"rate": 198.45, "lab_perc": 0.55, "min_lab": 350.00, "legs": 4, "kg": 50},
    "3x6 Shade": {"rate": 396.90, "lab_perc": 0.55, "min_lab": 350.00, "legs": 6, "kg": 80},
    "4.5x4.5": {"rate": 446.51, "lab_perc": 0.55, "min_lab": 350.00, "legs": 4, "kg": 75}
}

GENERAL_PRODUCTS = {
    "Flooring": {
        "Supa-Trac®": {"rate": 11.55, "lab_perc": 0.40, "kg_sqm": 4.5, "unit": "SQM"},
        "I-Trac®": {"rate": 23.40, "lab_perc": 0.40, "kg_sqm": 15.0, "unit": "SQM"},
        "Plastorip": {"rate": 14.00, "lab_perc": 0.40, "kg_sqm": 4.0, "unit": "SQM"},
        "Dance Floor": {"rate": 200.00, "lab_perc": 0.40, "kg": 150.0, "unit": "ea"}
    },
    "Furniture": {
        "Stacking Chair": {"rate": 2.50, "lab_perc": 0.25, "kg": 5, "unit": "ea"},
        "Trestle Table": {"rate": 13.00, "lab_perc": 0.25, "kg": 15, "unit": "ea"}
    }
}

# --- PDF ENGINE ---
def create_calculation_pdf(name, df, subtotal, final_labour, waiver, cartage, grand_total, km, weeks, lab_details, total_kg, trucks):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "No Fuss Event Hire - Internal Calculation Sheet", ln=True, align="C")
    pdf.set_font("Arial", "", 10); pdf.cell(0, 10, f"Generated on: {date.today()}", ln=True, align="C"); pdf.ln(5)
    pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, f"Quote: {name}", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Duration: {weeks} Week(s) | Payload: {total_kg:,.0f} kg", ln=True)
    pdf.cell(0, 8, f"Logistics: {trucks} x 6,000kg Truck(s)", ln=True); pdf.ln(5)

    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 10, " Product", 1, 0, "L", True); pdf.cell(25, 10, " Qty", 1, 0, "C", True)
    pdf.cell(35, 10, " Rate", 1, 0, "C", True); pdf.cell(40, 10, " Total", 1, 1, "R", True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    for _, row in df.iterrows():
        pdf.cell(80, 8, f" {row['Product']}", 1)
        pdf.cell(25, 8, f" {row['Qty']} {row['Unit_Type']}", 1, 0, "C")
        pdf.cell(35, 8, f" ${row['Unit Rate']:,.2f}", 1, 0, "C")
        pdf.cell(40, 8, f" ${row['Total']:,.2f}", 1, 1, "R")
    
    pdf.ln(10); pdf.set_font("Arial", "B", 13); pdf.cell(0, 10, "Financial Breakdown", ln=True)
    pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"BASE HIRE SUBTOTAL: ${subtotal:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        if not row['Is_Lab_Line']: pdf.cell(0, 6, row['Hire_Math_Str'], ln=True)

    pdf.ln(4); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Labour Total: ${final_labour:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10)
    for line in lab_details: pdf.cell(0, 6, line, ln=True)

    pdf.ln(4); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Damage Waiver (7%): ${waiver:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(0, 6, f"${subtotal:,.2f} x 0.07", ln=True)

    pdf.ln(4); pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Cartage Total: ${cartage:,.2f}", ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(0, 6, f"{trucks} Trucks x {km} km x 4 trips x $3.50/km", ln=True)
    
    pdf.ln(10); pdf.set_font("Arial", "B", 14); pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, f"GRAND TOTAL (EX GST): ${grand_total:,.2f}", 1, 1, "R", True)
    return bytes(pdf.output())

# --- APP UI ---
st.set_page_config(page_title="No Fuss Quote Pro v29.6", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Unit_Type", "Product_Meta", "Min_Lab_Floor", "Raw_Lab_Value", "Lab_Math_Str", "Weight_KG", "Is_Lab_Line", "Hire_Math_Str"])

st.title("📦 No Fuss Quote Pro")

c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today())
end_date = c2.date_input("Hire End", value=date.today())
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=0.0)
live_weeks = math.ceil(((end_date - start_date).days) / 7) if (end_date - start_date).days > 0 else 1

# --- SECTION 1: MARQUEES ---
st.markdown("### ⚡ MARQUEE QUICK-ADD")
mq_in, mq_q, mq_s = st.columns([3, 1, 1])
q_input = mq_in.text_input("Size (Span x Length)", placeholder="4x12...")
q_qty = mq_q.number_input("Unit Qty", min_value=1, value=1)
q_sec = mq_s.radio("Securing", ["Weights", "Pegging"], horizontal=True)

if st.button("ADD MARQUEE"):
    nums = re.findall(r'\d+', q_input)
    if len(nums) >= 2:
        span, length = int(nums[0]), int(nums[1])
        new_rows = []
        if span == 3 and length == 3:
            data = MARQUEE_UNITS["3x3 Hi Top"]
            h_val = data['rate'] * q_qty; lab_val = h_val * data['lab_perc']
            new_rows.append({"Qty": q_qty, "Product": "3m x 3m Hi Top", "Unit Rate": data['rate'], "Total": 0.0, "Unit_Type": "ea", "Product_Meta": "9sqm", "Min_Lab_Floor": data['min_lab'], "Raw_Lab_Value": lab_val, "Lab_Math_Str": f"3m x 3m Hi Top: ${h_val:,.2f} x 55% = ${lab_val:,.2f}", "Weight_KG": data['kg'] * q_qty, "Is_Lab_Line": False, "Hire_Math_Str": f"{q_qty} - 3m x 3m Hi Top x ${data['rate']:,.2f} = ${h_val:,.2f}"})
            legs = data['legs']
        else:
            logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
            bays = math.ceil(length / logic['bay']); sqm = span * length
            rate = logic['s_rate'] if bays == 1 else logic['m_rate']
            lab_perc = logic['s_lab'] if bays == 1 else logic['m_lab']
            h_val = sqm * rate * q_qty; lab_val = h_val * lab_perc
            new_rows.append({"Qty": q_qty, "Product": f"Structure {span}m x {length}m", "Unit Rate": sqm * rate, "Total": 0.0, "Unit_Type": "ea", "Product_Meta": f"{sqm}sqm", "Min_Lab_Floor": logic['min_lab'], "Raw_Lab_Value": lab_val, "Lab_Math_Str": f"Structure {span}x{length}: ${h_val:,.2f} x {int(lab_perc*100)}% = ${lab_val:,.2f}", "Weight_KG": (sqm * 2.5) * q_qty, "Is_Lab_Line": False, "Hire_Math_Str": f"{q_qty} - Structure {span}m x {length}m ({sqm}sqm x ${rate:,.2f}) = ${h_val:,.2f}"})
            legs = ((length / logic['bay']) + 1) * 2

        if q_sec == "Weights":
            w_total = int(legs * 6 * q_qty)
            w_h_total = w_total * 6.60; lab_w = w_h_total * 0.25 
            new_rows.append({"Qty": w_total, "Product": "30kg Orange Weights", "Unit Rate": 6.60, "Total": 0.0, "Unit_Type": "ea", "Product_Meta": f"{int(legs)} legs", "Min_Lab_Floor": 0, "Raw_Lab_Value": lab_w, "Lab_Math_Str": f"Weights: ${w_h_total:,.2f} x 25% = ${lab_w:,.2f}", "Weight_KG": w_total * 30, "Is_Lab_Line": False, "Hire_Math_Str": f"{w_total} - 30kg Orange Weights x $6.60 = ${w_h_total:,.2f}"})
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True); st.rerun()

# --- SECTION 2: CATALOG ---
st.markdown("### 🪵 GENERAL CATALOG")
c_sel, p_sel, q_sel = st.columns([2, 2, 1])
category = c_sel.selectbox("Category", list(GENERAL_PRODUCTS.keys()))
product_name = p_sel.selectbox("Product", list(GENERAL_PRODUCTS[category].keys()))
qty_val = q_sel.number_input("Qty / SQM", min_value=0.0, step=1.0)

if st.button("ADD TO QUOTE"):
    data = GENERAL_PRODUCTS[category][product_name]
    h_total = qty_val * data['rate']
    lab_total = h_total * data['lab_perc']
    kg_total = (qty_val * data['kg_sqm']) if 'kg_sqm' in data else (qty_val * data.get('kg', 0))
    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
        "Qty": qty_val, "Product": product_name, "Unit Rate": data['rate'], "Total": 0.0, "Unit_Type": data['unit'], 
        "Product_Meta": "", "Min_Lab_Floor": 0, "Raw_Lab_Value": lab_total, 
        "Lab_Math_Str": f"{product_name}: ${h_total:,.2f} x {int(data['lab_perc']*100)}% = ${lab_total:,.2f}", 
        "Weight_KG": kg_total, "Is_Lab_Line": False, "Hire_Math_Str": f"{qty_val} - {product_name} x ${data['rate']:,.2f} = ${h_total:,.2f}"
    }])], ignore_index=True); st.rerun()

# --- FINANCES ---
if not st.session_state.df.empty:
    st.markdown("### 🏗️ CURRENT QUOTE")
    st.data_editor(st.session_state.df[["Qty", "Unit_Type", "Product", "Unit Rate", "Total"]], use_container_width=True)
    
    h_tot, raw_lab_sum, max_min_lab, total_weight = 0.0, 0.0, 0.0, 0.0
    lab_math_lines = []
    for idx, row in st.session_state.df.iterrows():
        is_structure = "Structure" in row["Product"] or "Marquee" in row["Product"]
        line_hire = row["Qty"] * row["Unit Rate"] * (live_weeks if is_structure else 1)
        h_tot += line_hire; raw_lab_sum += row["Raw_Lab_Value"]; max_min_lab = max(max_min_lab, row["Min_Lab_Floor"])
        total_weight += row["Weight_KG"]; st.session_state.df.at[idx, "Total"] = line_hire
        if row["Lab_Math_Str"]: lab_math_lines.append(row["Lab_Math_Str"])

    truck_count = math.ceil(total_weight / 6000) if total_weight > 0 else 1
    final_lab_charge = max(max_min_lab, raw_lab_sum)
    w_tot, c_val = h_tot * 0.07, truck_count * km_input * 4 * 3.50; grand = h_tot + final_lab_charge + w_tot + c_val

    st.divider(); m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE", f"${h_tot:,.2f}"); m2.metric("LABOUR", f"${final_lab_charge:,.2f}"); m3.metric("WAIVER", f"${w_tot:,.2f}"); m4.metric("CARTAGE", f"${c_val:,.2f}")
    
    fn = st.text_input("Project Name:")
    pdf_bytes = create_calculation_pdf(fn, st.session_state.df, h_tot, final_lab_charge, w_tot, c_val, grand, km_input, live_weeks, lab_math_lines, total_weight, truck_count)
    st.download_button("📥 DOWNLOAD PDF", pdf_bytes, file_name=f"{fn}_Calculations.pdf")
    if st.button("⚠️ RESET"): st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.rerun()
