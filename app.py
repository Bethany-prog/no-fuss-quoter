import streamlit as st
import math
import pandas as pd
from datetime import date, datetime
from fpdf import FPDF
import re
import json
import os

# --- DIRECTORIES ---
if not os.path.exists("quotes"):
    os.makedirs("quotes")

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

# --- PDF GENERATOR ENGINE ---
def create_calculation_pdf(name, subtotal, labour, waiver, cartage, grand, weeks, start, end, h_maths, l_details, log_maths, status):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16); pdf.cell(0, 10, f"Louis Quoting Tool - Calculation Analysis", ln=True, align="C")
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 7, f"PROJECT: {name} | STATUS: {status.upper()}", ln=True, align="C")
    pdf.cell(0, 7, f"HIRE PERIOD: {start.strftime('%d/%m/%Y')} to {end.strftime('%d/%m/%Y')} ({weeks} Week(s))", ln=True, align="C"); pdf.ln(5)
    
    # Hire Section
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " CALCULATIONS (Hire Breakdown)", 0, 1, "L", True); pdf.set_font("Arial", "", 10)
    for h in h_maths: pdf.cell(0, 7, f" {h}", border="B", ln=True)
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 10, f" TOTAL HIRE: ${subtotal:,.2f}", ln=True, align="R"); pdf.ln(5)
    
    # Labour Section
    if labour > 0:
        pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, " LABOUR (Installation & Dismantle)", 0, 1, "L", True); pdf.set_font("Arial", "", 10)
        for l in l_details: pdf.cell(0, 7, f" {l}", border="B", ln=True)
        pdf.set_font("Arial", "B", 10); pdf.cell(0, 10, f" TOTAL LABOUR POOL: ${labour:,.2f}", ln=True, align="R"); pdf.ln(5)

    # Logistics & Waiver Section
    pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, " LOGISTICS & WAIVER PROOFS", 0, 1, "L", True); pdf.set_font("Arial", "", 10)
    for m in log_maths: pdf.cell(0, 7, f" {m}", border="B", ln=True)
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 10, f" LOGISTICS SUBTOTAL: ${waiver + cartage:,.2f}", ln=True, align="R")
    
    pdf.ln(10); pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 15, f" GRAND TOTAL (EX GST): ${grand:,.2f} ", 0, 1, "R", True)
    return bytes(pdf.output())

# --- VISUAL STYLING ---
st.markdown("""
    <style>
    .main { background-color: #F4F7F9 !important; }
    h1 { color: #1A1D2D !important; font-size: 48px !important; font-weight: 900 !important; }
    h3 { color: #FFFFFF !important; border-left: 10px solid #00E676; padding: 15px; background-color: #1A1D2D; border-radius: 0 10px 10px 0; }
    div.stMetric { background-color: #FFFFFF !important; padding: 25px !important; border-radius: 15px !important; border: 2px solid #3D5AFE !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important; }
    div[data-testid="stMetricValue"] { color: #3D5AFE !important; font-size: 34px !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] p { color: #5F6368 !important; font-weight: 700 !important; text-transform: uppercase; }
    .item-text { font-size: 19px !important; font-weight: 600 !important; color: #202124; margin-top: 5px; }
    .item-sub { font-size: 16px !important; color: #70757A; font-style: italic; }
    .gt-banner { background: #1A1D2D; color: #00E676; padding: 35px; border-radius: 20px; text-align: right; font-size: 44px !important; font-weight: 900; margin-top: 30px; border: 5px solid #00E676; }
    .urgent-card { background-color: #FFEBEE; border-left: 10px solid #D32F2F; padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #B71C1C; }
    .warning-card { background-color: #FFF3E0; border-left: 10px solid #F57C00; padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #E65100; }
    </style>
    """, unsafe_allow_html=True)

