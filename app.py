import streamlit as st
import math
import pandas as pd
from datetime import date, datetime
from fpdf import FPDF
import re
import json
import os

# --- INITIAL CONFIG ---
st.set_page_config(page_title="Louis Master Quoter", layout="wide")

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

# --- GRANDSTAND BRACKET LOGIC ---
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
            desc = f"Labour Buildup: ({b['staff']} staff x {b['hrs']}hrs x $55) x 2 x 2 / {seats} seats"
            return round(per_seat, 2), desc
    return 0, ""

# --- PDF ENGINE ---
def clean_text(txt):
    if not txt: return ""
    replacements = {"®": "(R)", "™": "(TM)", "©": "(C)", "└": "->", "—": "-", "–": "-"}
    cleaned = str(txt)
    for char, rep in replacements.items():
        cleaned = cleaned.replace(char, rep)
    return cleaned.encode('latin-1', 'replace').decode('latin-1')

def create_calculation_pdf(name, subtotal, labour, waiver, cartage, grand, weeks, start, end, h_maths, l_details, log_maths, status):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text("Louis Quoting Tool - Calculation Analysis"), ln=True, align="C")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, clean_text(f"PROJECT: {name} | STATUS: {status.upper()}"), ln=True, align="C")
    pdf.cell(0, 7, f"HIRE PERIOD: {start.strftime('%d/%m/%Y')} to {end.strftime('%d/%m/%Y')} ({weeks} Week(s))", ln=True, align="C"); pdf.ln(5)
    
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " CALCULATIONS (Hire Breakdown)", 0, 1, "L", True); pdf.set_font("Arial", "", 10)
    for h in h_maths: 
        pdf.cell(0, 7, clean_text(f" {h}"), border="B", ln=True)
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 10, f" TOTAL HIRE: ${subtotal:,.2f}", ln=True, align="R"); pdf.ln(5)
    
    if labour > 0:
        pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, " OTHER LABOUR", 0, 1, "L", True); pdf.set_font("Arial", "", 10)
        for l in l_details: 
            pdf.cell(0, 7, clean_text(f" {l}"), border="B", ln=True)
        pdf.set_font("Arial", "B", 10); pdf.cell(0, 10, f" TOTAL LABOUR POOL: ${labour:,.2f}", ln=True, align="R"); pdf.ln(5)

    pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, " LOGISTICS & WAIVER PROOFS", 0, 1, "L", True); pdf.set_font("Arial", "", 10)
    for m in log_maths: 
        pdf.cell(0, 7, clean_text(f" {m}"), border="B", ln=True)
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 10, f" LOGISTICS SUBTOTAL: ${waiver + cartage:,.2f}", ln=True, align="R")
    
    pdf.ln(10); pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 15, f" GRAND TOTAL (EX GST): ${grand:,.2f} ", 0, 1, "R", True)
    return bytes(pdf.output())

# --- MASTER DATA ---
CATALOG = {
    "Flooring": {
        "I-Trac®": {"rate": 23.40, "block": 46.80, "lab_fix": 4.65, "kg": 15.0},
        "Supa-Trac®": {"rate": 11.55, "block": 25.00, "lab_fix": 4.65, "kg": 4.5, "sheet_sqm": 3.13},
        "Plastorip": {"rate": 10.15, "block": 20.30, "lab_fix": 3.05, "kg": 4.0},
        "Trakmat": {"rate": 22.05, "block": 44.10, "lab_fix": 5.00, "kg": 35.0}
    },
    "Grandstands": {
        "Standard Seating": {"rate": 15.00, "block": 30.00, "kg": 25.0}
    }
}
STRUCT_LOGIC = {span: {"bay": (5 if span >= 10 else 3), "s_rate": 23.0, "m_rate": 18.20, "s_lab": 0.40} for span in [3, 4, 6, 9, 10, 12, 15, 20]}
STAGES = ["Quoted", "Accepted", "Paid", "On Hire", "Returned", "Cancelled"]
STAGE_COLORS = {"Quoted": "#FF9100", "Accepted": "#00E676", "Paid": "#00B8D4", "On Hire": "#D500F9", "Returned": "#757575", "Cancelled": "#263238"}

