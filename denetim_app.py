import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Polwis | Financial Audit", page_icon="📈", layout="wide")

# Kurumsal Tema Uygulaması
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F4F7F9; }
    
    /* Üst Bar Tasarımı */
    .main-header {
        background-color: #1A3755;
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
    
    /* Metrik Kartları */
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #E1E4E8;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>Pre-Audit & Internal Control Dashboard</h1><p>Financial Integrity & Risk Analysis Tool</p></div>", unsafe_allow_html=True)
st.sidebar.header("📊 Kontrol Paneli")
kdv_oranlari = st.sidebar.multiselect("KDV Oranları", options=[0.01, 0.10, 0.20], default=[0.20])
tahsilat_esigi = st.sidebar.slider("Risk Eşiği (%)", 10, 90, 40) / 100.0
uploaded_file = st.sidebar.file_uploader("Mizan Dosyası (Excel)", type=["xlsx", "xls"])

def create_pro_chart(df, cat_col, val_col, title, color_scheme):
    chart = alt.Chart(df).mark_arc(innerRadius=70, cornerRadius=10).encode(
        theta=alt.Theta(val_col, stack=True),
        color=alt.Color(cat_col, scale=alt.Scale(range=color_scheme), legend=alt.Legend(orient="bottom")),
        tooltip=[cat_col, val_col]
    ).properties(title=title, width=250, height=350).configure_title(fontSize=18, anchor='middle', color='#1A3755')
    return chart
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
            if kod.startswith('1'): donen += bak; aktif += bak if bak > 0 else 0
            elif kod.startswith('2'): duran += bak; aktif += bak if bak > 0 else 0
            elif kod.startswith('3'): kvy += -bak; pasif += -bak if -bak > 0 else 0
            elif kod.startswith('4'): uvy += -bak; pasif += -bak if -bak > 0 else 0
            elif kod.startswith('5'): ozk += -bak; pasif += -bak if -bak > 0 else 0
            if kod.startswith(('1','2')) and bak < 0 and not kod.startswith(('103','257')): ters.append(kod)
            if kod.startswith('600'): satis += a
            if kod.startswith('391'): kdv391 += a
            if kod == '100': kasa100 += bak
            if kod == '131': ortak131 += bak
            if kod.startswith('300'): kredi += a
            if kod == '780': faiz780 += b

        # Metrikler
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Toplam Ciro", f"{satis:,.0f} ₺")
        m2.metric("Aktif Büyüklük", f"{aktif:,.0f} ₺")
        m3.metric("Finansal Borçlar", f"{kredi:,.0f} ₺")
        m4.metric("Özkaynaklar", f"{ozk:,.0f} ₺")

        # Grafikler
        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1:
            st.altair_chart(create_pro_chart(pd.DataFrame({'K':['Dönen','Duran'],'T':[donen,duran]}),'K','T','Varlık Dağılımı',['#1A3755','#5D737E']), use_container_width=True)
        with g2:
            st.altair_chart(create_pro_chart(pd.DataFrame({'K':['KV','UV','Özk'],'T':[kvy,uvy,ozk]}),'K','T','Kaynak Yapısı',['#2C5F2D','#97BC62','#1A3755']), use_container_width=True)

        st.subheader("📝 Denetim Notları & Bulgular")
        if satis > 0 and not (min(kdv_oranlari) <= (kdv391/satis) <= max(kdv_oranlari)):
            st.error(f"KDV Analizi: Efektif oran (%{(kdv391/satis)*100:.1f}) sektörel ortalamadan sapma gösteriyor.")
        if ters: st.warning(f"Ters Bakiye: {', '.join(ters)} hesapları aktif karakterli olmasına rağmen alacak bakiyesi vermektedir.")
        if aktif > 0 and (kasa100+ortak131)/aktif > 0.1: st.error("Likidite Riski: Kasa ve Ortaklar hesabındaki yoğunlaşma adatlandırma riski taşımaktadır.")

    except Exception as e: st.error(f"Veri Okuma Hatası: {e}")
else: st.info("Lütfen sol menüden kurumsal mizan dosyanızı (Excel) yükleyiniz.")
