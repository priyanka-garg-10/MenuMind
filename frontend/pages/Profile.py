import streamlit as st
from config import APP_NAME, APP_ICON, PRIMARY_COLOR, ACCENT_COLOR
from utils.auth_guard import require_auth, render_sidebar
from api.user_api import get_profile, get_preferences, save_preferences, get_order_history

st.set_page_config(
    page_title=f"Profile — {APP_NAME}",
    page_icon=APP_ICON,
    layout="wide",
)

token = require_auth()
render_sidebar(active_page="Profile")

st.markdown(f"""
<style>
    .profile-hero {{
        background: linear-gradient(135deg, {PRIMARY_COLOR}18, {ACCENT_COLOR}18);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        display: flex; align-items: center; gap: 1.5rem;
    }}
    .avatar-circle {{
        width: 64px; height: 64px; border-radius: 50%;
        background: {PRIMARY_COLOR};
        color: white; font-size: 1.8rem;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }}
    .profile-name {{ font-size: 1.4rem; font-weight: 700; color: #1A1A2E; }}
    .profile-sub  {{ font-size: 0.85rem; color: #666; margin-top: 0.2rem; }}

    .memory-card {{
        background: #1A1A2E;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        color: #E0E0E0;
        margin-bottom: 1rem;
    }}
    .memory-card h5 {{ color: {ACCENT_COLOR}; margin: 0 0 0.8rem 0; }}
    .memory-row {{ font-size: 0.83rem; margin: 0.4rem 0; }}
    .memory-key {{ color: #aaa; }}

    .hist-item {{
        background: white;
        border-radius: 10px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 5px rgba(0,0,0,0.06);
        display: flex; justify-content: space-between; align-items: center;
        font-size: 0.88rem;
    }}
    .hist-name {{ font-weight: 600; color: #1A1A2E; }}
    .hist-date {{ font-size: 0.75rem; color: #999; }}

    .section-label {{
        font-size: 0.7rem; font-weight: 700; color: #aaa;
        text-transform: uppercase; letter-spacing: 0.08em;
        margin: 1rem 0 0.3rem 0;
    }}
</style>
""", unsafe_allow_html=True)
profile_data, p_status   = get_profile(token)
pref_data,    pref_status = get_preferences(token)

if p_status == 200:
    st.session_state["profile"] = profile_data
    st.session_state["user_name"] = profile_data.get("name") or "Guest"

if pref_status == 200:
    st.session_state["preferences"] = pref_data

profile = profile_data if p_status == 200 else {}
prefs   = pref_data   if pref_status == 200 else {}
name    = profile.get("name") or "Guest"
phone   = profile.get("phone", "")

initial = (name[0].upper()) if name and name != "Guest" else "?"
st.markdown(f"""
<div class="profile-hero">
    <div class="avatar-circle">{initial}</div>
    <div>
        <div class="profile-name">{name}</div>
        <div class="profile-sub">📱 {phone} &nbsp;|&nbsp; MenuMind Member</div>
    </div>
</div>
""", unsafe_allow_html=True)

form_col, info_col = st.columns([3, 2], gap="large")

