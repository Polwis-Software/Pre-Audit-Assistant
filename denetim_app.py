import streamlit as st
import pandas as pd
import altair as alt
from fpdf import FPDF
import base64

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Polwis | Audit Terminal", page_icon="📊", layout="wide")

# --- DARK MODE CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .main-header { background: #1E232E; padding: 25px; border-radius: 12px; border: 1px solid #30363D; margin-bottom: 25px; }
    div[data-testid="stMetric"] { background-color: #161B22 !important; border-radius: 10px; padding: 15px; border: 1px solid #30363D; }
    [data-testid="stMetricLabel"] { color: #8B949E !important; }
    [data-testid="stMetricValue"] { color: #58A6FF !important; }
    section[data-testid="stSidebar"] { background-color: #0E1117 !important; border-right: 1px solid #30363D; }
    h1, h2, h3, p, span { color: #F0F6FC !important; }
</style>
""", unsafe_allow_html=True)

# --- PDF OLUŞTURMA FONKSİYONU ---
def create_pdf(satis, aktif, kredi, ozk, bulgular):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Polwis Financial Audit Report", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total Revenue: {satis:,.0f} TRY", ln=True)
    pdf.cell(200, 10, txt=f"Total Assets: {aktif:,.0f} TRY", ln=True)
    pdf.cell(200, 10, txt=f"Financial Debt: {kredi:,.0f} TRY", ln=True)
    pdf.cell(200, 10, txt=f"Total Equity: {ozk:,.0f} TRY", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Audit Findings & Notes:", ln=True)
    pdf.set_font("Arial", '', 11)
    for b in bulgular:
        pdf.multi_cell(0, 10, txt=f"- {b}")
    return pdf.output(dest='S').encode('latin-1')

# --- HEADER ---
st.markdown("""
<div class='main-header'>
    <h1 style='margin:0; font-size: 26px; color: #58A6FF !important;'>PreFin</h1>
    <p style='margin:0; color: #8B949E !important; font-size: 18px;'>
        Fast and Easy Internal Control & Compliance Tool powered with Artificial Intelligence
    </p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ Settings")
kdv_oran = st.sidebar.multiselect("VAT Thresholds", [0.01, 0.10, 0.20], [0.20])
uploaded_file = st.sidebar.file_uploader("Upload Trial Balance", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df['Hesap Kodu'] = df['Hesap Kodu'].astype(str)
        satis, kdv391, alici120, aktif, pasif, kasa100, ortak131, kredi, faiz780, ozk = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        donen, duran, kvy, uvy = 0.0, 0.0, 0.0, 0.0
        bulgular_listesi = []

        for i, row in df.iterrows():
            kod, b, a = row['Hesap Kodu'], row.get('Borç Bakiye', 0), row.get('Alacak Bakiye', 0)
            bak = b - a
            if kod.startswith('1'): donen += bak; aktif += bak if bak > 0 else 0
            elif kod.startswith('2'): duran += bak; aktif += bak if bak > 0 else 0
            elif kod.startswith('3'): kvy += -bak; pasif += -bak if -bak > 0 else 0
            elif kod.startswith('4'): uvy += -bak; pasif += -bak if -bak > 0 else 0
            elif kod.startswith('5'): ozk += -bak; pasif += -bak if -bak > 0 else 0
            if kod.startswith('600'): satis += a
            if kod.startswith('391'): kdv391 += a
            if kod == '100': kasa100 += bak
            if kod == '131': ortak131 += bak
            if kod.startswith('300'): kredi += a
            if kod == '780': faiz780 += b

        # Metrikler
        cols = st.columns(4)
        cols[0].metric("Revenue", f"₺{satis:,.0f}")
        cols[1].metric("Assets", f"₺{aktif:,.0f}")
        cols[2].metric("Debt", f"₺{kredi:,.0f}")
        cols[3].metric("Equity", f"₺{ozk:,.0f}")

        # Bulguları Topla
        if satis > 0 and len(kdv_oran) > 0: # Liste boş değilse kontrol et
            ef = kdv391/satis
            if not (min(kdv_oran) <= ef <= max(kdv_oran)): 
                bulgular_listesi.append(f"VAT Mismatch: Effective rate is %{ef*100:.1f}")
        elif satis > 0:
            bulgular_listesi.append("VAT Analysis skipped: Please select at least one VAT rate.")

        # PDF BUTONU
        pdf_data = create_pdf(satis, aktif, kredi, ozk, bulgular_listesi)
        st.download_button(label="📥 Download Audit Report (PDF)", data=pdf_data, file_name="Audit_Report.pdf", mime="application/pdf")

    except Exception as e: st.error(f"Error: {e}")
