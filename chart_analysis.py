import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from time_parser import TimeParser
from bazaar_api import BazaarAPI

class ChartAnalysis:
    def __init__(self, api: BazaarAPI):
        self.api = api

    @staticmethod
    def _bollinger(series: pd.Series, window:int=20, k:int=2):
        ma = series.rolling(window).mean()
        sd = series.rolling(window).std()
        return ma, ma+k*sd, ma-k*sd

    def render(self):
        st.header("📈 Erweiterte Chart-Analyse")
        item = st.selectbox("Item für Chart:", ["BOOSTER_COOKIE","RECOMBOBULATOR_3000"])
        period = st.selectbox("Zeitraum:", ["hour","day","week"])
        data = self.api.get_history(item, period)
        if not data:
            st.error("Keine Daten verfügbar.")
            return
        df = pd.DataFrame({
            'time': [TimeParser.parse(d['timestamp']) for d in data],
            'price': [d['sell'] for d in data]
        })
        ma, ub, lb = ChartAnalysis._bollinger(df['price'])
        fig, ax = plt.subplots(figsize=(8,4))
        ax.plot(df['time'], df['price'], label='Preis')
        ax.plot(df['time'], ma, label='GD')
        ax.plot(df['time'], ub, label='GD+2σ', linestyle='--')
        ax.plot(df['time'], lb, label='GD-2σ', linestyle='--')
        ax.legend(); ax.grid(True)
        st.pyplot(fig)
