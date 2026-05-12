import streamlit as st
from streamlit_gsheets import GSheetsConnection
import math
import pandas as pd
from datetime import date
from fpdf import FPDF
import io

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

# 2. DATABASE CONNECTION
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_google(name, df, start, end, km):
    try:
        new_entry = pd.DataFrame([{
            "Quote_Name": name, "Data_JSON": df.to_json(orient='records'),
            "Start_Date": str(start), "End_Date": str(end), "KM": km, "Saved_Date": str(date.today())
        }])
        existing_data = conn.read(ttl=0)
        updated_data = pd.concat([existing_data, new_entry], ignore_index=True)
        conn.update(data=updated_data)
        st.cache_data.clear()
        return True
    except: return False

# --- PDF GENERATION (v25.0) ---
def create_calculation_pdf(name, df, subtotal, labour, waiver, cartage, grand_total, km, weeks, lab_mode):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "No Fuss Event Hire - Internal Calculation Sheet", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Generated on: {date.today()}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Quote: {name}", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(26, 29, 45); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 10, " Product", 1, 0, "L", True); pdf.cell(25, 10, " Qty", 1, 0, "C", True)
    pdf.cell(35, 10, " Rate", 1, 0, "C", True); pdf.cell(40, 10, " Total", 1, 1, "R", True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    math_parts = []
    for _, row in df.iterrows():
        pdf.cell(80, 8, f" {row['Product']}", 1)
        pdf.cell(25, 8, f" {row['Qty']} {row['Unit_Type']}", 1, 0, "C")
        pdf.cell(35, 8, f" ${row['Unit Rate']:,.2f}", 1, 0, "C")
        pdf.cell(40, 8, f" ${row['Total']:,.2f}", 1, 1, "R")
        math_parts.append(f"{row['Qty']} x ${row['Unit Rate']:,.2f}")
    
    pdf.ln(10); pdf.set_font("Arial", "B", 13); pdf.cell(0, 10, "Financial Breakdown", ln=True)
    pdf.set_font("Arial", "B", 11); pdf.cell(100, 8, "Base Hire Subtotal:", 0); pdf.cell(0, 8, f"${subtotal:,.2f}", 0, 1, "R")
    pdf.set_font("Arial", "I", 9); pdf.set_text_color(100, 100, 100)
    sub_math = " + ".join(math_parts)
    if weeks > 1: sub_math = f"({sub_math}) x {weeks} weeks"
    pdf.cell(0, 5, f"Calc: {sub_math}", ln=True)
    
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "B", 11)
    pdf.cell(100, 8, "Damage Waiver (7%):", 0); pdf.cell(0, 8, f"${waiver:,.2f}", 0, 1, "R")
    pdf.set_font("Arial", "I", 9); pdf.set_text_color(100, 100, 100); pdf.cell(0, 5, f"Calc: ${subtotal:,.2f} x 0.07", ln=True)
    
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "B", 11)
    pdf.cell(100, 8, "Cartage Total:", 0); pdf.cell(0, 8, f"${cartage:,.2f}", 0, 1, "R")
    pdf.set_font("Arial", "I", 9); pdf.set_text_color(100, 100, 100); pdf.cell(0, 5, f"Calc: {km} km x 4 trips x $3.50/km", ln=True)
    
    pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "B", 14); pdf.cell(100, 12, "GRAND TOTAL (EX GST):", "T"); pdf.cell(0, 12, f"${grand_total:,.2f}", "T", 1, "R")
    return bytes(pdf.output())

# 3. MASTER CATALOG
CATALOG = {
    "MARQUEE": {
        "Structures": [
            # Weights Req synced to Column G "AMMOUNT"
            {"Product": "Marquee 3 X 3", "w1_3": 207.00, "labour": 113.85, "weights_req": 24, "unit": "ea"},
            {"Product": "Marquee 4 X 3", "w1_3": 276.00, "labour": 151.80, "weights_req": 0, "unit": "ea"},
            {"Product": "Marquee 6 X 3", "w1_3": 414.00, "labour": 227.70, "weights_req": 0, "unit": "ea"},
            {"Product": "Marquee 9 X 3", "w1_3": 621.00, "labour": 341.55, "weights_req": 0, "unit": "ea"},
            {"Product": "Marquee 10 X 5", "w1_3": 1150.00, "labour": 632.50, "weights_req": 0, "unit": "ea"},
            {"Product": "Marquee 12 X 5", "w1_3": 1380.00, "labour": 759.00, "weights_req": 0, "unit": "ea"},
            {"Product": "Marquee 15 X 5", "w1_3": 1725.00, "labour": 948.75, "weights_req": 0, "unit": "ea"}
        ]
    },
    "FLOORING": {
        "Supa-Trac System": [
            {"Product": "Supa-trac flooring", "w1_3": 11.55, "block": 25.00, "labour": 4.65, "unit": "SQM", "waiver": True}
        ]
    }
}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo", "Unit_Type", "Is_ST"])

st.title("📦 No Fuss Quote Pro")

# LOGISTICS
c1, c2, c3 = st.columns(3)
start_date = c1.date_input("Hire Start", value=date.today())
end_date = c2.date_input("Hire End", value=date.today())
km_input = c3.number_input("Distance (KM)", min_value=0.0, value=None)
live_weeks = math.ceil(((end_date - start_date).days) / 7) if (end_date - start_date).days > 0 else 1

