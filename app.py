import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Finansal Terminal v5", layout="wide", page_icon="⚖️")

st.title("⚖️ Profesyonel Risk & Getiri Analiz Terminali")
st.markdown("""
Bu sürüm; varlıkları **Dolar bazına** çevirir, **normalize** eder, **korelasyon** ve **yıllık volatilite (risk)** analizlerini sunar.
""")

# --- 2. YAN MENÜ ---
st.sidebar.header("Analiz Ayarları")
st.sidebar.info("🔍 [Ticker Kodlarını Bul](https://finance.yahoo.com/lookup)")

ticker_input = st.sidebar.text_input(
    "Sembolleri girin (Virgülle ayırın):", 
    value="AAPL, THYAO.IS, BTC-USD, GLD"
)

secilen_hisseler = [s.strip().upper() for s in ticker_input.split(",") if s.strip()]
start_date = st.sidebar.date_input("Başlangıç:", value=pd.to_datetime("2022-01-01"))
end_date = st.sidebar.date_input("Bitiş:", value=pd.to_datetime("today"))

if st.sidebar.button("Stratejik Analizi Başlat"):
    if secilen_hisseler:
        try:
            with st.spinner('Veriler işleniyor...'):
                download_list = secilen_hisseler.copy()
                if any(s.endswith(".IS") for s in secilen_hisseler):
                    download_list.append("USDTRY=X")
                
                all_data = yf.download(download_list, start=start_date, end=end_date)['Close']
                all_data = all_data.ffill().dropna()

                if not all_data.empty:
                    if isinstance(all_data, pd.Series): all_data = all_data.to_frame()
                    df_final = all_data.copy()
                    
                    # 🟢 KUR DÖNÜŞTÜRME (USD BAZLI TEMİZLİK)
                    if "USDTRY=X" in df_final.columns:
                        kur = df_final["USDTRY=X"]
                        for col in secilen_hisseler:
                            if col.endswith(".IS") and col in df_final.columns:
                                df_final[col] = df_final[col] / kur
                        df_final = df_final.drop(columns=["USDTRY=X"])
                    
                    df_final = df_final[secilen_hisseler]
                    
                    # Günlük Getiriler (Korelasyon ve Volatilite için)
                    returns = df_final.pct_change().dropna()
                    
                    # 🟠 NORMALLEŞTİRME (Çizgi Grafik)
                    normalized = (df_final / df_final.iloc[0] * 100)

                    # --- 3. GÖRSEL ANALİZ BÖLÜMÜ ---
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.subheader("📊 Kümülatif Performans (Base=100 USD)")
                        fig_line = px.line(normalized, template="plotly_white")
                        fig_line.update_xaxes(dtick="M12", tickformat="%Y", hoverformat="%d %m %Y")
                        fig_line.update_layout(hovermode="x unified")
                        st.plotly_chart(fig_line, use_container_width=True)

                    with col2:
                        st.subheader("📈 Toplam Getiri (%)")
                        perf_values = (normalized.iloc[-1] - 100)
                        perf_df = pd.DataFrame({'Varlık': perf_values.index, 'Getiri (%)': perf_values.values}).sort_values('Getiri (%)', ascending=False)
                        st.bar_chart(data=perf_df, x='Varlık', y='Getiri (%)')

                    st.divider()

                    # --- 4. RİSK & UYUM ANALİZİ ---
                    risk_col, corr_col = st.columns(2)

                    with risk_col:
                        st.subheader("⚡ Yıllık Volatilite (Risk Skoru)")
                        # Yıllık Volatilite Formülü: Günlük Std * Karekök(252 İş Günü)
                        volatility = (returns.std() * np.sqrt(252) * 100).sort_values()
                        vol_df = pd.DataFrame({'Varlık': volatility.index, 'Yıllık Risk (%)': volatility.values})
                        
                        fig_vol = px.bar(vol_df, x='Yıllık Risk (%)', y='Varlık', orientation='h',
                                         title="Düşük Bar = Daha Güvenli/Stabil", color='Yıllık Risk (%)',
                                         color_continuous_scale='Viridis')
                        st.plotly_chart(fig_vol, use_container_width=True)

                    with corr_col:
                        st.subheader("🌡️ Korelasyon Isı Haritası")
                        corr_matrix = returns.corr()
                        fig_heat = px.imshow(corr_matrix, text_auto=".2f", aspect="auto", 
                                            color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
                        st.plotly_chart(fig_heat, use_container_width=True)

                    # --- 5. ÖZET TABLO ---
                    st.subheader("📝 Stratejik Özet Tablosu")
                    summary_df = pd.DataFrame({
                        'Toplam Getiri (%)': perf_values.values,
                        'Yıllık Risk (%)': volatility.values
                    }, index=perf_values.index)
                    st.table(summary_df.sort_values(by='Toplam Getiri (%)', ascending=False))

                else:
                    st.error("Seçilen kriterlerde veri bulunamadı.")
        except Exception as e:
            st.error(f"Sistemsel Hata: {e}")
