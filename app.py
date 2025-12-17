import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Global Finans Terminali", layout="wide", page_icon="📈")

st.title("📈 Global Varlık Karşılaştırma Terminali (Dolar Bazlı)")
st.markdown("""
Bu terminal, seçtiğiniz tüm varlıkları **Amerikan Doları (USD)** cinsine çevirerek 
kur farkından arındırılmış gerçek performansı karşılaştırır. 
Varlıklar başlangıç tarihinde **100** baz noktasına sabitlenir.
""")

# --- 2. YAN MENÜ (GİRİŞLER) ---
st.sidebar.header("Analiz Parametreleri")
st.sidebar.markdown("[🔍 Ticker Kodlarını Bul (Yahoo Finance)](https://finance.yahoo.com/lookup)")

ticker_input = st.sidebar.text_input(
    "Sembolleri virgülle ayırarak girin (Örn: AAPL, THYAO.IS, BTC-USD):", 
    value="AAPL, MSFT, THYAO.IS, XU100.IS"
)

# Girdiyi temizle ve listeye çevir
secilen_hisseler = [s.strip().upper() for s in ticker_input.split(",") if s.strip()]

# Tarih aralığı seçimi
start_date = st.sidebar.date_input("Başlangıç Tarihi:", value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("Bitiş Tarihi:", value=pd.to_datetime("today"))

# --- 3. ANA ANALİZ MOTORU ---
if st.sidebar.button("Analizi Başlat"):
    if secilen_hisseler:
        try:
            with st.spinner('Veriler ve Kur bilgileri çekiliyor...'):
                # Varlık fiyatlarını çek
                raw_data = yf.download(secilen_hisseler, start=start_date, end=end_date)['Close']
                
                # Eğer tek bir hisse seçilirse Series döner, bunu DataFrame'e çeviriyoruz
                if isinstance(raw_data, pd.Series):
                    raw_data = raw_data.to_frame(name=secilen_hisseler[0])
                
                # BIST (.IS) hissesi var mı kontrol et ve varsa USD/TRY kurunu çek
                bist_hisseleri = [s for s in secilen_hisseler if s.endswith(".IS")]
                if bist_hisseleri:
                    usd_try = yf.download("USDTRY=X", start=start_date, end=end_date)['Close']
            
            # Veri Temizleme: Tüm varlıkların ve kurun olduğu günleri eşle
            # dropna() kullanarak eksik günleri siliyoruz (Senkronizasyon)
            combined_data = raw_data.dropna()
            
            if not combined_data.empty:
                # 🟢 KRİTİK: GÜNLÜK KUR DÖNÜŞTÜRME
                # Her günü kendi tarihindeki USD/TRY kuruyla böler
                if bist_hisseleri:
                    for col in combined_data.columns:
                        if col.endswith(".IS"):
                            # Pandas, index (tarih) üzerinden otomatik eşleştirme yaparak böler
                            combined_data[col] = combined_data[col] / usd_try
                
                # NORMALLEŞTİRME (V1'deki temel mantık)
                # Tüm varlıklar ilk günün fiyatına bölünür ve 100 ile çarpılır
                normalized_data = (combined_data / combined_data.iloc[0] * 100)

                # --- 4. GÖRSELLEŞTİRME (PLOTLY) ---
                st.subheader("📊 Dolar Bazlı Kümülatif Getiri Gelişimi (Başlangıç=100 USD)")
                
                fig = px.line(normalized_data, 
                              labels={"value": "Dolar Bazlı Endeks", "Date": "Tarih"},
                              template="plotly_white")

                # Eksen ve Hover (Gezerken Tarih Görme) Ayarları
                fig.update_xaxes(
                    dtick="M12",             # Eksen çizgilerini yılda bir koy (Sade görünüm)
                    tickformat="%Y",         # Eksen etiketinde sadece YIL yazsın
                    hoverformat="%d %m %Y",  # FAREYLE ÜZERİNE GELİNCE: GÜN AY YIL GÖSTER
                    gridcolor='lightgrey'
                )
                
                fig.update_layout(
                    hovermode="x unified",   # Tüm çizgileri aynı anda göster
                    legend_title_text='Varlıklar',
                    yaxis_title="Normalize Edilmiş Değer (USD)"
                )

                st.plotly_chart(fig, use_container_width=True)

                # --- 5. PERFORMANS ÖZETİ (BAR GRAFİĞİ) ---
                st.subheader("📈 Toplam Getiri (%) - Dolar Bazında")
                
                # Başlangıçtan sona toplam yüzde değişim
                toplam_getiri = (normalized_data.iloc[-1] - 100).reset_index()
                toplam_getiri.columns = ['Varlık', 'Getiri (%)']
                toplam_getiri = toplam_getiri.sort_values(by='Getiri (%)', ascending=False)
                
                # Bar grafiğini tablo üzerinden çiz (Encoding hatasını önler)
                st.bar_chart(data=toplam_getiri, x='Varlık', y='Getiri (%)')

                # Ham Veri Tablosu
                with st.expander("Normalize Edilmiş Ham Verileri İncele (USD)"):
                    st.dataframe(normalized_data)

            else:
                st.error("Seçilen tarih aralığında veriler çakışmıyor veya eksik. Lütfen tarihi değiştirin.")
                
        except Exception as e:
            st.error(f"Beklenmedik bir hata oluştu: {e}")
    else:
        st.warning("Lütfen analiz etmek için en az bir sembol girin.")
else:
    st.info("Analizi başlatmak için sol menüdeki 'Analizi Başlat' butonuna tıklayın.")
