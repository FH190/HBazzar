import streamlit as st

class Settings:
    def render(self):
        st.header("⚙️ Benutzer-Customization & UX")
        theme = st.selectbox("Theme:", ["dark","light"], index=0)
        st.session_state['theme'] = theme
        fav = st.multiselect("Favoriten:",
                             ["BOOSTER_COOKIE","RECOMBOBULATOR_3000"],
                             default=st.session_state.get('favorites', []))
        st.session_state['favorites'] = fav
        st.write("Favoriten:", fav)
