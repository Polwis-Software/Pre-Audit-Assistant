import streamlit as st
import pandas as pd
import altair as alt

# --- KURUMSAL SAYFA AYARLARI ---
st.set_page_config(page_title="Polwis | Audit Terminal Dark", page_icon="📊", layout="wide")

# --- KOYU TEMA VE OKUNABİLİRLİK (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Arka Planı Koyu Yap */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* Header Tasarımı */
    .main-header {
        background: #1E232E;
        padding: 30px;
        border-radius: 12px;
        border: 1px solid #30363D;
        margin-bottom: 30px;
    }
    
    /* Metrik Kartları (Koyu Gri Üstüne Beyaz Yazı) */
    div[data-testid="stMetric"] {
        background-color: #161B22 !important;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #30363D;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* Metrik Etiketlerini Beyaz Yap */
    [data-testid="stMetricLabel"] {
        color: #8B949E !important;
        font-weight: 600;
    }
    
    /* Metrik Değerlerini Beyaz Yap */
    [data-testid="stMetricValue"] {
        color: #58A6FF !important;
    }

    /* Sidebar Düzeni */
    section[data-testid="stSidebar"] {
        background-color: #0E1117 !important;
        border-right: 1px solid #30363D;
    }
    
    /* Yazı Renklerini Sabitle */
    h1, h2, h3, p, span {
        color: #F0F6FC !important;
    }

    /* Tablo ve Dataframe Okunabilirliği */
    .stDataFrame {
        background-color: #161B22;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class='main-header'>
    <h1 style='margin:0; font-size: 28px; color: #58A6FF !important;'>Polwis Audit Terminal</h1>
    <p style='margin:0; color: #8B949E !important;'>Internal Control & Risk Surveillance Platform</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ Terminal Settings")
kdv_oranlari = st.sidebar.multiselect("VAT Thresholds", options=[0.01, 0.10, 0.20], default=[0.20])
tahsilat_esigi = st.sidebar.slider("Risk Tolerance (%)", 10, 90, 40) / 100.0
st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Secure Data Upload (Excel)", type=["xlsx", "xls"])

# --- CHART FONKSİYONU ---
def create_dark_chart(df, cat_col, val_col, title, colors):
    chart = alt.Chart(df).mark_arc(innerRadius=80, cornerRadius=10).encode(
        theta=alt.Theta(val_col, stack=True),
        color=alt.Color(cat_col, scale=alt.Scale(range=colors), legend=alt.Legend(orient="bottom", labelColor="#C9D1D9")),
        tooltip=[cat_col, alt.Tooltip(val_col, format=",d")]
    ).properties(title=title, width=280, height=350).configure_title(fontSize=16, color='#58A6FF', anchor='middle').configure_view(strokeWidth=0)
    return chart

# --- DENETİM MOTORU ---
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df['Hesap Kodu'] = df['Hesap Kodu'].astype(str)
        
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

        # Metrik Kartları
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Gross Revenue", f"₺ {satis:,.0f}")
        m2.metric("Asset Volume", f"₺ {aktif:,.0f}")
        m3.metric("Financial Debt", f"₺ {kredi:,.0f}")
        m4.metric("Total Equity", f"₺ {ozk:,.0f}")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Grafikler
        g1, g2 = st.columns(2)
        with g1:
            st.altair_chart(create_dark_chart(pd.DataFrame({'C':['Current','Non-Current'], 'V':[donen, duran]}), 'C', 'V', 'Asset Balance', ['#58A6FF','#1F6FEB']), use_container_width=True)
        with g2:
            st.altair_chart(create_dark_chart(pd.DataFrame({'C':['KV','UV','Equity'], 'V':[kvy, uvy, ozk]}), 'C', 'V', 'Source Balance', ['#238636','#2EA043','#58A6FF']), use_container_width=True)

        st.subheader("📝 Audit Notes")
        if satis > 0:
            ef_kdv = kdv391/satis
            if not (min(kdv_oranlari) <= ef_kdv <= max(kdv_oranlari)):
                st.error(f"VAT Alert: Effective rate is %{ef_kdv*100:.1f}. Check for unrecorded sales.")
        if ters:
            st.warning(f"Classification Warning: Accounts {', '.join(ters)} show irregular balances.")
        if aktif > 0 and (kasa100+ortak131)/aktif > 0.1:
            st.error("High Concentration Risk: Large balances in Related Party/Cash accounts.")

    except Exception as e:
        st.error(f"Kernel Error: {e}")
else:
    st.info("System Online. Waiting for encrypted trial balance data...")
