import streamlit as st
import math
import pandas as pd
from datetime import date
from fpdf import FPDF
import re
import json
import os

# --- v32.1 CONFIG & DIRECTORIES ---
if not os.path.exists("quotes"):
    os.makedirs("quotes")

# 1. ACCESS CONTROL
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        st.title("🔒 Unified Engine Access")
        password = st.text_input("Access Code", type="password")
        if st.button("Unlock Engine"):
            if password == "NoFuss2026":
                st.session_state.password_correct = True
                st.rerun()
        return False
    return True

if not check_password():
    st.stop()

# --- LOCKED MASTER DATA ---
CONFIG = {
    "WEIGHT_UNIT_KG": 30,
    "WEIGHT_HIRE": 6.60,
    "WEIGHT_LABOUR": 1.65, # Fixed 25% of hire
    "TRUCK_PAYLOAD": 6000,
    "CARTAGE_RATE": 3.50
}

STRUCT_LOGIC = {
    4:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    6:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    9:  {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    10: {"bay": 5, "s_rate": 23.00, "m_rate": 16.55, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 350.00},
    12: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 1500.00},
    15: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.55, "m_lab": 0.40, "min_lab": 1500.00},
    20: {"bay": 5, "s_rate": 19.95, "m_rate": 19.95, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 0.00},
}

MARQUEE_UNITS = {
    "3m x 3m Hi Top": {"rate": 198.45, "lab": 0.55, "min": 350.0, "legs": 4, "kg": 50},
    "3m x 3m Shade": {"rate": 198.45, "lab": 0.55, "min": 350.0, "legs": 4, "kg": 50},
    "3m x 6m Shade": {"rate": 396.90, "lab": 0.55, "min": 350.0, "legs": 6, "kg": 80}
}

# --- PDF ENGINE ---
def create_calculation_pdf(name, df, subtotal, labour, waiver, cartage, grand, km, weeks, start, end, h_maths, l_details, kg, trucks, status):
    pdf = FPDF()
    pdf.add_page()
    title = "TAX INVOICE" if status == "Invoiced" else "QUOTE CALCULATION SHEET"
    pdf.set_font("Arial", "B", 15); pdf.cell(0, 10, f"No Fuss Event Hire - {title}", ln=True, align="C")
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 7, f"HIRE PERIOD: {start} to {end} ({weeks} Week(s))", ln=True, align="C")
    pdf.set_font("Arial", "I", 9); pdf.cell(0, 7, f"Status: {status} | Payload: {kg:,.0f}kg | Logistics: {trucks} Trucks", ln=True, align="C"); pdf.ln(5)

    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255)
    pdf.cell(85, 10, " Product Description", 1, 0, "L", True); pdf.cell(20, 10, " Qty", 1, 0, "C", True)
    pdf.cell(35, 10, " Rate", 1, 0, "C", True); pdf.cell(45, 10, " Total", 1, 1, "R", True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    for _, row in df.iterrows():
        pdf.cell(85, 8, f" {row['Product']}", 1); pdf.cell(20, 8, f" {row['Qty']}", 1, 0, "C")
        pdf.cell(35, 8, f" ${row['Unit Rate']:,.2f}", 1, 0, "C"); pdf.cell(45, 8, f" ${row['Total']:,.2f}", 1, 1, "R")
    
    if status == "Dispatched":
        pdf.ln(10); pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "LOAD LIST (DISPATCH)", ln=True)
        for _, row in df.iterrows():
            pdf.cell(0, 7, f"[ ] {row['Qty']:,.0f} x {row['Product']} ({row['KG']:,.0f}kg)", ln=True)

    pdf.ln(5); pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, f"Hire Subtotal: ${subtotal:,.2f}", ln=True)
    pdf.cell(0, 7, f"Labour Total: ${labour:,.2f}", ln=True)
    pdf.cell(0, 7, f"Grand Total (EX GST): ${grand:,.2f}", ln=True)
    return bytes(pdf.output())

# --- APP UI ---
st.set_page_config(page_title="No Fuss Quote Pro v32.1", layout="wide")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Is_Marquee", "Hire_Math_Str"])

# --- SIDEBAR: QUOTE STORAGE ---
st.sidebar.title("📁 Quote Manager")
proj_name = st.sidebar.text_input("Project Label", "New Quote")
wf_status = st.sidebar.selectbox("Workflow Step", ["Draft", "Invoiced", "Dispatched", "Returned"])

if st.sidebar.button("💾 SAVE QUOTE"):
    data = {"status": wf_status, "items": st.session_state.df.to_dict(orient='records'), "proj": proj_name}
    with open(f"quotes/{proj_name}.json", "w") as f:
        json.dump(data, f)
    st.sidebar.success("Saved!")

saved_quotes = [f.replace(".json", "") for f in os.listdir("quotes") if f.endswith(".json")]
load_choice = st.sidebar.selectbox("Retreive Quote", ["None"] + saved_quotes)
if st.sidebar.button("📂 LOAD") and load_choice != "None":
    with open(f"quotes/{load_choice}.json", "r") as f:
        loaded = json.load(f)
        st.session_state.df = pd.DataFrame(loaded["items"])
        st.rerun()

# --- CALCULATOR INPUTS ---
st.title(f"📦 Unified Engine: {proj_name}")

