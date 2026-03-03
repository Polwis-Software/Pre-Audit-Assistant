import streamlit as st
import pandas as pd
import altair as alt

# --- KURUMSAL SAYFA AYARLARI ---
st.set_page_config(page_title="Polwis | Financial Audit Terminal", page_icon="📈", layout="wide")

# --- PROFESYONEL FİNANSAL TEMA (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F4F7F9; }
    
    /* Kurumsal Header */
    .main-header {
        background: linear-gradient(90deg, #1A3755 0%, #2E5077 100%);
        padding: 30px;
        border-radius: 12px;
        color: white;
        text-align: left;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Metrik Kartları */
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #1A3755;
    }
    
    /* Sidebar Düzeni */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E1E4E8;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class='main-header'>
    <h1 style='margin:0; font-size: 28px;'>Polwis Financial Audit Terminal</h1>
    <p style='margin:0; opacity: 0.8;'>Professional Pre-Audit & Internal Control Analytics</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR (KONTROL PANELİ) ---
st.sidebar.markdown("### ⚙️ Audit Configuration")
kdv_oranlari = st.sidebar.multiselect("VAT Rates (KDV)", options=[0.01, 0.10, 0.20], default=[0.20])
tahsilat_esigi = st.sidebar.slider("Receivables Risk Threshold (%)", 10, 90, 40) / 100.0
st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Upload Trial Balance (Mizan)", type=["xlsx", "xls"])

# --- CHART FONKSİYONU ---
def create_pro_chart(df, cat_col, val_col, title, color_scheme):
    chart = alt.Chart(df).mark_arc(innerRadius=75, cornerRadius=8).encode(
        theta=alt.Theta(val_col, stack=True),
        color=alt.Color(cat_col, scale=alt.Scale(range=color_scheme), legend=alt.Legend(orient="bottom", title=None)),
        tooltip=[cat_col, alt.Tooltip(val_col, format=",d")]
    ).properties(title=title, width=280, height=350).configure_title(fontSize=16, color='#1A3755', anchor='start')
    return chart

# --- DENETİM MOTORU ---
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df['Hesap Kodu'] = df['Hesap Kodu'].astype(str)
        
        # Init Variables
        satis, kdv391, alici120, aktif, pasif = 0.0, 0.0, 0.0, 0.0, 0.0
        kasa100, ortak131, kredi, faiz780, ozk = 0.0, 0.0, 0.0, 0.0, 0.0
        donen, duran, kvy, uvy = 0.0, 0.0, 0.0, 0.0
        ters = []

        for i, row in df.iterrows():
            kod, b, a = row['Hesap Kodu'], row.get('Borç Bakiye', 0), row.get('Alacak Bakiye', 0)
            bak = b - a
            if kod.startswith('1'): 
                donen += bak
                aktif += bak if bak > 0 else 0
            elif kod.startswith('2'): 
                duran += bak
                aktif += bak if bak > 0 else 0
            elif kod.startswith('3'): 
                kvy += -bak
                pasif += -bak if -bak > 0 else 0
            elif kod.startswith('4'): 
                uvy += -bak
                pasif += -bak if -bak > 0 else 0
            elif kod.startswith('5'): 
                ozk += -bak
                pasif += -bak if -bak > 0 else 0
            
            if kod.startswith(('1','2')) and bak < 0 and not kod.startswith(('103','257','268')):
                ters.append(kod)
            
            if kod.startswith('600'): satis += a
            if kod.startswith('391'): kdv391 += a
            if kod == '100': kasa100 += bak
            if kod == '131': ortak131 += bak
            if kod.startswith('300'): kredi += a
            if kod == '780': faiz780 += b

        # Key Financial Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Gross Revenue", f"₺ {satis:,.0f}")
        m2.metric("Total Assets", f"₺ {aktif:,.0f}")
        m3.metric("Financial Debt", f"₺ {kredi:,.0f}")
        m4.metric("Total Equity", f"₺ {ozk:,.0f}")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Visual Analytics
        g1, g2 = st.columns(2)
        with g1:
            asset_df = pd.DataFrame({'Category':['Current Assets','Non-Current'], 'Value':[donen, duran]})
            st.altair_chart(create_pro_chart(asset_df, 'Category', 'Value', 'Asset Structure', ['#1A3755','#5D737E']), use_container_width=True)
        with g2:
            source_df = pd.DataFrame({'Category':['ST Liabilities','LT Liabilities','Equity'], 'Value':[kvy, uvy, ozk]})
            st.altair_chart(create_pro_chart(source_df, 'Category', 'Value', 'Capital Structure', ['#2C5F2D','#97BC62','#1A3755']), use_container_width=True)

        # Audit Findings
        st.subheader("📑 Audit Memorandum & Observations")
        
        if satis > 0:
            ef_kdv = kdv391/satis
            if not (min(kdv_oranlari) <= ef_kdv <= max(kdv_oranlari)):
                st.error(f"VAT Compliance: Effective rate (%{ef_kdv*100:.1f}) is outside expected thresholds. Risk of unrecorded revenue.")
        
        if ters:
            st.warning(f"Classification Error: Accounts {', '.join(ters)} show credit balances. Immediate reclassification required.")
            
        if aktif > 0 and (kasa100+ortak131)/aktif > 0.1:
            st.error("Liquidity & Related Party Risk: High concentration in Cash/Shareholder accounts detected.")

    except Exception as e:
        st.error(f"System Error: {e}")
else:
    st.info("System Ready. Please upload a corporate trial balance to begin analysis.")