with form_col:
    st.markdown("### ✏️ Your Preferences")
    st.caption(
        "These preferences power the AI pipeline: dietary filters, health ranking, "
        "and the Waiter Copilot briefing all use this data."
    )

    DIET_OPTIONS    = ["veg", "non-veg", "vegan", "jain", "eggetarian"]
    SPICE_OPTIONS   = ["mild", "medium", "hot", "extra-hot"]
    CUISINE_OPTIONS = [
        "Indian", "Chinese", "Italian", "Thai", "Mexican",
        "Middle Eastern", "Continental", "Japanese", "Korean", "Mediterranean",
    ]
    ALLERGY_OPTIONS = [
        "nuts", "peanuts", "dairy", "gluten", "soy",
        "eggs", "seafood", "shellfish", "lactose",
    ]
    GOAL_OPTIONS = [
        "weight-loss", "high-protein", "low-carb",
        "low-calorie", "heart-healthy", "diabetic-friendly",
    ]

    cur_diet     = prefs.get("diet_type", "veg")
    cur_spice    = prefs.get("spice_level", "medium")
    cur_cuisines = prefs.get("favorite_cuisines", [])
    cur_allergies= prefs.get("allergies", [])
    cur_goals    = prefs.get("health_goals", [])

    cur_goals = [g.replace("_", "-") for g in cur_goals]

    for cv in cur_cuisines:
        if cv not in CUISINE_OPTIONS:
            CUISINE_OPTIONS.append(cv)
    for ca in cur_allergies:
        if ca not in ALLERGY_OPTIONS:
            ALLERGY_OPTIONS.append(ca)
    for cg in cur_goals:
        if cg not in GOAL_OPTIONS:
            GOAL_OPTIONS.append(cg)

    with st.form("preferences_form"):
        st.markdown('<div class="section-label">Basic Preferences</div>', unsafe_allow_html=True)

        col_diet, col_spice = st.columns(2)
        with col_diet:
            diet = st.selectbox(
                "Diet Type",
                options=DIET_OPTIONS,
                index=DIET_OPTIONS.index(cur_diet) if cur_diet in DIET_OPTIONS else 0,
            )
        with col_spice:
            spice = st.selectbox(
                "Spice Level",
                options=SPICE_OPTIONS,
                index=SPICE_OPTIONS.index(cur_spice) if cur_spice in SPICE_OPTIONS else 1,
            )

        st.markdown('<div class="section-label">Cuisines you love</div>', unsafe_allow_html=True)
        cuisines = st.multiselect(
            "Favorite Cuisines",
            options=CUISINE_OPTIONS,
            default=[c for c in cur_cuisines if c in CUISINE_OPTIONS],
            label_visibility="collapsed",
        )

        st.markdown('<div class="section-label">Allergies & Intolerances</div>', unsafe_allow_html=True)
        allergies = st.multiselect(
            "Allergies",
            options=ALLERGY_OPTIONS,
            default=[a for a in cur_allergies if a in ALLERGY_OPTIONS],
            label_visibility="collapsed",
            help="These trigger health warnings in the AI pipeline and Waiter Copilot.",
        )

        st.markdown('<div class="section-label">Health Goals</div>', unsafe_allow_html=True)
        goals = st.multiselect(
            "Health Goals",
            options=GOAL_OPTIONS,
            default=[g for g in cur_goals if g in GOAL_OPTIONS],
            label_visibility="collapsed",
            help="Goals influence how the health_agent re-ranks recommendations.",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # st.form_submit_button() is the only allowed submit trigger inside a form.
        # When clicked, Streamlit reruns the script with the form widget values
        # available in their variables (diet, spice, cuisines, allergies, goals).
        submitted = st.form_submit_button(
            "💾 Save Preferences",
            type="primary",
            use_container_width=True,
        )
    if submitted:
        payload = {
            "diet_type":          diet,
            "spice_level":        spice,
            "favorite_cuisines":  cuisines,
            "allergies":          allergies,
            "health_goals":       goals,
        }
        result, status = save_preferences(token, payload)
        if status == 200:
            # Bust the cached preferences so the rest of the app sees fresh data
            st.session_state["preferences"] = result
            st.success("✅ Preferences saved! The AI pipeline will use these on your next recommendation run.")
        else:
            err = result.get("detail", "Failed to save.")
            st.error(f"❌ {err}")

with info_col:

    st.markdown("### 🧠 What the AI Knows About You")
    st.caption("This is the data that flows into the 6-agent pipeline on every recommendation run.")

    diet_display    = prefs.get("diet_type", "Not set")
    spice_display   = prefs.get("spice_level", "Not set")
    cuisine_display = ", ".join(prefs.get("favorite_cuisines") or []) or "None saved"
    allergy_display = ", ".join(prefs.get("allergies") or []) or "None"
    goal_display    = ", ".join(prefs.get("health_goals") or []) or "None"

    st.markdown(f"""
    <div class="memory-card">
        <h5>🤖 AI Memory Snapshot</h5>
        <div class="memory-row"><span class="memory-key">Diet type &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span> {diet_display}</div>
        <div class="memory-row"><span class="memory-key">Spice level &nbsp;&nbsp;&nbsp;</span> {spice_display}</div>
        <div class="memory-row"><span class="memory-key">Cuisines &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span> {cuisine_display}</div>
        <div class="memory-row"><span class="memory-key">Allergies &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span> {allergy_display}</div>
        <div class="memory-row"><span class="memory-key">Health goals &nbsp;&nbsp;</span> {goal_display}</div>
    </div>
    """, unsafe_allow_html=True)

    st.caption(
        "**How this flows:** "
        "`preference_agent` converts diet type → Qdrant `is_veg` filter. "
        "Health goals → `health_agent` scoring weights. "
        "Allergies → `health_warnings` in Waiter Copilot."
    )

    st.markdown("---")

    st.markdown("### 📦 Your Order History")

    orders, o_status = get_order_history(token)

    if o_status != 200 or not orders:
        st.info("No orders yet. Visit the Menu or Search page to place your first order.")
    else:
        st.caption(f"Showing last {len(orders)} order(s).")
        for order in orders:
            item_name  = order.get("item_name") or order.get("name") or "—"
            price      = order.get("price", "?")
            ordered_at = order.get("ordered_at") or order.get("created_at", "")

            date_str = ""
            if ordered_at:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(str(ordered_at).replace("Z", "+00:00"))
                    date_str = dt.strftime("%b %d, %Y")
                except Exception:
                    date_str = str(ordered_at)[:10]

            st.markdown(f"""
            <div class="hist-item">
                <div>
                    <div class="hist-name">🍽️ {item_name}</div>
                    <div class="hist-date">{date_str}</div>
                </div>
                <div style="font-weight:700; color:#1A1A2E">₹{price}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("⚙️ Account Actions", expanded=False):
        st.caption("Session management.")
        if st.button("🚪 Log Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("pages/Login.py")
