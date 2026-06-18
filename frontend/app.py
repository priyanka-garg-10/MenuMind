import streamlit as st
from config import APP_NAME, APP_ICON

# Must be the very first Streamlit call on every page
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

if st.session_state.get("token"):
    st.switch_page("pages/Dashboard.py")
else:
    st.switch_page("pages/Login.py")