# ADD PRODUCT
dept_col, bundle_col = st.columns(2)
dept_choice = dept_col.selectbox("Department", sorted(CATALOG.keys()))
bundle_choice = bundle_col.selectbox("Select Group", sorted(CATALOG[dept_choice].keys()))
selected_bundle = CATALOG[dept_choice][bundle_choice]

bundle_results = []
for item in selected_bundle:
    q_val = st.number_input(f"Qty: {item['Product']} ({item['unit']})", min_value=0.0, key=f"q_{item['Product']}")
    secure_method = None
    if q_val and q_val > 0 and dept_choice == "MARQUEE":
        secure_method = st.radio(f"Securing for {item['Product']}?", ["Weights", "Pegging"], horizontal=True, key=f"sec_{item['Product']}")
    if q_val and q_val > 0: bundle_results.append({"item": item, "qty": q_val, "secure": secure_method})

if st.button("ADD SELECTED ITEMS TO QUOTE"):
    new_rows = []
    for entry in bundle_results:
        it, q, secure = entry['item'], entry['qty'], entry['secure']
        # Add structure
        new_rows.append({"Qty": q, "Product": it['Product'], "Unit Rate": it['w1_3'], "Disc %": 0.0, "Total": 0.0, "Labour_Rate": it['labour'], "Block_Rate": it.get('block', it['w1_3']), "SYSTEM RATE": 0.0, "No_Waiver": False, "Unit_Type": it['unit']})
        # Add securing
        if secure == "Weights" and it.get('weights_req', 0) > 0:
            w_qty = q * it['weights_req']
            new_rows.append({"Qty": w_qty, "Product": f"Orange Weight (For {it['Product']})", "Unit Rate": 6.60, "Disc %": 0.0, "Total": 0.0, "Labour_Rate": 0.0, "Block_Rate": 6.60, "SYSTEM RATE": 0.0, "No_Waiver": False, "Unit_Type": "ea"})
        elif secure == "Pegging":
            new_rows.append({"Qty": q, "Product": f"Pegging (For {it['Product']})", "Unit Rate": 0.0, "Disc %": 0.0, "Total": 0.0, "Labour_Rate": 0.0, "Block_Rate": 0.0, "SYSTEM RATE": 0.0, "No_Waiver": True, "Unit_Type": "ea"})
    if new_rows: st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True); st.rerun()

# FINANCES
if not st.session_state.df.empty:
    display_cols = ["Qty", "Unit_Type", "Product", "Unit Rate", "Disc %", "SYSTEM RATE", "Total"]
    st.data_editor(st.session_state.df[display_cols], use_container_width=True, key="editor")
    
    labour_mode = st.selectbox("Labour Mode", ["Bake Labour into Unit Rate", "Show Labour as Separate Line Item", "No Labour"])
    charge_cartage, include_damage_waiver = st.checkbox("🚚 Include Cartage", value=True), st.checkbox("🛡️ Include Damage Waiver (7%)", value=True)
    
    hire_total, lab_total, waiver_total = 0.0, 0.0, 0.0
    for idx, row in st.session_state.df.iterrows():
        q, r, d, b, lr = row["Qty"], row["Unit Rate"], row["Disc %"], row["Block_Rate"], row["Labour_Rate"]
        hire_val = (q * (b / 4) * live_weeks) if live_weeks >= 4 else (q * r * live_weeks)
        hire_disc = hire_val * (1 - (d / 100))
        if include_damage_waiver and not row["No_Waiver"]: waiver_total += hire_disc * 0.07
        item_lab = q * lr if labour_mode == "Bake Labour into Unit Rate" else 0.0
        if labour_mode == "Show Labour as Separate Line Item": lab_total += (q * lr) * (1 - (d / 100))
        total_line = hire_disc + (item_lab * (1 - (d / 100)))
        st.session_state.df.at[idx, "Total"], st.session_state.df.at[idx, "SYSTEM RATE"] = total_line, (total_line / q if q > 0 else 0)
        hire_total += total_line

    cart_val = (km_input * 14.0 if km_input and charge_cartage else 0)
    final_grand = hire_total + lab_total + waiver_total + cart_val

    st.divider(); m1, m2, m3, m4 = st.columns(4)
    m1.metric("SUBTOTAL", f"${hire_total:,.2f}"); m2.metric("LABOUR", f"${lab_total:,.2f}"); m3.metric("WAIVER", f"${waiver_total:,.2f}"); m4.metric("CARTAGE", f"${cart_val:,.2f}")
    st.metric("GRAND TOTAL (EX GST)", f"${final_grand:,.2f}")

    fn = st.text_input("Quote Name:", placeholder="Client Name")
    pdf_bytes = create_calculation_pdf(fn if fn else "Internal_Quote", st.session_state.df, hire_total, lab_total, waiver_total, cart_val, final_grand, km_input if km_input else 0, live_weeks, labour_mode)
    st.download_button("📥 DOWNLOAD INTERNAL PDF", data=pdf_bytes, file_name=f"{fn}_Calculations.pdf", mime="application/pdf")
    if st.button("⚠️ RESET ALL"): st.session_state.df = pd.DataFrame(columns=["Qty", "Product", "Unit Rate", "Disc %", "Total", "Labour_Rate", "Block_Rate", "SYSTEM RATE", "No_Waiver", "Is_GS", "Is_Mojo", "Unit_Type", "Is_ST"]); st.rerun()
