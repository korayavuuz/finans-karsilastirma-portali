import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. DİL SÖZLÜĞÜ (Dinamik İçerik) ---
translations = {
    "TR": {
        "title": "🏛️ Global Finansal Analiz Terminali",
        "intro": "Bu terminal, varlıkları **Tarihe dayalı Dolar bazına** çevirir ve bağımsız risk/getiri analizlerini sunar.",
        "sidebar_header": "Parametreler",
        "ticker_help": "🔍 [Ticker Kodlarını Bul](https://finance.yahoo.com/lookup)",
        "input_label": "Sembolleri girin (Örn: AAPL, THYAO.IS, BTC-USD):",
        "date_start": "Başlangıç:",
        "date_end": "Bitiş:",
        "btn_analyze": "Analizi Başlat",
        "spinner": "Veriler senkronize ediliyor ve kur gürültüsü temizleniyor...",
        "chart_return": "📊 Dolar Bazlı Getiri Gelişimi (Base=100)",
        "chart_rank": "🏆 Getiri Sıralaması (%)",
        "risk_profile": "⚡ Risk Profili (Düşük = Güvenli)",
        "corr_heat": "🌡️ Korelasyon Isı Haritası",
        "corr_desc": "**Analiz Notu:** Korelasyon, varlıkların birlikte hareket etme eğilimidir. +1.00’a yakın değerler varlıkların aynı yönde hareket ettiğini, 0 bağımsız olduklarını, -1.00 ise ters yönde hareket ederek riski dengelediklerini (Hedge) gösterir.",
        "summary": "📝 Stratejik Analiz Özeti",
        "legend": "💡 **Yeşil hücreler:** İlgili sütundaki en iyi (En Yüksek Getiri / En Düşük Risk) değeri gösterir.",
        "error_data": "Veri bulunamadı.",
        "error_general": "Hata:",
        "col_asset": "Varlık",
        "col_return": "Toplam Getiri (%)",
        "col_risk": "Yıllık Risk (%)"
    },
    "EN": {
        "title": "🏛️ Global Financial Analysis Terminal",
        "intro": "This terminal converts assets using **historical USD rates** and provides independent risk/return analysis.",
        "sidebar_header": "Parameters",
        "ticker_help": "🔍 [Lookup Tickers](https://finance.yahoo.com/lookup)",
        "input_label": "Enter Tickers (e.g., AAPL, THYAO.IS, BTC-USD):",
        "date_start": "Start Date:",
        "date_end": "End Date:",
        "btn_analyze": "Run Analysis",
        "spinner": "Syncing data and cleaning currency noise...",
        "chart_return": "📊 USD-Based Performance (Base=100)",
        "chart_rank": "🏆 Return Ranking (%)",
        "risk_profile": "⚡ Risk Profile (Lower = Safer)",
        "corr_heat": "🌡️ Correlation Heatmap",
        "corr_desc": "**Analysis Note:** Correlation measures asset movement sync. Values near +1.00 mean they move together, 0 means independent, and -1.00 means they move in opposite directions (Hedging).",
        "summary": "📝 Strategic Analysis Summary",
        "legend": "💡 **Green cells:** Show the best value in each column (Highest Return / Lowest Risk).",
        "error_data": "No data found.",
        "error_general": "Error:",
        "col_asset": "Asset",
        "col_return": "Total Return (%)",
        "col_risk": "Annualized Risk (%)"
    }
}

# --- 2. SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Financial Terminal", layout="wide", page_icon="📈")

# Dil Seçimi
lang = st.sidebar.selectbox("🌐 Language / Dil", options=["EN", "TR"])
T = translations[lang]

st.title(T["title"])
st.markdown(T["intro"])

# --- 3. YAN MENÜ ---
st.sidebar.divider()
st.sidebar.header(T["sidebar_header"])
st.sidebar.info(T["ticker_help"])

ticker_input = st.sidebar.text_input(T["input_label"], value="AAPL, THYAO.IS, BTC-USD, GC=F")
secilen_hisseler = [s.strip().upper() for s in ticker_input.split(",") if s.strip()]
start_date = st.sidebar.date_input(T["date_start"], value=pd.to_datetime("2021-01-01"))
end_date = st.sidebar.date_input(T["date_end"], value=pd.to_datetime("today"))

if st.sidebar.button(T["btn_analyze"]):
    if secilen_hisseler:
        try:
            with st.spinner(T["spinner"]):
                download_list = secilen_hisseler.copy()
                if any(s.endswith(".IS") for s in secilen_hisseler):
                    download_list.append("USDTRY=X")
                
                raw_data = yf.download(download_list, start=start_date, end=end_date)['Close'].ffill()

                if not raw_data.empty:
                    if isinstance(raw_data, pd.Series): raw_data = raw_data.to_frame()

                    
                    # 🟢 KUR DÜZELTMESİ
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

                    # 🟠 HESAPLAMALAR
                    summary_results = []
                    normalized_list = []
                    for col in processed_df.columns:
                        temp_series = processed_df[col].dropna()
                        if not temp_series.empty:
                            toplam_getiri = (temp_series.iloc[-1] / temp_series.iloc[0] - 1) * 100
                            yillik_risk = temp_series.pct_change().std() * np.sqrt(252) * 100
                            summary_results.append({T["col_asset"]: col, T["col_return"]: toplam_getiri, T["col_risk"]: yillik_risk})
                            normalized_list.append((temp_series / temp_series.iloc[0] * 100).rename(col))

                    summary_df = pd.DataFrame(summary_results).set_index(T["col_asset"])
                    final_normalized = pd.concat(normalized_list, axis=1).ffill()

                    # --- 4. GÖRSELLEŞTİRME ---
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.subheader(T["chart_return"])
                        fig_line = px.line(final_normalized, template="plotly_dark")
                        st.plotly_chart(fig_line, use_container_width=True)
                    with col2:
                        st.subheader(T["chart_rank"])
                        st.bar_chart(summary_df[T["col_return"]].sort_values(ascending=False))

                    st.divider()

                    r_col, c_col = st.columns(2)
                    with r_col:
                        st.subheader(T["risk_profile"])
                        st.bar_chart(summary_df[T["col_risk"]].sort_values())
                    with c_col:
                        st.subheader(T["corr_heat"])
                        corr = final_normalized.pct_change().corr()
                        st.plotly_chart(px.imshow(corr, text_auto=".2f", color_continuous_scale='RdBu_r'), use_container_width=True)
                        st.info(T["corr_desc"])

                    # --- 5. ÖZET TABLO ---
                    st.subheader(T["summary"])
                    styled_df = summary_df.style.highlight_max(subset=[T["col_return"]], color='#2ecc71').highlight_min(subset=[T["col_risk"]], color='#2ecc71')
                    st.dataframe(styled_df, use_container_width=True)

                else: st.error(T["error_data"])
        except Exception as e: st.error(f"{T['error_general']} {e}")