# --- MASTER DATA ---
GENERAL_PRODUCTS = {
    "Flooring": {
        "I-Trac®": {"rate": 23.40, "block": 46.80, "lab_fix": 4.65, "kg": 15.0},
        "Supa-Trac®": {"rate": 11.55, "block": 25.00, "lab_fix": 4.65, "kg": 4.5},
        "Plastorip": {"rate": 10.15, "block": 20.30, "lab_fix": 3.05, "kg": 4.0},
        "Rollout": {"rate": 7.10, "block": 15.00, "lab_fix": 3.05, "kg": 3.5},
        "Trakmat": {"rate": 22.05, "block": 44.10, "lab_fix": 5.00, "kg": 35.0}
    },
    "Accessories": {
        "Weights": {"rate": 6.60, "lab_fix": 1.65, "kg": 30.0},
        "I-Trac Ramps": {"rate": 42.00, "lab_fix": 0, "kg": 10.0},
        "Barrier": {"rate": 70.00, "lab_p": 0.40, "kg": 60.0}
    }
}
STRUCT_LOGIC = {
    3: {"bay": 3, "s_rate": 22.05, "m_rate": 22.05, "s_lab": 0.55, "m_lab": 0.55, "min_lab": 350.00},
    4: {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 350.00},
    6: {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 350.00},
    9: {"bay": 3, "s_rate": 23.00, "m_rate": 18.20, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 350.00},
    10: {"bay": 5, "s_rate": 23.00, "m_rate": 16.55, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 650.00},
    12: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 1500.00},
    15: {"bay": 5, "s_rate": 23.00, "m_rate": 15.45, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 1500.00},
    20: {"bay": 5, "s_rate": 19.95, "m_rate": 19.95, "s_lab": 0.40, "m_lab": 0.40, "min_lab": 0.00},
}
STAGES = ["Quoted", "Accepted", "Paid", "On Hire", "Returned", "Cancelled"]
STAGE_COLORS = {"Quoted": "#FF9100", "Accepted": "#00E676", "Paid": "#00B8D4", "On Hire": "#D500F9", "Returned": "#757575", "Cancelled": "#263238"}

# --- SESSION STATE ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount", "Lab_Math"])
if 'status' not in st.session_state: st.session_state.status = "Quoted"
if 'proj' not in st.session_state: st.session_state.proj = "New Project"
if 'km' not in st.session_state: st.session_state.km = 0.0
if 'start_d' not in st.session_state: st.session_state.start_d = date.today()
if 'end_d' not in st.session_state: st.session_state.end_d = date.today()

def load_project_safe(fname):
    try:
        with open(f"quotes/{fname}", "r") as f:
            d = json.load(f)
            st.session_state.df = pd.DataFrame(d["items"])
            if "Discount" not in st.session_state.df.columns: st.session_state.df["Discount"] = 0.0
            if "Lab_Math" not in st.session_state.df.columns: st.session_state.df["Lab_Math"] = ""
            st.session_state.status, st.session_state.proj = d.get("status", "Quoted"), d.get("proj", fname.replace(".json", ""))
            try: st.session_state.start_d = datetime.strptime(d.get("start_date"), '%Y-%m-%d').date()
            except: st.session_state.start_d = date.today()
            try: st.session_state.end_d = datetime.strptime(d.get("end_date"), '%Y-%m-%d').date()
            except: st.session_state.end_d = date.today()
            km_raw = d.get("km", 0.0)
            st.session_state.km = float(km_raw) if km_raw is not None else 0.0
    except: st.error("Load Error")

# --- MAIN UI ---
st.title("📦 NO FUSS QUOTING ENGINE")

# --- DASHBOARD ---
quoted_files = [f for f in os.listdir("quotes") if f.endswith(".json")]
for fn in quoted_files:
    try:
        with open(f"quotes/{fn}", "r") as f:
            p = json.load(f)
            if p.get("status") == "Quoted" and p.get("start_date"):
                sd = datetime.strptime(p["start_date"], '%Y-%m-%d').date()
                diff = (sd - date.today()).days
                if 0 <= diff <= 28:
                    cl, cr = st.columns([5, 1])
                    cl.warning(f"**{p.get('proj')}** starts in {diff} days.")
                    if cr.button("📂 LOAD", key=f"edit_{fn}"): load_project_safe(fn); st.rerun()
    except: continue

# --- SIDEBAR ---
st.sidebar.title("📁 ARCHIVE")
if st.sidebar.button("➕ START NEW"):
    st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.session_state.km = 0.0; st.rerun()
st.session_state.proj = st.sidebar.text_input("Project Label", st.session_state.proj)
if st.sidebar.button("💾 SAVE PROJECT"):
    data = {"status": st.session_state.status, "items": st.session_state.df.to_dict(orient='records'), "proj": st.session_state.proj, "start_date": str(st.session_state.start_d), "end_date": str(st.session_state.end_d), "km": st.session_state.km}
    with open(f"quotes/{st.session_state.proj}.json", "w") as f: json.dump(data, f)
    st.sidebar.success("Saved!")

