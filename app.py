import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- 1. SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Finansal Analiz Terminali v4", layout="wide", page_icon="📊")

st.title("📊 Profesyonel Varlık Analiz Terminali")
st.markdown("""
Bu araç varlıkları **Dolar bazına** çevirir, **normalize** eder ve birbirleriyle olan **korelasyonlarını** hesaplar.
""")

# --- 2. YAN MENÜ ---
st.sidebar.header("Analiz Ayarları")
st.sidebar.info("🔍 [Ticker Kodlarını Bul](https://finance.yahoo.com/lookup)")

ticker_input = st.sidebar.text_input(
    "Sembolleri girin (Virgülle ayırın):", 
    value="V, MA, XOM, CVX, AKBNK.IS, GARAN.IS"
)

secilen_hisseler = [s.strip().upper() for s in ticker_input.split(",") if s.strip()]
start_date = st.sidebar.date_input("Başlangıç:", value=pd.to_datetime("2022-01-01"))
end_date = st.sidebar.date_input("Bitiş:", value=pd.to_datetime("today"))

if st.sidebar.button("Kapsamlı Analizi Başlat"):
    if secilen_hisseler:
        try:
            with st.spinner('Veriler işleniyor...'):
                # Veri Çekme
                download_list = secilen_hisseler.copy()
                if any(s.endswith(".IS") for s in secilen_hisseler):
                    download_list.append("USDTRY=X")
                
                all_data = yf.download(download_list, start=start_date, end=end_date)['Close']
                all_data = all_data.ffill().dropna()

                if not all_data.empty:
                    # Tek hisse kontrolü
                    if isinstance(all_data, pd.Series): all_data = all_data.to_frame()
                    df_final = all_data.copy()
                    
                    # 🟢 KUR DÖNÜŞTÜRME
                    if "USDTRY=X" in df_final.columns:
                        kur = df_final["USDTRY=X"]
                        for col in secilen_hisseler:
                            if col.endswith(".IS") and col in df_final.columns:
                                df_final[col] = df_final[col] / kur
                        df_final = df_final.drop(columns=["USDTRY=X"])
                    
                    df_final = df_final[secilen_hisseler]
                    
                    # 🟠 NORMALLEŞTİRME (Çizgi Grafik İçin)
                    normalized = (df_final / df_final.iloc[0] * 100)

                    # --- 3. GRAFİKLER ---
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.subheader("📈 Kümülatif Getiri (USD)")
                        fig_line = px.line(normalized, template="plotly_white")
                        fig_line.update_xaxes(dtick="M12", tickformat="%Y", hoverformat="%d %m %Y")
                        fig_line.update_layout(hovermode="x unified")
                        st.plotly_chart(fig_line, use_container_width=True)

                    with col2:
                        st.subheader("🏆 Toplam Performans (%)")
                        perf_values = (normalized.iloc[-1] - 100)
                        perf_df = pd.DataFrame({'Varlık': perf_values.index, 'Getiri (%)': perf_values.values}).sort_values('Getiri (%)', ascending=False)
                        st.bar_chart(data=perf_df, x='Varlık', y='Getiri (%)')

                    st.divider()

                    # --- 4. KORELASYON ANALİZİ (YENİ BÖLÜM) ---
                    st.subheader("🌡️ Varlıkların Birbiriyle Uyumu (Korelasyon Matrisi)")
                    st.write("Bu tablo, hisselerin ne kadar benzer hareket ettiğini gösterir. **1.00** tam uyum, **0** alakasızlık demektir.")
                    
                    # Günlük getiriler üzerinden korelasyon hesapla
                    corr_matrix = df_final.pct_change().corr()
                    
                    # Isı Haritası (Heatmap)
                    fig_heat = px.imshow(
                        corr_matrix, 
                        text_auto=".3f", 
                        aspect="auto", 
                        color_continuous_scale='RdBu_r', # Kırmızı (Negatif) - Beyaz (0) - Mavi (Pozitif)
                        zmin=-1, zmax=1
                    )
                    st.plotly_chart(fig_heat, use_container_width=True)

                else:
                    st.error("Veri bulunamadı.")
        except Exception as e:
            st.error(f"Hata: {e}")
    else:
        st.warning("Lütfen sembol girin.")
