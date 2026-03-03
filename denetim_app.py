import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Polwis Software | Pre-Audit Assistant", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    .stApp { background-color: #F8F9FA; }
    h1 { color: #1A3755; font-weight: 600; }
    div[data-testid="stMetric"] { background-color: #FFFFFF; border-radius: 8px; padding: 15px; border: 1px solid #E9ECEF; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Dijital Pre-Audit & İç Kontrol Asistanı")
st.markdown("Mizanınızı göndermeden önce check-up'tan geçirin.")

st.sidebar.header("Denetim Ayarları")
kdv_oranlari = st.sidebar.multiselect("KDV Oranları", options=[0.01, 0.10, 0.20], default=[0.20])
tahsilat_esigi = st.sidebar.slider("Şüpheli Alacak Eşiği (%)", 10, 90, 40) / 100.0
uploaded_file = st.sidebar.file_uploader("Mizan Yükle", type=["xlsx", "xls"])

def create_donut_chart(df, cat_col, val_col, title, colors):
    chart = alt.Chart(df).mark_arc(innerRadius=80).encode(
        theta=alt.Theta(val_col, stack=True),
        color=alt.Color(cat_col, scale=alt.Scale(range=colors)),
        tooltip=[cat_col, val_col]
    ).properties(title=title, width=300, height=300)
    return chart

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df['Hesap Kodu'] = df['Hesap Kodu'].astype(str)
        
        satis, kdv391, alici120, aktif, pasif = 0.0, 0.0, 0.0, 0.0, 0.0
        kasa100, ortak131, kredi, faiz780, stok153, smm620 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        donen, duran, kvy, uvy, ozk = 0.0, 0.0, 0.0, 0.0, 0.0
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
                ters.append(f"{kod} Ters Bakiye")
            
            if kod.startswith('600'): satis += a
            elif kod.startswith('391'): kdv391 += a
            elif kod.startswith('120'): alici120 += bak
            elif kod == '100': kasa100 += bak
            elif kod == '131': ortak131 += bak
            elif kod.startswith('300'): kredi += a
            elif kod == '780': faiz780 += b
            elif kod == '153': stok153 += bak
            elif kod == '620': smm620 += b

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Satışlar", f"{satis:,.0f}")
        c2.metric("Aktif", f"{aktif:,.0f}")
        c3.metric("Krediler", f"{kredi:,.0f}")
        c4.metric("Özkaynak", f"{ozk:,.0f}")
        
        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1:
            st.altair_chart(create_donut_chart(pd.DataFrame({'K':['Dönen','Duran'],'T':[donen,duran]}),'K','T','Aktif Yapı Dağılımı',['#1E6091','#F58518']), use_container_width=True)
        with g2:
            st.altair_chart(create_donut_chart(pd.DataFrame({'K':['KV Yük.','UV Yük.','Özkaynak'],'T':[kvy,uvy,ozk]}),'K','T','Kaynak Yapı Dağılımı',['#F28E2B','#E15759','#1E6091']), use_container_width=True)

        st.subheader("🚩 Bulgular")
        if satis > 0:
            ef_kdv = kdv391/satis
            if not (min(kdv_oranlari) <= ef_kdv <= max(kdv_oranlari)):
                st.error(f"🚨 KDV Uyumsuzluğu: Efektif oran %{ef_kdv*100:.1f}")
        for t in ters: st.error(f"🚨 {t}")
        if aktif > 0 and (kasa100+ortak131)/aktif > 0.1: st.error("🚨 Yüksek Kasa/Ortak Bakiyesi Riskli")
        if kredi > 0 and faiz780 < kredi*0.01: st.error("🚨 Kredilere Rağmen Eksik Faiz Tahakkuku")
        
    except Exception as e:
        st.error(f"Hata oluştu: {e}")
else:
    st.info("Analiz için lütfen mizan dosyanızı yükleyin.")
