import streamlit as st
import math
import pandas as pd
from datetime import date
from fpdf import FPDF
import re
import json
import os

# --- v32.0 CONFIGURATION & DIRECTORIES ---
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

# --- MASTER LOGIC (LOCKED) ---
# Sourced from Engineering & Cartage Logic documents[cite: 4]
CONFIG = {
    "WEIGHT_UNIT_KG": 30,
    "WEIGHT_HIRE": 6.60,
    "WEIGHT_LABOUR": 1.65, # Fixed 25% of hire[cite: 4]
    "TRUCK_PAYLOAD": 6000,
    "CARTAGE_RATE": 3.50
}

# --- PDF ENGINE v32 (WORKFLOW AWARE) ---
def create_calculation_pdf(name, df, subtotal, labour, waiver, cartage, grand, km, weeks, start, end, h_maths, l_details, kg, trucks, status):
    pdf = FPDF()
    pdf.add_page()
    
    # Title based on Workflow Status
    title = "TAX INVOICE" if status == "Invoiced" else "QUOTE CALCULATION SHEET"
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"No Fuss Event Hire - {title}", ln=True, align="C")
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, f"STATUS: {status.upper()} | DATES: {start} to {end} ({weeks} Weeks)", ln=True, align="C")
    
    # Logistics Header for Dispatch
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 7, f"Payload: {kg:,.0f}kg | Logistics: {trucks} x 6,000kg Trucks Required", ln=True, align="C")
    pdf.ln(5)

    # Tables and Math... (Same as previous version)
    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255)
    pdf.cell(85, 10, " Product Description", 1, 0, "L", True); pdf.cell(20, 10, " Qty", 1, 0, "C", True)
    pdf.cell(35, 10, " Rate", 1, 0, "C", True); pdf.cell(45, 10, " Total", 1, 1, "R", True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    for _, row in df.iterrows():
        pdf.cell(85, 8, f" {row['Product']}", 1)
        pdf.cell(20, 8, f" {row['Qty']:,.1f}", 1, 0, "C")
        pdf.cell(35, 8, f" ${row['Unit Rate']:,.2f}", 1, 0, "C")
        pdf.cell(45, 8, f" ${row['Total']:,.2f}", 1, 1, "R")

    # If Dispatched, add a Load List summary
    if status == "Dispatched":
        pdf.ln(10); pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "LOAD LIST (FOR DRIVER)", ln=True)
        pdf.set_font("Arial", "", 10)
        for _, row in df.iterrows():
            pdf.cell(0, 7, f"[ ] {row['Qty']:,.0f} x {row['Product']} ({row['KG']:,.0f}kg total)", ln=True)

    return bytes(pdf.output())

# --- UI STYLING & SESSION STATE ---
st.set_page_config(page_title="No Fuss Quote Pro v32.0", layout="wide")
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "Lab_Math", "KG", "Is_Marquee", "Hire_Math_Str"])

# --- SIDEBAR: RETRIEVAL & WORKFLOW ---
st.sidebar.title("📁 Quote Management")
project_name = st.sidebar.text_input("Project Name", "New_Project")
workflow_status = st.sidebar.selectbox("Workflow Step", ["Draft", "Invoiced", "Dispatched", "Returned"])

if st.sidebar.button("💾 SAVE QUOTE"):
    quote_data = {
        "status": workflow_status,
        "items": st.session_state.df.to_dict(orient='records'),
        "project": project_name
    }
    with open(f"quotes/{project_name}.json", "w") as f:
        json.dump(quote_data, f)
    st.sidebar.success("Saved to /quotes/")

st.sidebar.divider()
saved_files = [f.replace(".json", "") for f in os.listdir("quotes") if f.endswith(".json")]
load_file = st.sidebar.selectbox("Load Existing", ["None"] + saved_files)

if st.sidebar.button("📂 LOAD QUOTE") and load_file != "None":
    with open(f"quotes/{load_file}.json", "r") as f:
        loaded = json.load(f)
        st.session_state.df = pd.DataFrame(loaded["items"])
        st.rerun()

# --- MAIN ENGINE (Same logic as provided, integrated with CONFIG) ---
st.title(f"📦 No Fuss Engine: {project_name}")
# ... [Rest of your UI logic for adding Marquees and Flooring] ...
# NOTE: Ensure you replace weight labor with CONFIG['WEIGHT_LABOUR'] (1.65)[cite: 4]
