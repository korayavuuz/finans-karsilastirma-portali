import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Global Finans Terminali", layout="wide", page_icon="📈")

st.title("📈 Global Varlık Terminali (Dolar Bazlı)")
st.markdown("""
Bu terminal, seçtiğiniz tüm varlıkları **günlük kur üzerinden** USD'ye çevirip 
100 baz noktasında karşılaştırır.
""")

# --- YAN MENÜ ---
st.sidebar.header("Parametreler")
ticker_input = st.sidebar.text_input(
    "Sembolleri virgülle girin (Örn: AAPL, THYAO.IS, BTC-USD):", 
    value="AAPL, THYAO.IS, BTC-USD"
)

# Girdiyi temizle
secilen_hisseler = [s.strip().upper() for s in ticker_input.split(",") if s.strip()]
start_date = st.sidebar.date_input("Başlangıç:", value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("Bitiş:", value=pd.to_datetime("today"))

if st.sidebar.button("Analizi Başlat"):
    if secilen_hisseler:
        try:
            with st.spinner('Veriler senkronize ediliyor...'):
                # 1. VERİLERİ ÇEK
                # BIST hissesi varsa USDTRY kurunu da listeye ekleyip tek seferde çekiyoruz
                download_list = secilen_hisseler.copy()
                if any(s.endswith(".IS") for s in secilen_hisseler):
                    download_list.append("USDTRY=X")
                
                # yfinance'den verileri çekiyoruz
                all_data = yf.download(download_list, start=start_date, end=end_date)['Close']
                
                # Veri temizleme (Eksik günleri ffill ile doldur, sonra kalan NaN'ları sil)
                all_data = all_data.ffill().dropna()

                if not all_data.empty:
                    # 2. DOLAR ÇEVRİMİ
                    # Eğer sadece bir tane hisse seçildiyse yf.download Series döndürebilir, 
                    # bunu DataFrame'e zorluyoruz.
                    if isinstance(all_data, pd.Series):
                        all_data = all_data.to_frame()
                    
                    df_final = all_data.copy()
                    
                    # Eğer kur verisi çekildiyse, .IS olanları böl
                    if "USDTRY=X" in df_final.columns:
                        kur = df_final["USDTRY=X"]
                        for col in secilen_hisseler:
                            if col.endswith(".IS") and col in df_final.columns:
                                df_final[col] = df_final[col] / kur
                        # Kuru artık grafikte göstermemek için siliyoruz
                        df_final = df_final.drop(columns=["USDTRY=X"])
                    
                    # Sadece kullanıcının istediği hisseleri al (Başka sütun kalmışsa temizle)
                    df_final = df_final[secilen_hisseler]

                    # 3. NORMALLEŞTİRME
                    normalized = (df_final / df_final.iloc[0] * 100)

                    # 4. GRAFİK (PLOTLY)
                    st.subheader("📊 Dolar Bazlı Performans Gelişimi (Başlangıç=100)")
                    fig = px.line(normalized, labels={"value": "Endeks (USD)", "Date": "Tarih"})
                    
                    fig.update_xaxes(
                        dtick="M12", tickformat="%Y", 
                        hoverformat="%d %m %Y", gridcolor='lightgrey'
                    )
                    
                    fig.update_layout(hovermode="x unified", template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)

                    # 5. PERFORMANS ÖZETİ (HATA GİDERİLMİŞ BAR GRAFİĞİ)
                    st.subheader("📈 Toplam Getiri (%) - USD")
                    
                    # Hata veren kısmı daha güvenli hale getirdik:
                    perf_values = (normalized.iloc[-1] - 100)
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
        st.warning("Lütfen sembol girin.")
