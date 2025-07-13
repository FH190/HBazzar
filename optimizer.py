import streamlit as st
import pandas as pd
import numpy as np
from bazaar_api import BazaarAPI
from scipy.optimize import minimize

class PortfolioOptimizer:
    def __init__(self):
        self.api = BazaarAPI()

    def render(self):
        st.header("📊 Portfolio-Optimierung & Diversifikation")
        # Lade Portfolio aus Session State oder Datenbank
        try:
            import portfolio
            df_port = portfolio.Portfolio().get_transactions()
        except Exception:
            st.error("Portfolio-Daten nicht verfügbar. Bitte zuerst Transaktionen anlegen.")
            return

        items = df_port['item'].unique().tolist()
        if len(items) < 2:
            st.info("Für Optimierung mindestens zwei verschiedene Items benötigt.")
            return

        # Parameter-Einstellungen
        period = st.selectbox("Historischer Zeitraum für Renditen:", ['day','week'], index=0)
        risk_aversion = st.slider("Risikopräferenz (λ)", 0.0, 1.0, 0.5)

        # Sammlung historischer Preisdaten
        price_hist = {}
        for item in items:
            data = self.api.get_history(item, period)
            prices = [d['sell'] for d in data]
            price_hist[item] = prices
        # Alle Listen auf gleiche Länge kürzen (zuletzt verfügbare Werte)
        min_len = min(len(lst) for lst in price_hist.values())
        for key in price_hist:
            price_hist[key] = price_hist[key][-min_len:]
        df_prices = pd.DataFrame(price_hist)

        # Renditen berechnen
        returns = df_prices.pct_change().dropna()
        mu = returns.mean()              # erwartete Renditen
        cov = returns.cov()              # Kovarianzmatrix

        n = len(items)
        # Zielfunktion: Minimize λ * w.T @ cov @ w - (1-λ) * mu.T @ w
        def objective(w):
            return risk_aversion * np.dot(w.T, np.dot(cov, w)) - (1 - risk_aversion) * np.dot(mu, w)

        # Constraints: sum w = 1, w >= 0
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        bounds = tuple((0,1) for _ in range(n))
        w0 = np.array([1/n]*n)

        result = minimize(objective, w0, method='SLSQP', bounds=bounds, constraints=constraints)
        if not result.success:
            st.error("Optimierung konnte nicht durchgeführt werden.")
            return

        weights = pd.Series(result.x, index=items)
        st.subheader("Empfohlene Allokation")
        st.bar_chart(weights)
        st.write(weights.rename('Gewichte'))

        exp_return = np.dot(mu, result.x)
        exp_vol = np.sqrt(np.dot(result.x.T, np.dot(cov, result.x)))
        st.metric("Erwartete Rendite", f"{exp_return:.2%}")
        st.metric("Portfoliorisiko (Volatilität)", f"{exp_vol:.2%}")
