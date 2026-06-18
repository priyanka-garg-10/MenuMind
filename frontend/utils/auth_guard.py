import streamlit as st


def require_auth() -> str:
    """
    Call this as the first line of every protected page.
    """
    token = st.session_state.get("token")
    if not token:
        st.warning("You need to log in first.")
        st.switch_page("pages/Login.py")
        st.stop()
    return token


def get_auth_headers() -> dict:
    """Return the Authorization header dict for requests calls."""
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"}


def logout() -> None:
    """Clear all session state and redirect to Login."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("pages/Login.py")


def render_sidebar(active_page: str = "") -> None:
    """
    Render the custom sidebar navigation.
    Called from every protected page so navigation is consistent.

    We hide Streamlit's auto-generated sidebar nav via CSS and replace
    it with our own so we can control icons, ordering, and active state.
    """
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(f"### 🍽️ MenuMind")
        st.markdown(f"**{st.session_state.get('user_name', 'Guest')}**")
        st.markdown("---")

        pages = [
            ("🏠", "Dashboard",        "pages/Dashboard.py"),
            ("📋", "Menu",             "pages/Menu.py"),
            ("🔍", "Search",           "pages/Search.py"),
            ("✨", "Recommendations",  "pages/Recommendations.py"),
            ("💚", "Health Assistant", "pages/Health_Assistant.py"),
            ("🧑‍🍳", "Waiter Copilot", "pages/Waiter_Copilot.py"),
            ("👤", "Profile",          "pages/Profile.py"),
        ]

        for icon, label, page_path in pages:
            is_active = active_page == label
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{icon}  {label}", use_container_width=True, type=btn_type):
                st.switch_page(page_path)

        st.markdown("---")
        if st.button("🚪  Logout", use_container_width=True):
            logout()
