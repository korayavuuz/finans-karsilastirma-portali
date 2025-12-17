import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- 1. SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Global Finans Terminali", layout="wide", page_icon="📈")

st.title("📈 Global Varlık Terminali (Dolar Bazlı)")
st.markdown("""
Bu terminal, seçtiğiniz varlıkları **günlük kur üzerinden** USD'ye çevirip 100 baz noktasında karşılaştırır.
""")

# --- 2. YAN MENÜ (INPUTS) ---
st.sidebar.header("Analiz Parametreleri")

# Yahoo Finance Arama Linki (Yan Menüde En Üstte)
st.sidebar.info("🔍 [Buraya tıklayarak hisse kodlarını bulabilirsiniz (Yahoo Finance)](https://finance.yahoo.com/lookup)")

st.sidebar.divider() # Görsel ayırıcı

# 1. Sembol Girişi
ticker_input = st.sidebar.text_input(
    "Sembolleri virgülle girin (Örn: AAPL, THYAO.IS, BTC-USD):", 
    value="AAPL, THYAO.IS, BTC-USD"
)

# Girdiyi temizle
secilen_hisseler = [s.strip().upper() for s in ticker_input.split(",") if s.strip()]

# 2. Tarih Seçimi
start_date = st.sidebar.date_input("Başlangıç Tarihi:", value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("Bitiş Tarihi:", value=pd.to_datetime("today"))

# --- 3. ANA ANALİZ MOTORU ---
if st.sidebar.button("Analizi Başlat"):
    if secilen_hisseler:
        try:
            with st.spinner('Veriler senkronize ediliyor...'):
                # Veri çekme listesini hazırla
                download_list = secilen_hisseler.copy()
                if any(s.endswith(".IS") for s in secilen_hisseler):
                    if "USDTRY=X" not in download_list:
                        download_list.append("USDTRY=X")
                
                # yfinance ile verileri çek
                all_data = yf.download(download_list, start=start_date, end=end_date)['Close']
                
                # Veri temizleme (Tatil günlerini doldur ve boşlukları sil)
                all_data = all_data.ffill().dropna()

                if not all_data.empty:
                    # DataFrame zorlaması
                    if isinstance(all_data, pd.Series):
                        all_data = all_data.to_frame()
                    
                    df_final = all_data.copy()
                    
                    # 🟢 KUR DÖNÜŞTÜRME (GÜNLÜK)
                    if "USDTRY=X" in df_final.columns:
                        kur = df_final["USDTRY=X"]
                        for col in secilen_hisseler:
                            if col.endswith(".IS") and col in df_final.columns:
                                df_final[col] = df_final[col] / kur
                        # Kuru grafikten çıkar
                        df_final = df_final.drop(columns=["USDTRY=X"])
                    
                    # Sadece istenen hisseleri filtrele
                    df_final = df_final[secilen_hisseler]

                    # 🟠 NORMALLEŞTİRME (Başlangıç = 100)
                    normalized = (df_final / df_final.iloc[0] * 100)

                    # --- 4. GÖRSELLEŞTİRME (PLOTLY) ---
                    st.subheader("📊 Dolar Bazlı Performans Gelişimi (Başlangıç=100)")
                    
                    fig = px.line(normalized, 
                                  labels={"value": "Endeks (USD)", "Date": "Tarih"},
                                  template="plotly_white")

                    # Eksen ve Hover (Gezerken Tarih Görme)
                    fig.update_xaxes(
                        dtick="M12",             # Yıllık çizgiler
                        tickformat="%Y",         # Sadece Yıl yazısı
                        hoverformat="%d %m %Y",  # FAREYLE ÜSTÜNE GELİNCE: GÜN AY YIL
                        gridcolor='lightgrey'
                    )
                    
                    fig.update_layout(
                        hovermode="x unified",
                        legend_title_text='Varlıklar',
                        yaxis_title="Dolar Bazlı Değer"
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # --- 5. PERFORMANS ÖZETİ ---
                    st.subheader("📈 Toplam Getiri (%) - USD")
                    
                    perf_values = (normalized.iloc[-1] - 100)
                    # Güvenli DataFrame oluşturma (Hata vermeyen yöntem)
                    perf_df = pd.DataFrame({
                        'Varlık': perf_values.index,
                        'Getiri (%)': perf_values.values
                    }).sort_values(by='Getiri (%)', ascending=False)
                    
                    st.bar_chart(data=perf_df, x='Varlık', y='Getiri (%)')

                else:
                    st.error("Seçilen tarih aralığında veri bulunamadı.")
                    
        except Exception as e:
            st.error(f"Beklenmedik bir hata oluştu: {e}")
    else:
        st.warning("Lütfen en az bir sembol girin.")
else:
    st.info("Analizi başlatmak için yan menüdeki 'Analizi Başlat' butonuna tıklayın.")
