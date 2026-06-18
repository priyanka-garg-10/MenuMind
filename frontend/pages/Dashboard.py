import streamlit as st
from config import APP_NAME, APP_ICON, PRIMARY_COLOR, ACCENT_COLOR
from utils.auth_guard import require_auth, render_sidebar
from api.user_api import get_profile, get_preferences, get_order_history

st.set_page_config(
    page_title=f"Dashboard — {APP_NAME}",
    page_icon=APP_ICON,
    layout="wide",
)


token = require_auth()

render_sidebar(active_page="Dashboard")

st.markdown(f"""
<style>
    .metric-card {{
        background: white;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        border-left: 4px solid {PRIMARY_COLOR};
        margin-bottom: 1rem;
    }}
    .metric-label {{ font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }}
    .metric-value {{ font-size: 1.5rem; font-weight: 700; color: #1A1A2E; margin-top: 0.2rem; }}

    .order-item {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid #F0F0F0;
    }}
    .order-name {{ font-weight: 500; color: #1A1A2E; }}
    .order-date {{ font-size: 0.8rem; color: #999; }}

    .pref-tag {{
        display: inline-block;
        background: #FFF3EE;
        color: {PRIMARY_COLOR};
        border: 1px solid {PRIMARY_COLOR};
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.82rem;
        margin: 0.2rem;
    }}
    .allergy-tag {{
        display: inline-block;
        background: #FFF0F0;
        color: #E74C3C;
        border: 1px solid #E74C3C;
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.82rem;
        margin: 0.2rem;
    }}
    .section-card {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        height: 100%;
    }}
    .quick-action {{
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        cursor: pointer;
        transition: transform 0.15s;
    }}
</style>
""", unsafe_allow_html=True)

if "profile" not in st.session_state:
    profile_data, profile_status = get_profile(token)
    if profile_status == 200:
        st.session_state["profile"] = profile_data
        st.session_state["user_name"] = profile_data.get("name") or "Guest"
    else:
        st.session_state["profile"] = {}

if "preferences" not in st.session_state:
    pref_data, pref_status = get_preferences(token)
    st.session_state["preferences"] = pref_data if pref_status == 200 else None

profile = st.session_state.get("profile", {})
prefs   = st.session_state.get("preferences")
user_name = st.session_state.get("user_name", "Guest")

orders, _ = get_order_history(token)

is_new = st.session_state.get("is_new_user", False)

col_title, col_badge = st.columns([3, 1])
with col_title:
    st.markdown(f"## Welcome back, {user_name}! 👋")
    st.caption("Here's your personalized MenuMind dashboard.")
with col_badge:
    if is_new:
        st.info("🆕 New account — complete your profile to unlock AI recommendations!")

st.markdown("---")

m1, m2, m3, m4 = st.columns(4)

visit_count = len(orders)
diet_label  = prefs.get("diet_type", "—").replace("_", " ").title() if prefs else "—"
spice_label = prefs.get("spice_level", "—").title() if prefs else "—"
goals_count = len(prefs.get("health_goals", [])) if prefs else 0

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Orders</div>
        <div class="metric-value">🛍️ {visit_count}</div>
    </div>""", unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Diet Type</div>
        <div class="metric-value">🥗 {diet_label}</div>
    </div>""", unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Spice Level</div>
        <div class="metric-value">🌶️ {spice_label}</div>
    </div>""", unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Health Goals</div>
        <div class="metric-value">🎯 {goals_count} active</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### 🛍️ Recent Orders")

    if not orders:
        st.caption("No orders yet. Browse the menu to get started!")
    else:
        for order in orders[:5]:
            date_str = str(order.get("ordered_at", ""))[:10]
            st.markdown(f"""
            <div class="order-item">
                <span class="order-name">🍽️ {order.get('item_name', 'Unknown')}</span>
                <span class="order-date">{date_str}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ Your Preferences")

    if not prefs:
        st.caption("No preferences saved yet.")
        if st.button("Set up preferences →", type="primary"):
            st.switch_page("pages/Profile.py")
    else:
        # Favourite cuisines as tags
        cuisines = prefs.get("favorite_cuisines") or []
        if cuisines:
            st.caption("**Favourite Cuisines**")
            tags = " ".join(f'<span class="pref-tag">{c}</span>' for c in cuisines)
            st.markdown(tags, unsafe_allow_html=True)

        # Health goals as tags
        goals = prefs.get("health_goals") or []
        if goals:
            st.caption("**Health Goals**")
            tags = " ".join(
                f'<span class="pref-tag">{g.replace("-", " ").title()}</span>'
                for g in goals
            )
            st.markdown(tags, unsafe_allow_html=True)

        # Allergies — highlighted in red
        allergies = prefs.get("allergies") or []
        if allergies:
            st.caption("**⚠️ Allergies**")
            tags = " ".join(
                f'<span class="allergy-tag">⚠ {a}</span>' for a in allergies
            )
            st.markdown(tags, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

st.markdown("#### ⚡ Quick Actions")
qa1, qa2, qa3, qa4 = st.columns(4)

with qa1:
    if st.button("✨  AI Recommendations", use_container_width=True, type="primary"):
        st.switch_page("pages/Recommendations.py")
with qa2:
    if st.button("🔍  Semantic Search", use_container_width=True):
        st.switch_page("pages/Search.py")
with qa3:
    if st.button("📋  Browse Menu", use_container_width=True):
        st.switch_page("pages/Menu.py")
with qa4:
    if st.button("💚  Health Assistant", use_container_width=True):
        st.switch_page("pages/Health_Assistant.py")
