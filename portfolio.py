import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from bazaar_api import BazaarAPI

# --- Hilfsfunktion für deutsches Zahlenformat ---
def fmt_de(x, decimals=1):
    """Format x mit Tausenderpunkt und Komma als Dezimaltrennzeichen."""
    s = f"{x:,.{decimals}f}"          # z.B. "1,234,567.8"
    return s.replace(".", "`").replace(",", ".").replace("`", ",")

# --- Datenbank-Setup ---
DB_PATH = 'portfolio.db'
@st.cache_resource
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    # Portfolio-Tabelle
    c.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY,
            item TEXT,
            quantity REAL,
            buy_price REAL,
            timestamp TEXT
        )
    ''')
    # Sales-Tabelle
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY,
            item TEXT,
            quantity REAL,
            sale_price REAL,
            sale_value REAL,
            timestamp TEXT
        )
    ''')
    conn.commit()
    return conn

class Portfolio:
    def __init__(self):
        self.conn = init_db()
        self.api = BazaarAPI()

    def add_transaction(self, item: str, qty: float, price: float):
        ts = datetime.utcnow().isoformat()
        self.conn.execute(
            'INSERT INTO portfolio (item, quantity, buy_price, timestamp) VALUES (?,?,?,?)',
            (item, qty, price, ts)
        )
        self.conn.commit()

    def delete_transaction(self, txn_id: int):
        self.conn.execute('DELETE FROM portfolio WHERE id = ?', (txn_id,))
        self.conn.commit()

    def get_transactions(self) -> pd.DataFrame:
        return pd.read_sql('SELECT * FROM portfolio', self.conn)

    def add_sale(self, item: str, qty: float, price: float):
        ts = datetime.utcnow().isoformat()
        sale_value = qty * price
        self.conn.execute(
            'INSERT INTO sales (item, quantity, sale_price, sale_value, timestamp) VALUES (?,?,?,?,?)',
            (item, qty, price, sale_value, ts)
        )
        self.conn.commit()

    def delete_sale(self, sale_id: int):
        self.conn.execute('DELETE FROM sales WHERE id = ?', (sale_id,))
        self.conn.commit()

    def get_sales_for_today(self) -> pd.DataFrame:
        today = datetime.utcnow().date().isoformat()
        return pd.read_sql(
            """
            SELECT id, item, quantity, sale_price, sale_value, timestamp
            FROM sales
            WHERE date(timestamp)=?
            """,
            self.conn,
            params=(today,),
            parse_dates=['timestamp']
        )

    def render(self):
        st.header("📁 Portfolio & PnL-Tracking")

        # --- Kauf-Formular ---
        with st.form("portfolio_form", clear_on_submit=True):
            cols = st.columns([3, 1, 1, 1])
            item  = cols[0].selectbox("Item:", ["BOOSTER_COOKIE", "RECOMBOBULATOR_3000"], key="port_item")
            qty   = cols[1].number_input(
                        "Menge:",
                        min_value=0.0,
                        value=1.0,
                        step=0.1,
                        format="%.2f",
                        key="port_qty"
                    )
            price = cols[2].number_input("Kaufpreis pro Einheit:", min_value=0.0, value=0.0, key="port_price")
            submitted = cols[3].form_submit_button("Speichern")
        if submitted:
            self.add_transaction(item, qty, price)
            st.success(f"{fmt_de(qty,2)}× {item} @ {fmt_de(price,2)}")

        # --- Aktuelle Positionen ---
        st.subheader("Aktuelle Positionen")
        df = self.get_transactions()
        if df.empty:
            st.info("Keine Transaktionen vorhanden.")
        else:
            df['market_price'] = df['item'].apply(lambda it: self.api.get_history(it)[-1]['buy'])
            df['net_sale_price'] = df['market_price'] * (1 - 0.01125)
            df['PnL_raw'] = df['quantity'] * (df['market_price'] - df['buy_price'])
            df['PnL_tax'] = df['quantity'] * (df['net_sale_price'] - df['buy_price'])

            disp = df.rename(columns={
                'quantity':         'Menge',
                'buy_price':        'Kaufpreis',
                'market_price':     'Marktpreis',
                'net_sale_price':   'Verkaufspreis nach Tax',
                'PnL_raw':          'Gewinn/Verlust (brutto)',
                'PnL_tax':          'Gewinn/Verlust (netto)'
            }).set_index('id')

            # alle numerischen Spalten formatieren
            for col, dec in [
                ('Menge', 2),
                ('Kaufpreis', 1),
                ('Marktpreis', 1),
                ('Verkaufspreis nach Tax', 1),
                ('Gewinn/Verlust (brutto)', 1),
                ('Gewinn/Verlust (netto)', 1),
            ]:
                disp[col] = disp[col].apply(lambda v: fmt_de(v, dec))

            st.dataframe(disp)

            # Multi-Select + Löschen der Käufe
            to_del = st.multiselect(
                "Käufe löschen:",
                options=disp.index.tolist(),
                format_func=lambda x: f"ID {x} – {disp.loc[x,'item']} ×{disp.loc[x,'Menge']}"
            , key="del_purchases")
            if st.button("Ausgewählte Käufe löschen", key="btn_del_pur"):
                for txn_id in to_del:
                    self.delete_transaction(txn_id)
                st.success(f"{len(to_del)} Eintrag(e) gelöscht")
                from streamlit_autorefresh import st_autorefresh
                st_autorefresh(interval=500, limit=1, key="reload_pur")

            total_brutto = df['PnL_raw'].sum()
            total_netto  = df['PnL_tax'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Gesamt-PnL (brutto)", fmt_de(total_brutto,1) + " Coins")
            c2.metric("Gesamt-PnL (netto)",  fmt_de(total_netto,1) + " Coins")

        # --- Verkauf erfassen ---
        st.subheader("Verkauf erfassen")
        df_tx = self.get_transactions()
        if df_tx.empty:
            st.info("Keine Positionen zum Verkaufen vorhanden.")
        else:
            txn_map = df_tx.set_index('id').apply(
                lambda row: f"ID {row.name}: {row['item']} ×{fmt_de(row['quantity'],2)}", axis=1
            ).to_dict()
            sel_id = st.selectbox(
                "Verkaufs-Transaktion auswählen:",
                options=list(txn_map.keys()),
                format_func=lambda x: txn_map[x],
                key="sale_txn"
            )
            tx = df_tx.loc[df_tx['id'] == sel_id].iloc[0]
            default_price = self.api.get_history(tx['item'])[-1]['buy']
            if st.session_state.get("last_sale_txn") != sel_id:
                st.session_state["sale_price"] = default_price
                st.session_state["last_sale_txn"] = sel_id

            s_price = st.number_input(
                "Verkaufspreis pro Einheit:",
                min_value=0.0,
                value=st.session_state["sale_price"],
                step=0.1,
                format="%.2f",
                key="sale_price_input"
            )
            if st.button("Verkaufen", key="sale_btn"):
                final_price = st.session_state["sale_price_input"]
                self.add_sale(tx['item'], tx['quantity'], final_price)
                self.delete_transaction(sel_id)
                st.success(f"ID {sel_id} verkauft: {fmt_de(tx['quantity'],2)}× {tx['item']} @ {fmt_de(final_price,2)}")
                from streamlit_autorefresh import st_autorefresh
                st_autorefresh(interval=500, limit=1, key="reload_sale")

        # --- Tages-Verkäufe anzeigen ---
        today = datetime.utcnow().date().isoformat()
        st.subheader(f"Verkäufe am {today}")
        df_sales = self.get_sales_for_today()
        if df_sales.empty:
            st.info("Heute keine Verkäufe.")
        else:
            df_sales['margin_per_unit'] = df_sales['sale_price'] - (df_sales['sale_value'] / df_sales['quantity'])
            df_sales['profit_net']      = df_sales['sale_value'] * 0.98875 - df_sales['sale_value']

            df_disp = df_sales.rename(columns={
                'item':              'Artikel',
                'quantity':          'Menge',
                'sale_price':        'Preis/Einh.',
                'sale_value':        'Gesamt-Verkaufswert',
                'margin_per_unit':   'Marge/Einh.',
                'profit_net':        'Gewinn/Verlust (netto)'
            }).set_index('id')

            for col, dec in [
                ('Menge', 2),
                ('Preis/Einh.', 1),
                ('Gesamt-Verkaufswert', 1),
                ('Marge/Einh.', 1),
                ('Gewinn/Verlust (netto)', 1),
            ]:
                df_disp[col] = df_disp[col].apply(lambda v: fmt_de(v, dec))

            st.dataframe(df_disp)

            total_sales  = df_sales['sale_value'].sum()
            total_profit = df_sales['profit_net'].sum()
            v1, v2 = st.columns(2)
            v1.metric("Tages-Verkaufswert", fmt_de(total_sales,1) + " Coins")
            v2.metric("Tages-Profit (netto)", fmt_de(total_profit,1) + " Coins")

            to_del_sales = st.multiselect(
                "Verkäufe löschen:",
                options=df_disp.index.tolist(),
                format_func=lambda x: f"ID {x} – {df_disp.loc[x,'Artikel']}"
            , key="del_sales_today")
            if st.button("Ausgewählte Verkäufe löschen", key="btn_del_sales"):
                for sale_id in to_del_sales:
                    self.delete_sale(sale_id)
                st.success(f"{len(to_del_sales)} Verkaufs-Eintrag(e) gelöscht")
                from streamlit_autorefresh import st_autorefresh
                st_autorefresh(interval=500, limit=1, key="reload_sales")
