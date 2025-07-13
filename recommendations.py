import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from bazaar_api import BazaarAPI
from time_parser import TimeParser

class Recommendations:
    def render(self):
        st.header("💡 Automatisierte Empfehlungen")
        # Auswahl des Items
        item = st.selectbox(
            "Item:",
            ["BOOSTER_COOKIE", "RECOMBOBULATOR_3000"],
            key="rec_item"
        )
        # Auswahl des Zeitraums
        period = st.selectbox(
            "Zeitraum:",
            ["hour", "day", "week"],
            key="rec_period"
        )
        # Historische Daten abrufen
        data = BazaarAPI().get_history(item, period)
        if not data:
            st.error("⚠️ Keine Daten verfügbar.")
            return

        # Preise und Zeit indexieren
        times = [TimeParser.parse(d['timestamp']) for d in data]
        prices = pd.Series([d['sell'] for d in data], index=times)
        latest = prices.iloc[-1]
        low    = prices.quantile(0.05)
        high   = prices.quantile(0.95)
        avg    = prices.mean()

        # Grundempfehlung basierend auf Quantilen
        if latest <= low:
            action = "Kaufen"
            detail = (
                f"Preis von {latest:,.1f} liegt in den unteren 5 % der letzten Werte – günstiger Einstieg."
                f"\nDurchschnittlicher Preis (Referenz): {avg:,.1f} Coins"
            )
        elif latest >= high:
            action = "Verkaufen"
            detail = (
                f"Preis von {latest:,.1f} liegt in den oberen 5 % der letzten Werte – Gewinne realisieren."
                f"\nDurchschnittlicher Preis (Referenz): {avg:,.1f} Coins"
            )
            # Abschätzung des nächsten Verkaufszeitpunkts
            ts_nums = np.array([dt.timestamp() for dt in times])
            slope, intercept = np.polyfit(ts_nums, prices.values, 1)
            if slope > 0:
                t_target = (high - intercept) / slope
                dt_target = datetime.fromtimestamp(t_target)
                detail += f"\nErwarteter Verkaufszeitpunkt: {dt_target.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                detail += "\nKein steigender Trend – weiter beobachten empfohlen."
        else:
            action = "Beobachten"
            detail = (
                f"Preis von {latest:,.1f} ist durchschnittlich – Entscheidungen für klare Trends aufheben."
                f"\nDurchschnittlicher Preis (Referenz): {avg:,.1f} Coins"
            )

        # Ausgabe der Empfehlung und Details
        st.markdown(f"**Empfehlung:** {action}")
        st.write(detail)
        st.write(f"Aktueller Preis: {latest:,.1f} Coins")
