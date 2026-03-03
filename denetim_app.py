import streamlit as st
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Pre-Audit Asistanı", page_icon="📊", layout="wide")

st.title("📊 Dijital İç Kontrol ve Pre-Audit Asistanı")
st.markdown("Mizanınızı dış denetçiye veya yatırımcıya göndermeden önce saniyeler içinde check-up'tan geçirin. **Verileriniz sunucuda tutulmaz, analiz sonrası anında silinir.**")

# --- YAN PANEL (KULLANICI GİRDİLERİ) ---
st.sidebar.header("Denetim Parametreleri")
st.sidebar.markdown("Şirketinizin dinamiklerine göre risk eşiklerini belirleyin.")

kdv_oranlari = st.sidebar.multiselect(
    "Geçerli KDV Oranlarınız",
    options=[0.01, 0.10, 0.20],
    default=[0.20],
    format_func=lambda x: f"%{int(x*100)}"
)

tahsilat_esigi = st.sidebar.slider(
    "Şüpheli Alacak Risk Eşiği (%)", 
    min_value=10, max_value=90, value=40, step=5
) / 100.0

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Mizan Yükle (Excel)", type=["xlsx", "xls"])

# --- ANA DENETİM MOTORU ---
if uploaded_file is not None:
    st.info("Mizan başarıyla belleğe alındı. Denetim kuralları çalıştırılıyor...")
    
    try:
        df = pd.read_excel(uploaded_file)
        df['Hesap Kodu'] = df['Hesap Kodu'].astype(str)
        
        # Değişkenler
        brut_satislar = 0.0
        hesaplanan_kdv_391 = 0.0
        alici_bakiyesi_120 = 0.0
        aktif_toplami = 0.0
        kasa_100 = 0.0
        ortak_alacak_131 = 0.0
        kredi_300_400 = 0.0
        faiz_gideri_780 = 0.0
        stok_153 = 0.0
        maliyet_620 = 0.0
        
        ters_bakiye_hatalari = []

        # Mizanı Tarama
        for index, row in df.iterrows():
            kod = row['Hesap Kodu']
            borc = row.get('Borç Bakiye', 0)
            alacak = row.get('Alacak Bakiye', 0)
            
            # Aktif Toplamı (1 ve 2 ile başlayan hesapların borç kalıntısı)
            if kod.startswith(('1', '2')):
                aktif_toplami += (borc - alacak) if (borc - alacak) > 0 else 0
                
                # Ters Bakiye Kontrolü (1 ve 2 nolu hesaplar alacak kalıntısı veremez, istisnalar hariç)
                if (alacak - borc) > 0 and not kod.startswith(('103', '119', '121', '122', '129', '137', '139', '158', '199', '257', '268')):
                    ters_bakiye_hatalari.append(f"{kod} nolu hesap ters bakiye veriyor!")
            
            # Hesap Bazlı Toplamalar
            if kod.startswith(('600', '601', '602')): brut_satislar += alacak
            elif kod.startswith('391'): hesaplanan_kdv_391 += alacak
            elif kod.startswith('120'): alici_bakiyesi_120 += (borc - alacak)
            elif kod == '100': kasa_100 += (borc - alacak)
            elif kod == '131': ortak_alacak_131 += (borc - alacak)
            elif kod.startswith(('300', '303', '400')): kredi_300_400 += alacak
            elif kod == '780': faiz_gideri_780 += borc
            elif kod.startswith('153'): stok_153 += (borc - alacak)
            elif kod == '620': maliyet_620 += borc

        # --- RİSK ANALİZ SONUÇLARI ---
        st.subheader("Finansal Röntgen")
        col1, col2, col3 = st.columns(3)
        col1.metric("Brüt Satışlar", f"{brut_satislar:,.0f} TL")
        col2.metric("Aktif Büyüklük", f"{aktif_toplami:,.0f} TL")
        col3.metric("Banka Kredileri", f"{kredi_300_400:,.0f} TL")

        st.markdown("---")
        st.subheader("🚩 Denetim Bulguları")
        
        kirmizi_bayraklar = []
        sari_bayraklar = []
        
        # 1. KDV Testi
        if brut_satislar > 0 and kdv_oranlari:
            efektif_kdv = hesaplanan_kdv_391 / brut_satislar
            if not (min(kdv_oranlari) <= efektif_kdv <= max(kdv_oranlari)):
                kirmizi_bayraklar.append(f"**KDV Uyumsuzluğu:** Efektif KDV %{efektif_kdv*100:.1f} çıktı. Beyan edilen oranlarla eşleşmiyor. Kayıtdışı satış riski.")
        
        # 2. Ters Bakiye Testi
        if ters_bakiye_hatalari:
            for hata in ters_bakiye_hatalari:
                kirmizi_bayraklar.append(f"**Muhasebe Hatası:** {hata} (Yanlış sınıflandırma veya makyajlama riski)")

        # 3. Kasa/Ortak Sifonlama Testi
        if aktif_toplami > 0:
            sifon_orani = (kasa_100 + ortak_alacak_131) / aktif_toplami
            if sifon_orani > 0.10:
                kirmizi_bayraklar.append(f"**İç Boşaltma Riski:** Varlıkların %{sifon_orani*100:.1f}'i Kasada (100) veya Ortakta (131). Fiktif bakiye veya adatlandırma cezası riski yüksek.")

        # 4. Kredi / Faiz Testi
        if kredi_300_400 > 0 and faiz_gideri_780 < (kredi_300_400 * 0.01):
            kirmizi_bayraklar.append("**Tahakkuk Hatası:** Yüksek banka kredisine rağmen Finansman Gideri (780) eksik. Kâr suni olarak şişirilmiş.")

        # 5. Şüpheli Alacak Testi
        if brut_satislar > 0:
            tahsilat_riski = alici_bakiyesi_120 / brut_satislar
            if tahsilat_riski > tahsilat_esigi:
                sari_bayraklar.append(f"**Nakit Dönüşüm Riski:** Satışların %{tahsilat_riski*100:.1f}'i 120 Alıcılar hesabında bekliyor. Şüpheli alacak potansiyeli.")

        # 6. Stok Testi
        if maliyet_620 > 0:
            stok_orani = stok_153 / maliyet_620
            if stok_orani > 1.5:
                sari_bayraklar.append(f"**Stok Şişkinliği:** Eldeki stoklar, yıllık maliyetin {stok_orani:.1f} katı. Satılamayan çöp stok veya maliyet gizleme riski.")

        # Çıktıları Ekrana Bas
        if kirmizi_bayraklar:
            for bayrak in kirmizi_bayraklar:
                st.error(bayrak, icon="🚨")
        
        if sari_bayraklar:
            for bayrak in sari_bayraklar:
                st.warning(bayrak, icon="⚠️")
                
        if not kirmizi_bayraklar and not sari_bayraklar:
            st.success("Tebrikler! Mizanınız belirlediğimiz majör risk filtrelerinden başarıyla geçti.", icon="✅")

    except Exception as e:
        st.error(f"Dosya işlenirken bir hata oluştu. Lütfen Excel formatını kontrol edin. Hata detayı: {e}")
else:
    st.info("👈 Lütfen sol panelden şirketinize ait mizanı yükleyin. (İlk sütun 'Hesap Kodu', diğerleri 'Borç Bakiye' ve 'Alacak Bakiye' olmalıdır)")