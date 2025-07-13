import streamlit as st
from streamlit_autorefresh import st_autorefresh
from bazaar_api import BazaarAPI
from dashboard import Dashboard
from optimizer import PortfolioOptimizer
from orders_tracker import OrdersLeaderboard
from portfolio import Portfolio
from chart_analysis import ChartAnalysis
from forecast import Forecast
from settings import Settings
from recommendations import Recommendations

# Automatische Seitenaktualisierung
st_autorefresh(interval=20 * 1000, limit=None, key="datarefresh")

st.set_page_config(page_title="Bazaar Tracker", layout="wide")

api = BazaarAPI()
pages = {
    "Dashboard": Dashboard(api),
    "Portfolio": Portfolio(),
    "Charts": ChartAnalysis(api),
    "Forecast": Forecast(),
    "Settings": Settings(),
    "Recommendations": Recommendations(),
    "Orders": OrdersLeaderboard(),
    "Optimizer": PortfolioOptimizer(),
}

# unten in main.py, nach dem pages-Dict

# Erzeuge Tabs anhand der Keys
tab_labels = list(pages.keys())
tabs = st.tabs(tab_labels)

# Iteriere synchron über Tabs und die dazugehörigen Page-Objekte
for tab, page_obj in zip(tabs, pages.values()):
    with tab:
        # Falls versehentlich None oder nicht implementiert:
        if page_obj is None:
            st.info("Diese Seite ist noch nicht implementiert.")
        else:
            page_obj.render()
