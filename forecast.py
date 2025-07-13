import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from bazaar_api import BazaarAPI
from time_parser import TimeParser

class Forecast:
    def render(self):
        st.header("🔮 Short-Term Forecasting")
        # Auswahl des Items
        item = st.selectbox(
            "Item für Forecast:",
            ["BOOSTER_COOKIE", "RECOMBOBULATOR_3000"],
            key="forecast_item"
        )
        # Auswahl des Zeitraums für historische Daten
        period = st.selectbox(
            "Historischer Zeitraum:",
            ["hour", "day", "week"],
            key="forecast_period"
        )
        # Abruf historischer Verkäufe
        api = BazaarAPI()
        data = api.get_history(item, period)
        if not data:
            st.error("⚠️ Keine historischen Daten verfügbar.")
            return

        # DataFrame vorbereiten
        df_hist = pd.DataFrame({
            'ds': [TimeParser.parse(d['timestamp']) for d in data],
            'y':  [d['sell'] for d in data]
        })
        df_hist['ts'] = df_hist['ds'].map(lambda dt: dt.timestamp())

        # Lineare Regression auf Zeitstempel vs. Preis
        coef, intercept = np.polyfit(df_hist['ts'], df_hist['y'], 1)

        # Forecast-Horizont wählen
        hours = st.slider(
            "Forecast-Horizont (Stunden):", 1, 24, 6, key="forecast_horizon"
        )
        last_time = df_hist['ds'].iloc[-1]
        future_times = [last_time + timedelta(hours=i) for i in range(1, hours + 1)]
        future_ts = np.array([dt.timestamp() for dt in future_times])
        yhat = coef * future_ts + intercept

        # Ergebnis-DF
        df_fc = pd.DataFrame({
            'Zeit': future_times,
            'Vorhersage': yhat
        }).set_index('Zeit')

        # Anzeige: Historie und Forecast in einem Chart
        st.subheader("Historischer Verlauf vs. Forecast")
        chart_df = pd.concat([
            df_hist.set_index('ds')['y'].rename('Historie'),
            df_fc['Vorhersage']
        ])
        st.line_chart(chart_df, height=300)