# --- SESSION STATE ---
if 'df' not in st.session_state: 
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Total", "Min_Lab", "Raw_Lab", "KG", "Is_Marquee", "Discount", "Lab_Math", "Lab_Per_Unit", "Base_Hire"])
if 'status' not in st.session_state: st.session_state.status = "Quoted"
if 'proj' not in st.session_state: st.session_state.proj = "New Project"
if 'km' not in st.session_state: st.session_state.km = 0.0
if 'start_d' not in st.session_state: st.session_state.start_d = date.today()
if 'end_d' not in st.session_state: st.session_state.end_d = date.today()

def load_project_safe(fname):
    try:
        with open(f"quotes/{fname}", "r") as f:
            d = json.load(f); st.session_state.df = pd.DataFrame(d["items"])
            st.session_state.status, st.session_state.proj = d.get("status", "Quoted"), d.get("proj", fname.replace(".json", ""))
            st.session_state.start_d = datetime.strptime(d.get("start_date", str(date.today())), '%Y-%m-%d').date()
            st.session_state.end_d = datetime.strptime(d.get("end_date", str(date.today())), '%Y-%m-%d').date()
            st.session_state.km = float(d.get("km", 0.0))
            st.rerun()
    except: st.error("Load Error")

# --- UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #F4F7F9 !important; }
    h1 { color: #1A1D2D !important; font-size: 48px !important; font-weight: 900 !important; }
    h3 { color: #FFFFFF !important; border-left: 10px solid #00E676; padding: 15px; background-color: #1A1D2D; border-radius: 0 10px 10px 0; }
    div.stMetric { background-color: #FFFFFF !important; padding: 15px !important; border-radius: 12px !important; border: 2px solid #3D5AFE !important; }
    div[data-testid="stMetricValue"] { color: #3D5AFE !important; font-size: 32px !important; font-weight: 800 !important; }
    .item-text { font-size: 20px !important; font-weight: 700 !important; color: #1A1D2D; margin-top: 10px; }
    .gt-banner { background: #1A1D2D; color: #00E676; padding: 40px; border-radius: 20px; text-align: right; font-size: 44px !important; font-weight: 900; margin-top: 30px; border: 5px solid #00E676; }
    </style>
    """, unsafe_allow_html=True)

# --- DASHBOARD ---
st.title("⚡ Louis Master Quoter")
quoted_files = sorted([f for f in os.listdir("quotes") if f.endswith(".json")])

# --- SIDEBAR ---
st.sidebar.title("📁 PROJECT ARCHIVE")
if st.sidebar.button("➕ START NEW"):
    st.session_state.df = pd.DataFrame(columns=st.session_state.df.columns); st.session_state.km = 0.0; st.session_state.proj = "New Project"; st.rerun()
st.session_state.proj = st.sidebar.text_input("Project Label", st.session_state.proj)
if st.sidebar.button("💾 SAVE / UPDATE"):
    data = {"status": st.session_state.status, "items": st.session_state.df.to_dict(orient='records'), "proj": st.session_state.proj, "start_date": str(st.session_state.start_d), "end_date": str(st.session_state.end_d), "km": st.session_state.km}
    with open(f"quotes/{st.session_state.proj}.json", "w") as f: json.dump(data, f)
    st.sidebar.success("Saved!")
load_choice = st.sidebar.selectbox("Retrieval", ["-- Choose --"] + [f.replace(".json", "") for f in quoted_files])
if st.sidebar.button("📂 LOAD PROJECT") and load_choice != "-- Choose --": load_project_safe(f"{load_choice}.json")
if st.sidebar.button("🗑️ DELETE JOB") and load_choice != "-- Choose --": os.remove(f"quotes/{load_choice}.json"); st.rerun()

# --- WORKSPACE ---
st.markdown(f"### 📍 Project: {st.session_state.proj}")
st.session_state.status = st.selectbox("Stage", STAGES, index=STAGES.index(st.session_state.status) if st.session_state.status in STAGES else 0)
st.markdown(f"<div style='height: 14px; background-color: {STAGE_COLORS[st.session_state.status]}; border-radius: 7px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
st.session_state.start_d = c1.date_input("Start", value=st.session_state.start_d)
st.session_state.end_d = c2.date_input("End", value=st.session_state.end_d)
km_val = st.session_state.km if (st.session_state.km and st.session_state.km > 0) else None
st.session_state.km = c3.number_input("One-Way KM", value=km_val, placeholder="KM...")
weeks = math.ceil(((st.session_state.end_d - st.session_state.start_d).days) / 7) or 1

b1, b2 = st.columns(2)
cartage_mode, labour_mode = b1.segmented_control("Cartage", ["Charge", "Free"], default="Charge"), b2.segmented_control("Labour", ["Separate", "Include in Hire", "Free"], default="Separate")

st.divider(); col1, col2 = st.columns(2)
with col1:
    st.markdown("### ⚡ Structures")
    m_in, m_q = st.text_input("Size (10x15)"), st.number_input("Qty", min_value=1, value=None, key="mq_in")
    if st.button("Add Structure") and m_in and m_q:
        nums = re.findall(r'\d+', m_in)
        if len(nums) >= 2:
            span, length = int(nums[0]), int(nums[1])
            logic = STRUCT_LOGIC.get(span, STRUCT_LOGIC[4])
            sqm = span*length; hire_rate = logic['s_rate'] if (length/3) <= 1 else logic['m_rate']
            brate = sqm * hire_rate; l1 = brate * logic['s_lab']
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
                "Qty": m_q, "Product": f"Structure {span}x{length}m", "Unit Rate": brate, "Min_Lab": 350, 
                "Raw_Lab": l1, "Lab_Math": f"Structure {span}x{length}: ${l1:,.2f}", "KG": (sqm*15)*m_q, 
                "Is_Marquee": True, "Discount": 0.0, "Lab_Per_Unit": 0, "Base_Hire": brate
            }])], ignore_index=True); st.rerun()

with col2:
    st.markdown("### 🪵 Catalog Items")
    cat_sel = st.selectbox("Category", list(CATALOG.keys()))
    p_sel = st.selectbox("Product", list(CATALOG[cat_sel].keys()))
    f_qty = st.number_input("Seats / SQM Count", min_value=0.0, value=None, key="p_qty")
    if st.button("Add to Quote") and f_qty:
        data = CATALOG[cat_sel][p_sel]
        base_h = (data['block']/4) if (weeks >= 4 and 'block' in data) else data['rate']
        lab_per_unit, raw_lab_pool, lab_desc = 0, 0, ""
        if cat_sel == "Grandstands":
            lab_per_unit, lab_desc = get_gs_per_seat_labour(f_qty)
            unit_rate = base_h + lab_per_unit
        else:
            unit_rate = base_h; raw_lab_pool = f_qty * data.get('lab_fix', 0); lab_desc = f"{p_sel}: ${raw_lab_pool:,.2f}"
        eff_qty = (math.ceil(f_qty / data["sheet_sqm"]) * data["sheet_sqm"]) if "sheet_sqm" in data else f_qty
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([{
            "Qty": f_qty, "Product": p_sel, "Unit Rate": unit_rate, "Min_Lab": 0, "Raw_Lab": raw_lab_pool, 
            "Lab_Math": lab_desc, "KG": eff_qty * data['kg'], "Is_Marquee": False, "Discount": 0.0, 
            "Lab_Per_Unit": lab_per_unit, "Base_Hire": base_h
        }])], ignore_index=True); st.rerun()

# --- SUMMARY ---
if not st.session_state.df.empty:
    st.divider(); st.subheader("📝 QUOTE SUMMARY")
    h_tot_c, h_wk1_gear, total_kg, pdf_h, pdf_l = 0.0, 0.0, 0.0, [], []
    for idx, row in st.session_state.df.iterrows():
        qty, brate, dm = row["Qty"], row["Unit Rate"], (1 - (row["Discount"]/100))
        total_kg += row["KG"]; h_wk1_gear += (qty * row["Base_Hire"])
        wk1_t = (qty * brate + row["Raw_Lab"]) * dm if labour_mode == "Include in Hire" else (qty * brate) * dm
        h_tot_c += wk1_t
        c0, c1, c2, c3, c4, c5 = st.columns([0.4, 4.0, 0.8, 1.2, 1.0, 1.4])
        if c0.button("🗑️", key=f"sdel_{idx}"): st.session_state.df.drop(idx, inplace=True); st.rerun()
        c1.markdown(f"<div class='item-text'>{row['Product']} - Wk 1</div>", unsafe_allow_html=True)
        c2.write(f"{qty:,.0f}"); c3.write(f"${wk1_t/qty:,.2f}")
        st.session_state.df.at[idx, "Discount"] = c4.number_input("", 0.0, 100.0, float(row["Discount"]), 1.0, key=f"sd_{idx}", label_visibility="collapsed")
        c5.write(f"${wk1_t:,.2f}"); pdf_h.append(f"{row['Product']} Wk1: ${wk1_t:,.2f}")
        if row["Lab_Math"]: pdf_l.append(row["Lab_Math"])
        if weeks > 1:
            base_r = row["Base_Hire"]; r_rate, r_tot = (base_r * 0.5 if row["Is_Marquee"] else base_r), qty * (base_r * 0.5 if row["Is_Marquee"] else base_r) * (weeks-1) * dm
            h_tot_c += r_tot; cb = st.columns([0.4, 4.0, 0.8, 1.2, 1.0, 1.4])
            cb[1].markdown(f"<div style='color:grey; font-style:italic; font-size:18px;'>└ Recurring (x{weeks-1} wks)</div>", unsafe_allow_html=True)
            cb[2].write(f"{qty:,.0f}"); cb[3].write(f"${r_rate*dm:,.2f}"); cb[5].write(f"${r_tot:,.2f}"); pdf_h.append(f"-> Recurring: ${r_tot:,.2f}")

    trks, safe_km = (math.ceil(total_kg / 6000) or 1), (st.session_state.km if st.session_state.km else 0)
    wav, crt = h_wk1_gear * 0.07, trks * safe_km * 4 * 3.50 if cartage_mode == "Charge" else 0
    lab = max(st.session_state.df["Raw_Lab"].sum(), 350) if labour_mode == "Separate" else 0
    
    st.divider(); m = st.columns(6)
    m[0].metric("HIRE", f"${round(h_tot_c, 2):,}")
    m[1].metric("LABOUR", f"${round(lab, 2):,}")
    m[2].metric("WAIVER", f"${round(wav, 2):,}")
    m[3].metric("CARTAGE", f"${round(crt, 2):,}")
    m[4].metric("WEIGHT", f"{round(total_kg, 0):,}kg")
    m[5].metric("TRUCKS", f"{trks}")
    
    st.markdown(f"<div class='gt-banner'>GRAND TOTAL: ${h_tot_c + lab + wav + crt:,.2f}</div>", unsafe_allow_html=True)
    l_maths = [f"Damage Waiver (7%): ${h_wk1_gear:,.2f} x 0.07 = ${wav:,.2f}", f"Cartage: {trks} Trucks x {safe_km}km x 4 x $3.50 = ${crt:,.2f}"]
    pdf_b = create_calculation_pdf(st.session_state.proj, h_tot_c, lab, wav, crt, h_tot_c+lab+wav+crt, weeks, st.session_state.start_d, st.session_state.end_d, pdf_h, pdf_l, l_maths, st.session_state.status)
    st.download_button("📥 DOWNLOAD PDF", pdf_b, file_name=f"{st.session_state.proj}_Analysis.pdf")
