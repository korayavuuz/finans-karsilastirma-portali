import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Finansal Terminal v5.4", layout="wide", page_icon="📈")

st.title("🏛️ Profesyonel Stratejik Analiz Terminali")
st.markdown("""
Bu terminal, varlıkları **Dolar bazına** çevirir ve **bağımsız risk/getiri** analizlerini sunar. 
Tabloda en yüksek getiri ve en düşük risk otomatik olarak vurgulanır.
""")

# --- 2. YAN MENÜ ---
st.sidebar.header("Parametreler")
st.sidebar.info("🔍 [Ticker Kodlarını Bul](https://finance.yahoo.com/lookup)")

ticker_input = st.sidebar.text_input(
    "Sembolleri girin (Örn: AAPL, THYAO.IS, BTC-USD):", 
    value="AAPL, THYAO.IS, BTC-USD, GLD"
)

secilen_hisseler = [s.strip().upper() for s in ticker_input.split(",") if s.strip()]
start_date = st.sidebar.date_input("Başlangıç:", value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("Bitiş:", value=pd.to_datetime("today"))

if st.sidebar.button("Kapsamlı Analizi Başlat"):
    if secilen_hisseler:
        try:
            with st.spinner('Veriler senkronize ediliyor ve kur gürültüsü temizleniyor...'):
                download_list = secilen_hisseler.copy()
                if any(s.endswith(".IS") for s in secilen_hisseler):
                    download_list.append("USDTRY=X")
                
                # Ham veriyi çek (FFILL ile boşlukları doldur, DROPNA yapma ki hisseler birbirini silmesin)
                raw_data = yf.download(download_list, start=start_date, end=end_date)['Close'].ffill()

                if not raw_data.empty:
                    if isinstance(raw_data, pd.Series): raw_data = raw_data.to_frame()
                    
                    # 🟢 KUR DÜZELTMESİ (USD BAZLI)
                    processed_df = pd.DataFrame()
                    if "USDTRY=X" in raw_data.columns:
                        usd_try = raw_data["USDTRY=X"]
                        for col in secilen_hisseler:
                            if col.endswith(".IS") and col in raw_data.columns:
                                processed_df[col] = raw_data[col] / usd_try
                            elif col in raw_data.columns:
                                processed_df[col] = raw_data[col]
                    else:
                        processed_df = raw_data[secilen_hisseler]

                    # 🟠 RİSK VE GETİRİ HESAPLAMA (BAĞIMSIZ MOTOR)
                    # Artık her hisse kendi verisiyle hesaplanır, AAPL sabit kalır.
                    summary_results = []
                    normalized_list = []

                    for col in processed_df.columns:
                        temp_series = processed_df[col].dropna()
                        if not temp_series.empty:
                            # Performans (Getiri)
                            toplam_getiri = (temp_series.iloc[-1] / temp_series.iloc[0] - 1) * 100
                            # Risk (Yıllık Volatilite)
                            yillik_risk = temp_series.pct_change().std() * np.sqrt(252) * 100
                            
                            summary_results.append({
                                'Varlık': col,
                                'Toplam Getiri (%)': toplam_getiri,
                                'Yıllık Risk (%)': yillik_risk
                            })
                            # Grafik için normalleştirme
                            normalized_list.append((temp_series / temp_series.iloc[0] * 100).rename(col))

                    summary_df = pd.DataFrame(summary_results).set_index('Varlık')
                    final_normalized = pd.concat(normalized_list, axis=1).ffill()

                    # --- 3. GÖRSEL ANALİZ ---
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.subheader("📊 Dolar Bazlı Getiri Gelişimi (Base=100)")
                        fig_line = px.line(final_normalized, template="plotly_white")
                        fig_line.update_xaxes(dtick="M12", tickformat="%Y", hoverformat="%d %m %Y")
                        fig_line.update_layout(hovermode="x unified")
                        st.plotly_chart(fig_line, use_container_width=True)

                    with col2:
                        st.subheader("🏆 Getiri Sıralaması (%)")
                        st.bar_chart(summary_df['Toplam Getiri (%)'].sort_values(ascending=False))

                    st.divider()

                    # --- 4. STRATEJİK ÖZET VE BOYAMA ---
                    st.subheader("📝 Stratejik Analiz Özeti")
                    st.markdown("💡 **Yeşil hücreler:** İlgili sütundaki en iyi (En Yüksek Getiri / En Düşük Risk) değeri gösterir.")
                    
                    # BOYAMA MANTIĞI: Getiri için MAX, Risk için MIN
                    styled_df = summary_df.style.highlight_max(subset=['Toplam Getiri (%)'], color='#90ee90') \
                                               .highlight_min(subset=['Yıllık Risk (%)'], color='#90ee90')
                    
                    st.dataframe(styled_df, use_container_width=True)

                    # --- 5. RİSK & KORELASYON ---
                    r_col, c_col = st.columns(2)
                    with r_col:
                        st.subheader("⚡ Risk Profili (Düşük = Güvenli)")
                        st.bar_chart(summary_df['Yıllık Risk (%)'].sort_values())
                    with c_col:
                        st.subheader("🌡️ Korelasyon Isı Haritası")
                        corr = final_normalized.pct_change().corr()
                        st.plotly_chart(px.imshow(corr, text_auto=".2f", color_continuous_scale='RdBu_r', zmin=-1, zmax=1), use_container_width=True)

                else: st.error("Veri bulunamadı.")
        except Exception as e: st.error(f"Hata: {e}")
