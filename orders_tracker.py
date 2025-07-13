import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from bazaar_api import BazaarAPI
from time_parser import TimeParser

class OrdersLeaderboard:
    def __init__(self):
        self.api = BazaarAPI()

    def render(self):
        st.header("🎖️ Spieler Order Leaderboard (Top 5 Volumen letzter 24 h)")

        # Spieler-IDs eingeben
        raw = st.text_input(
            "Spieler-Namen (Komma-separiert):",
            placeholder="z. B. Spieler1, Spieler2, Spieler3",
            key="orders_players"
        )
        if not raw:
            st.info("Bitte mindestens einen Spielernamen eingeben.")
            return

        players = [p.strip() for p in raw.split(",") if p.strip()]
        cutoff = datetime.now() - timedelta(hours=24)

        volumes = []
        for player in players:
            orders = self.api.get_player_orders(player)
            st.write(f"DEBUG – Rohdaten für {player}:", orders)

            total_vol = 0.0
            for order in orders:
                raw_ts = (
                    order.get("timestamp")
                    or order.get("time")
                    or order.get("createdTimestamp", "")
                )
                try:
                    ts = TimeParser.parse(raw_ts)
                except:
                    continue
                if ts >= cutoff:
                    qty = order.get("quantity", 0)
                    price = order.get("price", order.get("unit_price", 0))
                    total_vol += qty * price

            volumes.append({"player": player, "volume": total_vol})

        if volumes:
            df = pd.DataFrame(volumes).sort_values("volume", ascending=False).head(5)
            df.index = df["player"]
            st.subheader("Top 5 Händler nach Volumen (letzte 24 h)")
            st.bar_chart(df["volume"])
            st.dataframe(df.rename(columns={"volume": "Volumen"}))
        else:
            st.info("Keine Volumen-Daten in den letzten 24 h gefunden.")