c1, c2, c3 = st.columns(3)
start_d = c1.date_input("Hire Start", value=date.today())
end_d = c2.date_input("Hire End", value=date.today())
km_in = c3.number_input("One-Way Distance (KM)", min_value=0.0)
weeks = math.ceil(((end_d - start_d).days) / 7) if (end_d - start_d).days > 0 else 1

st.divider(); col_mq, col_cat = st.columns(2)

with col_mq:
    st.markdown("### ⚡ Marquee Calculator")
    m_in = st.text_input("Size (e.g. 10x15)")
    m_q = st.number_input("Quantity", min_value=1, key="mq")
    m_sec = st.radio("Securing", ["Weights", "Pegging"], horizontal=True)
    if st.button("Add Marquee"):
        nums = re.findall(r'\d+', m_in)
        if len(nums) >= 2:
            span, length = int(nums[0]), int(nums[1])
            new_rows = []
            if span == 3 and (length == 3 or length == 6):
                key = f"3m x {length}m {'Hi Top' if length==3 else 'Shade'}"
                data = MARQUEE_UNITS.get(key)
                h_val = data['rate'] * m_q; l_val = h_val * data['lab']
                new_rows.append({"Qty": m_q, "Product": key, "Unit Rate": data['rate'], "Total": 0.0, "Min_Lab": data['min'], "Raw_Lab": l_val, "Lab_Math": f"{key} Lab: ${h_val:,.2f} x 55% = ${l_val:,.2f}", "KG": data['kg']*m_q, "Is_Marquee": True, "Hire_Math_Str": f"{m_q} - {key} x ${data['rate']:,.2f} = ${h_val:,.2f}"})
                legs = data['legs']
            else:
                logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
                bays = math.ceil(length/logic['bay']); sqm = span*length
                rate = logic['s_rate'] if bays == 1 else logic['m_rate']
                lab_p = logic['s_lab'] if bays == 1 else logic['m_lab']
                h_val = sqm * rate * m_q; l_val = h_val * lab_p
                new_rows.append({"Qty": m_q, "Product": f"Structure {span}m x {length}m", "Unit Rate": sqm*rate, "Total": 0.0, "Min_Lab": logic['min_lab'], "Raw_Lab": l_val, "Lab_Math": f"Structure {span}x{length} Lab: ${h_val:,.2f} x {int(lab_p*100)}% = ${l_val:,.2f}", "KG": (sqm*15)*m_q, "Is_Marquee": True, "Hire_Math_Str": f"{m_q} - Structure {span}m x {length}m ({sqm}sqm x ${rate:,.2f}) = ${h_val:,.2f}" })
                legs = ((length/logic['bay'])+1)*2
            
            if m_sec == "Weights":
                w_tot = int(legs*6*m_q) # Locked safety logic[cite: 4]
                w_h = w_tot * CONFIG["WEIGHT_HIRE"]
                w_l = w_tot * CONFIG["WEIGHT_LABOUR"]
                new_rows.append({"Qty": w_tot, "Product": "30kg Marquee Weights", "Unit Rate": CONFIG["WEIGHT_HIRE"], "Total": 0.0, "Min_Lab": 0, "Raw_Lab": w_l, "Lab_Math": f"Weights Lab: {w_tot} units x $1.65 = ${w_l:,.2f}", "KG": w_tot*30, "Is_Marquee": True, "Hire_Math_Str": f"{w_tot} - Weights x ${CONFIG['WEIGHT_HIRE']} = ${w_h:,.2f}"})
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True); st.rerun()

# --- TOTALS & LOGISTICS ---
if not st.session_state.df.empty:
    st.divider(); st.data_editor(st.session_state.df[["Qty", "Product", "Unit Rate", "Total"]], use_container_width=True)
    h_tot, raw_l_sum, max_min_l, total_kg = 0.0, 0.0, 0.0, 0.0
    h_math, l_math = [], []
    for idx, row in st.session_state.df.iterrows():
        line_h = row["Qty"] * row["Unit Rate"] * (weeks if row["Is_Marquee"] and "Weight" not in row["Product"] else 1)
        h_tot += line_h; raw_l_sum += row["Raw_Lab"]; max_min_l = max(max_min_l, row["Min_Lab"])
        total_kg += row["KG"]; st.session_state.df.at[idx, "Total"] = line_h
        if row["Lab_Math"]: l_math.append(row["Lab_Math"])
        if row["Hire_Math_Str"]: h_math.append(row["Hire_Math_Str"])
    
    trucks = math.ceil(total_kg / CONFIG["TRUCK_PAYLOAD"]) if total_kg > 0 else 1
    final_lab = max(max_min_l, raw_l_sum); waiver = h_tot * 0.07; cartage = trucks * km_in * 4 * CONFIG["CARTAGE_RATE"]; grand = h_tot + final_lab + waiver + cartage
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("HIRE", f"${h_tot:,.2f}"); m2.metric("LABOUR", f"${final_lab:,.2f}"); m3.metric("LOAD (KG)", f"{total_kg:,.0f}kg"); m4.metric("TRUCKS", f"{trucks}")
    
    pdf_b = create_calculation_pdf(proj_name, st.session_state.df, h_tot, final_lab, waiver, cartage, grand, km_in, weeks, start_d, end_d, h_math, l_math, total_kg, trucks, wf_status)
    st.download_button(f"📥 DOWNLOAD {wf_status.upper()}", pdf_b, file_name=f"{proj_name}_{wf_status}.pdf")
    if st.button("CLEAR ALL"): st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.rerun()
