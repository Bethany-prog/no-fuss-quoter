import streamlit as st
import math
from datetime import date

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
            else:
                st.error("❌ Incorrect Code")
        return False
    return True

if not check_password():
    st.stop()

# 2. PAGE CONFIG & STYLING
st.set_page_config(page_title="NO FUSS | Quote Builder", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0F111A; }
    label, .stCheckbox { color: #000000 !important; font-weight: 800 !important; }
    [data-testid="stMetricValue"] { color: #00E676 !important; font-size: 26px !important; }
    div.stMetric { background-color: #1A1D2D; padding: 15px; border-radius: 12px; border: 2px solid #3D5AFE; }
    [data-testid="stExpander"] { border: 2px solid #3D5AFE; border-radius: 12px; background-color: #FFFFFF; }
    .quote-box { background-color: #F8F9FA; color: #1A1D2D; padding: 20px; border-radius: 10px; border-left: 10px solid #3D5AFE; font-family: monospace; }
    .system-helper { background-color: #161925; padding: 15px; border-radius: 10px; border: 1px solid #444; color: #00E676; }
    </style>
    """, unsafe_allow_html=True)

# 3. PRODUCT CATALOG
PRODUCT_CATALOG = {
    "I-Trac (sqm)": {"rate": 23.40, "labour": 4.65},
    "Supa-Trac (sqm)": {"rate": 11.55, "labour": 4.65},
    "No Fuss Floor (sqm)": {"rate": 7.10, "labour": 3.05},
    "Terratrak Plus (sqm)": {"rate": 23.40, "labour": 4.65},
    "Wooden Floor (sqm)": {"rate": 8.85, "labour": 7.15},
    "Parquetry Dance Floor (sqm)": {"rate": 20.95, "labour": 4.80},
    "Protectall (sqm)": {"rate": 22.05, "labour": 3.25},
    "LD 20 Roll (3m x 20m)": {"rate": 1800.00, "labour": 0.00},
}

if 'quote_items' not in st.session_state:
    st.session_state.quote_items = []

st.title("📝 Pro Quote Builder")

# --- SECTION 1: CUSTOMER & JOB DETAILS ---
with st.expander("👤 JOB & CONTACT INFO", expanded=True):
    client_name = st.text_input("Client Name", value="GGOZ PTY LTD")
    job_ref = st.text_input("Job Reference", value="GGOZ- Caulfield North")
    delivery_addr = st.text_area("Delivery Address", value="278 Oorong Road, Caulfield North VIC 3161")
    ordered_by = st.text_input("Ordered By", value="Luke Ford")

# --- SECTION 2: LOGISTICS ---
with st.expander("📍 LOGISTICS & DATES", expanded=False):
    c1, c2 = st.columns(2)
    start_date = c1.date_input("Hire Start", value=date.today(), format="DD/MM/YYYY")
    end_date = c2.date_input("Hire End", value=date.today().replace(month=date.today().month+1), format="DD/MM/YYYY")
    km_input = st.number_input("One-Way KM", min_value=0.0, value=0.0)
    charge_cartage = st.checkbox("Charge Cartage?", value=True)

# --- SECTION 3: ADD PRODUCTS ---
st.markdown("### ➕ ADD PRODUCTS")
item_choice = st.selectbox("Select Item", sorted(PRODUCT_CATALOG.keys()))
qty = st.number_input("Quantity (sqm/pcs)", min_value=0.0, value=0.0)

if st.button("ADD TO QUOTE"):
    if qty > 0:
        days = (end_date - start_date).days
        weeks = math.ceil(days / 7) if days > 0 else 1
        rate = PRODUCT_CATALOG[item_choice]["rate"]
        total_hire = (qty * rate) + (qty * rate * (weeks - 1))
        
        st.session_state.quote_items.append({
            "Item": item_choice, "Qty": qty, "Weeks": weeks,
            "Rate": rate, "TotalHire": total_hire,
            "Labour": qty * PRODUCT_CATALOG[item_choice]["labour"]
        })
        st.rerun()

# --- SECTION 4: QUOTE GENERATION ---
if st.session_state.quote_items:
    st.markdown("### 📄 FINAL QUOTE TRANSFER BLOCK")
    
    # CALCULATIONS
    rent_total = sum(i["TotalHire"] for i in st.session_state.quote_items)
    rent_total = max(300.0, rent_total) # Min Fee
    transport = (km_input * 4 * 3.50) if charge_cartage else 0.0
    net_total = rent_total + transport + sum(i["Labour"] for i in st.session_state.quote_items)
    gst = net_total * 0.10
    gross = net_total + gst

    # THE TRANSFER BLOCK (Copy/Paste ready)
    quote_text = f"""
    JOB: {job_ref}
    CLIENT: {client_name}
    ORDERED BY: {ordered_by}
    ADDRESS: {delivery_addr}
    HIRE PERIOD: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}
    --------------------------------------------------
    ITEM BREAKDOWN:
    """
    for i in st.session_state.quote_items:
        sys_rate = i["TotalHire"] / i["Qty"]
        quote_text += f"\n- {i['Item']}: Qty {i['Qty']} | System Rate: ${sys_rate:.2f}"

    quote_text += f"""
    --------------------------------------------------
    SUMMARY:
    Total Rental Stock:  ${rent_total:,.2f}
    Total Transport:     ${transport:,.2f}
    Net Total (Ex GST):  ${net_total:,.2f}
    GST (10%):           ${gst:,.2f}
    Gross Total:         ${gross:,.2f}
    """
    
    st.markdown(f'<div class="quote-box"><pre>{quote_text}</pre></div>', unsafe_allow_html=True)
    
    # TOTALS DASHBOARD
    st.markdown("### 💰 TOTALS DASHBOARD")
    r1c1, r1c2 = st.columns(2)
    r1c1.metric("RENTAL STOCK", f"${rent_total:,.2f}")
    r1c2.metric("TRANSPORT", f"${transport:,.2f}")
    
    st.metric("GROSS TOTAL (INC GST)", f"${gross:,.2f}")

    if st.button("🗑️ RESET ALL"):
        st.session_state.quote_items = []
        st.rerun()