saved_quotes = sorted([f.replace(".json", "") for f in os.listdir("quotes") if f.endswith(".json")])
load_choice = st.sidebar.selectbox("Retrieval", ["-- Choose --"] + saved_quotes)
if st.sidebar.button("📂 LOAD PROJECT") and load_choice != "-- Choose --": load_project_safe(f"{load_choice}.json"); st.rerun()
if st.sidebar.button("🗑️ DELETE JOB") and load_choice != "-- Choose --": os.remove(f"quotes/{load_choice}.json"); st.rerun()

# --- WORKSPACE ---
st.markdown(f"### 📍 Project: {st.session_state.proj}")
st.session_state.status = st.selectbox("Stage", STAGES, index=STAGES.index(st.session_state.status) if st.session_state.status in STAGES else 0)
st.markdown(f"<div style='height: 12px; background-color: {STAGE_COLORS[st.session_state.status]}; border-radius: 6px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
st.session_state.start_d, st.session_state.end_d = c1.date_input("Start", value=st.session_state.start_d), c2.date_input("End", value=st.session_state.end_d)
km_val = st.session_state.km if (st.session_state.km and st.session_state.km > 0) else None
st.session_state.km = c3.number_input("One-Way KM", value=km_val, placeholder="Enter KM...")

diff = (st.session_state.end_d - st.session_state.start_d).days
weeks = math.ceil(diff / 7) if diff > 0 else 1
st.info(f"**Duration:** {diff // 7} Weeks, {diff % 7} Days")

st.markdown("#### 💳 BILLING")
b1, b2 = st.columns(2)
cartage_mode = b1.segmented_control("Cartage", ["Charge", "Free"], default="Charge")
labour_mode = b2.segmented_control("Labour", ["Separate", "Include in Hire", "Free"], default="Separate")

st.divider(); col1, col2 = st.columns(2)
with col1:
    st.markdown("### ⚡ Structures")
    m_in, m_q = st.text_input("Size (10x15)"), st.number_input("Qty", min_value=1, value=None)
    m_sec = st.radio("Securing", ["Weights", "Pegging"], horizontal=True)
    if st.button("Add Structure") and m_in and m_q:
        nums = re.findall(r'\d+', m_in)
        if len(nums) >= 2:
            span, length = int(nums[0]), int(nums[1])
            logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
            sqm = span*length; rate = logic['s_rate'] if (length/logic['bay']) <= 1 else logic['m_rate']
            h1 = sqm * rate * m_q; l1 = h1 * logic['s_lab']
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"Qty": m_q, "Product": f"Structure {span}x{length}m", "Unit Rate": sqm*rate, "Min_Lab": logic['min_lab'], "Raw_Lab": l1, "Lab_Math": f"Structure {span}x{length}: ${h1:,.2f} x {int(logic['s_lab']*100)}% = ${l1:,.2f}", "KG": (sqm*15)*m_q, "Is_Marquee": True, "Discount": 0.0}])], ignore_index=True)
            if m_sec == "Weights":
                w_tot = int((((length/logic['bay'])+1)*2)*6*m_q)
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"Qty": w_tot, "Product": "30kg Weights", "Unit Rate": 6.60, "Min_Lab": 0, "Raw_Lab": w_tot*1.65, "Lab_Math": f"Weights: {w_tot} x $1.65 = ${w_tot*1.65:,.2f}", "KG": w_tot*30, "Is_Marquee": True, "Discount": 0.0}])], ignore_index=True)
            st.rerun()
with col2:
    st.markdown("### 🪵 Flooring / Accs")
    p_sel = st.selectbox("Product", list(GENERAL_PRODUCTS["Flooring"].keys()) + list(GENERAL_PRODUCTS["Accessories"].keys()))
    f_qty = st.number_input("Amount", min_value=0.0, value=None)
    if st.button("Add Item") and f_qty:
        data = {**GENERAL_PRODUCTS["Flooring"], **GENERAL_PRODUCTS["Accessories"]}[p_sel]
        f_rate = (data['block']/4) if (weeks >= 4 and 'block' in data) else data.get('rate', 70)
        l1 = f_qty * data.get('lab_fix', (f_qty * f_rate * data.get('lab_p', 0)))
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{"Qty": f_qty, "Product": p_sel, "Unit Rate": f_rate, "Min_Lab": 0, "Raw_Lab": l1, "Lab_Math": f"{p_sel}: {f_qty} units x ${data.get('lab_fix', 0)} = ${l1:,.2f}", "KG": f_qty * data.get('kg', 0), "Is_Marquee": False, "Discount": 0.0}])], ignore_index=True); st.rerun()

