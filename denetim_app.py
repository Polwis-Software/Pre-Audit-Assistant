import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Polwis Software | Pre-Audit Assistant", page_icon="📊", layout="wide")

st.markdown("""

<style>
@import url('');
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

else: st.info("Mizan yükleyin.")
