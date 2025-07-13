import streamlit as st
import pandas as pd
import altair as alt
from statistics import mean, stdev

from chartRenderer import ChartRenderer

from bazaar_api import BazaarAPI
from time_parser import TimeParser


class Dashboard:
    def __init__(self, api: BazaarAPI):
        self.api = api
        self.items = [
            "BOOSTER_COOKIE", "RECOMBOBULATOR_3000", "ENCHANTED_SEA_LUMIES",
            "AGATHA_COUPON", "KISMET_FEATHER", "FIGSTONE", "SUMMONING_EYE"
        ]

    def render(self):
        selected = st.multiselect(
            "📦 Wähle Items:", self.items, default=[self.items[0]]
        )
        st.title("📊 Preisverlauf & Marge")
        self._inject_css()

        for i in range(0, len(selected), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(selected):
                    with col:
                        self._render_card(selected[idx])

    def _inject_css(self):
        st.markdown("""
        <style>
          .card {
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            color: #fff;
            margin-bottom: 24px;
          }
          .metrics {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 12px;
            margin: 12px 0;
          }
          .metrics .label { font-size: 0.8em; color: #ccc; }
          .metrics .value { font-size: 1.1em; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

    def _render_card(self, item: str):
        data = self.api.get_history(item)
        if not data:
            st.error(f"⚠️ Keine Daten für {item}")
            return

        times = [TimeParser.parse(d['timestamp']) for d in data]
        buy = [d['buy'] for d in data]
        sell = [d['sell'] for d in data]
        marge = [round(b - s, 1) for b, s in zip(buy, sell)]
        tax = [round(b * 0.98875 - s, 1) for b, s in zip(buy, sell)]
        roi = (tax[-1] / buy[-1] * 100) if buy[-1] else 0
        roi_color = 'lime' if roi >= 10 else 'orange' if roi >= 3 else 'tomato'

        # Prozent-basierte Schwellen mit Ø vorher und Aktuell
        window = tax[-11:-1] if len(tax) >= 11 else []
        avg, sd = (mean(window), stdev(window)) if window else (0, 0)
        curr = tax[-1]
        diff = curr - avg
        pct = (diff / avg * 100) if avg else 0

        warning_html = ''
        if pct > 20:
            warning_html = (
                f"<div style='background:rgba(0,200,0,0.7); padding:8px; border-radius:6px;'>"
                f"<strong>🚀 Massive Steigerung!</strong><br>"
                f"Ø vorher: {avg:,.1f} &nbsp; Aktuell: {curr:,.1f}<br>"
                f"∆: {pct:+.1f}% ({diff:+,.1f} Coins)"
                f"</div>"
            )
        elif pct > 10:
            warning_html = (
                f"<div style='background:rgba(0,128,0,0.6); padding:8px; border-radius:6px;'>"
                f"<strong>📈 Stark gestiegen!</strong><br>"
                f"Ø vorher: {avg:,.1f} &nbsp; Aktuell: {curr:,.1f}<br>"
                f"∆: {pct:+.1f}% ({diff:+,.1f} Coins)"
                f"</div>"
            )
        elif pct < -20:
            warning_html = (
                f"<div style='background:rgba(200,0,0,0.7); padding:8px; border-radius:6px;'>"
                f"<strong>📉 Massiver Einbruch!</strong><br>"
                f"Ø vorher: {avg:,.1f} &nbsp; Aktuell: {curr:,.1f}<br>"
                f"∆: {pct:+.1f}% ({diff:+,.1f} Coins)"
                f"</div>"
            )
        elif pct < -10:
            warning_html = (
                f"<div style='background:rgba(255,80,80,0.6); padding:8px; border-radius:6px;'>"
                f"<strong>⚠️ Stark gefallen!</strong><br>"
                f"Ø vorher: {avg:,.1f} &nbsp; Aktuell: {curr:,.1f}<br>"
                f"∆: {pct:+.1f}% ({diff:+,.1f} Coins)"
                f"</div>"
            )
        elif pct < -5:
            warning_html = (
                f"<div style='background:rgba(255,120,120,0.6); padding:8px; border-radius:6px;'>"
                f"<strong>⚠️ Deutlicher Einbruch!</strong><br>"
                f"Ø vorher: {avg:,.1f} &nbsp; Aktuell: {curr:,.1f}<br>"
                f"∆: {pct:+.1f}% ({diff:+,.1f} Coins)"
                f"</div>"
            )
        else:
            warning_html = (
                f"<div style='background:rgba(255,255,255,0.1); padding:8px; border-radius:6px;'>"
                f"Ø vorher: {avg:,.1f} &nbsp; Aktuell: {curr:,.1f}<br>"
                f"Ξ {pct:+.1f}% ({diff:+,.1f} Coins)<br>"
                f"</div>"
            )


        card_html = f"""
        <div class='card'>
          <h3>📦 {item.replace('_', ' ').title()}</h3>
          {warning_html}
          <div class='metrics'>
            <div><div class='label'>Letzte Abfrage</div><div class='value'>{times[-1].strftime('%H:%M:%S')}</div></div>
            <div><div class='label'>Sell</div><div class='value'>{buy[-1]:,}</div></div>
            <div><div class='label'>Buy</div><div class='value'>{sell[-1]:,}</div></div>
            <div><div class='label'>Marge</div><div class='value'>{marge[-1]:,}</div></div>
            <div><div class='label'>Nach Steuer</div><div class='value'>{tax[-1]:,}</div></div>
            <div><div class='label'>ROI</div><div class='value' style='color:{roi_color};'>{roi:.2f}%</div></div>
          </div>
          <hr>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        chart = ChartRenderer.render_charts(times, sell, buy, marge)
        st.altair_chart(chart, use_container_width=True)