import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Finansal Karşılaştırma Portalı", layout="wide", page_icon="📈")

st.title("📈 Global Varlık Karşılaştırma Terminali")
st.markdown("""
Bu uygulama, seçtiğiniz hisse senedi, endeks veya kripto paraları **100 baz noktasına** sabitleyerek 
başlangıçtan itibaren kümülatif performanslarını karşılaştırmanızı sağlar.
""")

# --- YAN MENÜ (INPUTS) ---
st.sidebar.header("Analiz Parametreleri")

# Yahoo Finance Ticker Arama Yardımcı Linki
st.sidebar.markdown("[🔍 Hisse/Endeks Kodunu Bul (Yahoo Finance)](https://finance.yahoo.com/lookup)")

# 1. Özelleştirilebilir Hisse Girişi
ticker_input = st.sidebar.text_input(
    "Sembolleri virgülle girin (Örn: AAPL, THYAO.IS, BTC-USD):", 
    value="AAPL, MSFT, THYAO.IS, XU100.IS"
)

# Girdiyi temizleyip listeye çeviriyoruz
secilen_hisseler = [s.strip().upper() for s in ticker_input.split(",") if s.strip()]

# 2. Tarih Seçimi
start_date = st.sidebar.date_input("Başlangıç Tarihi:", value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("Bitiş Tarihi:", value=pd.to_datetime("today"))

# --- ANA EKRAN İŞLEMLERİ ---
if st.sidebar.button("Analizi Çalıştır"):
    if secilen_hisseler:
        try:
            with st.spinner('Veriler çekiliyor...'):
                # Veri Çekme (Sadece Kapanış Fiyatları)
                raw_data = yf.download(secilen_hisseler, start=start_date, end=end_date)['Close']
            
            # Veri Temizleme: NaN değerleri temizlemezsek hesaplamalar bozulur
            data = raw_data.dropna()

            if not data.empty:
                # 1. NORMALLEŞTİRME HESABI
                # Formül: (Mevcut Fiyat / İlk Günün Fiyatı) * 100
                normalized_data = (data / data.iloc[0] * 100)

                # 2. İNTERAKTİF ÇİZGİ GRAFİĞİ (PLOTLY)
                st.subheader("📊 Kümülatif Getiri Gelişimi (Başlangıç=100)")
                
                fig = px.line(normalized_data, 
                              labels={"value": "Normalleştirilmiş Değer", "Date": "Tarih"},
                              template="plotly_white")

                # EKSEN VE HOVER DÜZENLEME
                fig.update_xaxes(
                    dtick="M12",       # Eksen işaretleri her 12 ayda bir (yılda bir)
                    tickformat="%Y",   # Eksen üzerindeki yazılar sadece YIL (2020, 2021...)
                    hoverformat="%d %m %Y", # BURASI DEĞİŞTİ: Gezerken GÜN AY YIL gösterir
                    gridcolor='lightgrey'
                )
                
                fig.update_layout(
                    hovermode="x unified", 
                    legend_title_text='Varlıklar',
                    yaxis_title="Getiri Endeksi"
                )

                st.plotly_chart(fig, use_container_width=True)

                # 3. TOPLAM PERFORMANS BAR GRAFİĞİ (Encoding Hatasız Versiyon)
                st.subheader("📈 Toplam Performans (%)")
                
                # Başlangıçtan sona yüzde değişim hesabı
                toplam_getiri_serisi = (normalized_data.iloc[-1] - 100)
                
                # Veriyi DataFrame'e çeviriyoruz
                perf_df = toplam_getiri_serisi.reset_index()
                perf_df.columns = ['Varlık', 'Getiri (%)']
                perf_df = perf_df.sort_values(by='Getiri (%)', ascending=False)

                # Bar Grafiği Çizimi
                st.bar_chart(data=perf_df, x='Varlık', y='Getiri (%)')

                # Veri Tablosu
                with st.expander("Normalleştirilmiş Ham Verileri İncele"):
                    st.dataframe(normalized_data)

            else:
                st.error("Seçilen semboller veya tarih aralığı için yeterli veri bulunamadı.")
                
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
    else:
        st.warning("Lütfen analiz için en az bir sembol girin.")
else:
    st.info("Soldaki 'Analizi Çalıştır' butonuna basarak kümülatif karşılaştırmayı görebilirsiniz.")