# --- SUMMARY & PDF CALCS ---
if not st.session_state.df.empty:
    st.divider(); st.subheader("📝 QUOTE SUMMARY")
    hc = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
    cols = ["", "DESCRIPTION", "QTY", "RATE", "DISC%", "TOTAL"]
    for i, col in enumerate(hc): col.write(f"**{cols[i]}**")
    
    h_tot_c, h_wk1_gear, total_kg, pdf_h, pdf_l = 0.0, 0.0, 0.0, [], []
    for idx, row in st.session_state.df.iterrows():
        qty, brate, dm = row["Qty"], row["Unit Rate"], (1 - (row["Discount"]/100))
        total_kg += row["KG"]; h_wk1_gear += (qty * brate)
        c0, c1, c2, c3, c4, c5 = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
        if c0.button("🗑️", key=f"del_{idx}"): st.session_state.df.drop(idx, inplace=True); st.rerun()
        
        wk1_t = (qty * brate + row["Raw_Lab"]) * dm if labour_mode == "Include in Hire" else (qty * brate) * dm
        h_tot_c += wk1_t
        c1.markdown(f"<div class='item-text'>{row['Product']} - Wk 1</div>", unsafe_allow_html=True)
        c2.write(f"{qty:,.0f}"); c3.write(f"${wk1_t/qty:,.2f}")
        st.session_state.df.at[idx, "Discount"] = c4.number_input("", 0.0, 100.0, float(row["Discount"]), 1.0, key=f"d_{idx}", label_visibility="collapsed")
        c5.write(f"${wk1_t:,.2f}")
        pdf_h.append(f"{row['Product']} Wk1: ${wk1_t:,.2f} (Incl {row['Discount']}% Disc)")
        if row["Lab_Math"]: pdf_l.append(row["Lab_Math"])

        if weeks > 1:
            r_rate = brate * 0.5 if row["Is_Marquee"] else brate
            r_tot = qty * r_rate * (weeks-1) * dm; h_tot_c += r_tot
            cb = st.columns([0.4, 3.2, 0.8, 1.2, 1, 1.2])
            cb[1].markdown(f"<div class='item-sub'>└ Recurring Hire (x{weeks-1} wks)</div>", unsafe_allow_html=True)
            cb[2].write(f"{qty:,.0f}"); cb[3].write(f"${r_rate*dm:,.2f}"); cb[5].write(f"${r_tot:,.2f}")
            pdf_h.append(f"└ Recurring: ${r_tot:,.2f}")

    trks = math.ceil(total_kg / 6000) if total_kg > 0 else 1
    wav, crt = h_wk1_gear * 0.07, trks * (st.session_state.km if st.session_state.km else 0) * 4 * 3.50 if cartage_mode == "Charge" else 0
    lab = max(st.session_state.df["Min_Lab"].max(), st.session_state.df["Raw_Lab"].sum()) if labour_mode == "Separate" else 0
    l_maths = [f"Damage Waiver (7% of Wk1 Gear): ${h_wk1_gear:,.2f} x 7% = ${wav:,.2f}", f"Cartage: {trks} Trucks x {st.session_state.km}km x 4 trips x $3.50 = ${crt:,.2f}"]

    st.divider(); m = st.columns(6)
    m[0].metric("HIRE", f"${h_tot_c:,.2f}"); m[1].metric("LABOUR", f"${lab:,.2f}"); m[2].metric("WAIVER", f"${wav:,.2f}"); m[3].metric("CARTAGE", f"${crt:,.2f}"); m[4].metric("WEIGHT", f"{total_kg:,.0f}kg"); m[5].metric("TRUCKS", f"{trks}")
    st.markdown(f"<div class='gt-banner'>GRAND TOTAL: ${h_tot_c + lab + wav + crt:,.2f}</div>", unsafe_allow_html=True)
    
    pdf_b = create_calculation_pdf(st.session_state.proj, h_tot_c, lab, wav, crt, h_tot_c+lab+wav+crt, weeks, st.session_state.start_d, st.session_state.end_d, pdf_h, pdf_l, l_maths, st.session_state.status)
    st.download_button(f"📥 DOWNLOAD {st.session_state.status.upper()} PDF", pdf_b, file_name=f"{st.session_state.proj}_Analysis.pdf")
