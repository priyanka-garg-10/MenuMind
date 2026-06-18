import streamlit as st
from config import APP_NAME, APP_ICON, PRIMARY_COLOR, ACCENT_COLOR
from utils.auth_guard import require_auth, render_sidebar
from api.recommendation_api import run_agent_pipeline
from api.user_api import get_profile
from api.menu_api import create_order

st.set_page_config(
    page_title=f"Recommendations — {APP_NAME}",
    page_icon=APP_ICON,
    layout="wide",
)

token = require_auth()
render_sidebar(active_page="Recommendations")

st.markdown(f"""
<style>
    .rec-hero {{
        background: linear-gradient(135deg, #1A1A2E, #E8491D);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        color: white;
        margin-bottom: 1.5rem;
    }}
    .rec-hero h2 {{ color: white; margin-bottom: 0.3rem; }}
    .rec-hero p  {{ color: rgba(255,255,255,0.8); margin: 0; }}

    .ai-quote {{
        background: #FFFBF0;
        border-left: 4px solid {ACCENT_COLOR};
        border-radius: 0 12px 12px 0;
        padding: 1.2rem 1.5rem;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #333;
        white-space: pre-wrap;
    }}

    .dish-card {{
        background: white;
        border-radius: 12px;
        padding: 1rem 1.3rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }}
    .rank-badge {{
        width: 2.2rem; height: 2.2rem;
        border-radius: 50%;
        background: {PRIMARY_COLOR};
        color: white;
        font-weight: 700;
        font-size: 0.9rem;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }}
    .dish-info {{ flex: 1; }}
    .dish-name  {{ font-weight: 700; color: #1A1A2E; font-size: 1rem; }}
    .dish-meta  {{ font-size: 0.78rem; color: #888; margin-top: 0.2rem; }}
    .health-score {{
        font-size: 1.2rem; font-weight: 700;
        color: {PRIMARY_COLOR}; text-align: right;
    }}
    .hs-label {{ font-size: 0.65rem; color: #aaa; text-align: right; }}

    .warning-box {{
        background: #FFF3CD;
        border: 1px solid #FFC107;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        font-size: 0.88rem;
        color: #856404;
        margin-bottom: 0.5rem;
    }}
    .staff-box {{
        background: #1A1A2E;
        color: #E0E0E0;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        font-family: monospace;
        font-size: 0.88rem;
        line-height: 1.6;
        white-space: pre-wrap;
    }}
    .pipeline-step {{
        display: inline-block;
        background: #F0F0F0;
        border-radius: 20px;
        padding: 0.3rem 0.8rem;
        font-size: 0.75rem;
        color: #555;
        margin: 0.2rem;
    }}
    .pipeline-step.done {{ background: #E8F5E9; color: #2E7D32; }}
</style>
""", unsafe_allow_html=True)

if "profile" not in st.session_state:
    profile_data, status = get_profile(token)
    if status == 200:
        st.session_state["profile"] = profile_data
        st.session_state["user_name"] = profile_data.get("name") or "Guest"

profile   = st.session_state.get("profile", {})
user_name = st.session_state.get("user_name", "Guest")
phone     = profile.get("phone", "")

st.markdown(f"""
<div class="rec-hero">
    <h2>✨ AI Recommendations</h2>
    <p>Personalized for <strong>{user_name}</strong> — powered by 6 AI agents working in sequence.</p>
</div>
""", unsafe_allow_html=True)

if not phone:
    st.error("Could not load your profile. Please visit Dashboard first or try logging in again.")
    st.stop()

col_btn, col_info = st.columns([2, 5])
with col_btn:
    run_clicked = st.button("🚀 Get My Recommendations", type="primary", use_container_width=True)
with col_info:
    if "agent_result" in st.session_state:
        st.caption("✅ Showing latest results. Click the button to refresh with updated data.")
    else:
        st.caption("Click the button to run the full AI pipeline (takes ~5 seconds).")

if run_clicked:
    if not phone:
        st.error("Phone number not found in your profile.")
        st.stop()

    progress_placeholder = st.empty()
    steps = [
        ("🔍", "Customer ID Agent",     "Identifying customer…"),
        ("⚙️", "Preference Agent",      "Loading dietary preferences…"),
        ("🧠", "Memory Agent",          "Fetching order history…"),
        ("🔮", "Recommendation Agent",  "Running RAG search + GPT…"),
        ("💚", "Health Agent",          "Re-ranking by nutrition…"),
        ("🧑‍🍳", "Waiter Copilot",     "Generating staff briefing…"),
    ]

    with progress_placeholder.container():
        st.markdown("**Running AI pipeline…**")
        prog_bar = st.progress(0)
        status_text = st.empty()
        for i, (icon, name, msg) in enumerate(steps):
            status_text.caption(f"{icon} {msg}")
            prog_bar.progress((i + 1) / len(steps))

    with st.spinner("Waiting for AI response…"):
        result, status = run_agent_pipeline(token, phone)

    progress_placeholder.empty()

    if status == 200:
        st.session_state["agent_result"] = result
        st.rerun()
    else:
        err = result.get("detail", "Pipeline failed. Please try again.")
        if result.get("is_new_user"):
            st.warning("You're a new user! Please save your preferences first so the AI can personalize recommendations.")
        else:
            st.error(err)

result = st.session_state.get("agent_result")

if result is None:
    st.info("Your personalized recommendations will appear here after you click the button above.")
    st.stop()

is_new = result.get("is_new_user", False)

if is_new:
    st.warning(
        "👋 You're a new user! The AI pipeline ran but has no preference data to personalize with. "
        "Go to **Profile** to save your diet type, health goals, and favorite cuisines — "
        "then come back for fully personalized recommendations."
    )
    st.stop()

recommendations  = result.get("recommendations", [])
rec_text         = result.get("recommendation_text", "")
health_warnings  = result.get("health_warnings", [])
staff_summary    = result.get("staff_summary", "")
visit_count      = result.get("visit_count", 0)
dietary_filters  = result.get("dietary_filters", {})
current_step     = result.get("current_step", "")

st.markdown("**Pipeline completed:**")
pipeline_labels = ["customer_identified", "preference_enriched",
                   "memory_loaded", "recommendation_done",
                   "health_checked", "waiter_briefing_ready"]
done_set = set()
for label in pipeline_labels:
    if label <= current_step or current_step == "waiter_briefing_ready":
        done_set.add(label)

badges = ""
icons  = ["🔍", "⚙️", "🧠", "🔮", "💚", "🧑‍🍳"]
names  = ["Customer ID", "Preference", "Memory", "Recommendation", "Health", "Waiter Copilot"]
for icon, name in zip(icons, names):
    badges += f'<span class="pipeline-step done">{icon} {name} ✓</span>'
st.markdown(badges, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if rec_text:
    st.markdown("### 🤖 What the AI Recommends")
    st.markdown(f'<div class="ai-quote">{rec_text}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

if recommendations:
    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.markdown("### 🏆 Health-Ranked Dishes")
        st.caption("Re-ranked by nutritional fit to your goals — not just semantic similarity.")

        if "cart" not in st.session_state:
            st.session_state["cart"] = []
        cart_ids = {c["id"] for c in st.session_state["cart"]}

        for rank, item in enumerate(recommendations, 1):
            name         = item.get("name", "Unknown")
            calories     = item.get("calories", "?")
            protein      = item.get("protein_g", "?")
            price        = item.get("price", "?")
            health_score = item.get("health_score", 0.0)
            qdrant_score = item.get("score", 0.0)
            item_id      = item.get("mysql_id")
            is_veg       = item.get("is_veg", True)
            spice        = item.get("spice_level", "?")

            veg_icon = "🟢" if is_veg else "🔴"

            card_col, action_col = st.columns([5, 1])
            with card_col:
                st.markdown(f"""
                <div class="dish-card">
                    <div class="rank-badge">#{rank}</div>
                    <div class="dish-info">
                        <div class="dish-name">{veg_icon} {name}</div>
                        <div class="dish-meta">
                            🔥 {calories} kcal &nbsp;|&nbsp;
                            💪 {protein}g protein &nbsp;|&nbsp;
                            🌶️ {spice} &nbsp;|&nbsp;
                            ₹{price}
                        </div>
                    </div>
                    <div>
                        <div class="health-score">{health_score}</div>
                        <div class="hs-label">health score</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with action_col:
                if item_id:
                    if item_id in cart_ids:
                        if st.button("✅ Added", key=f"rc_{item_id}", use_container_width=True):
                            st.session_state["cart"] = [
                                c for c in st.session_state["cart"] if c["id"] != item_id
                            ]
                            st.rerun()
                    else:
                        if st.button("+ Cart", key=f"ra_{item_id}",
                                     use_container_width=True, type="primary"):
                            st.session_state["cart"].append({
                                "id": item_id, "name": name, "price": price
                            })
                            st.rerun()

    with col_right:
        # Pipeline metadata panel
        st.markdown("### 📊 Pipeline Info")
        st.metric("Visit #", visit_count)
        st.metric("Dishes ranked", len(recommendations))
        if dietary_filters:
            st.markdown("**Filters applied:**")
            for k, v in dietary_filters.items():
                st.markdown(f"- `{k}`: `{v}`")

# ── Health warnings ───────────────────────────────────────────────────────────
st.markdown("### ⚠️ Health Warnings")
if health_warnings:
    for w in health_warnings:
        st.markdown(f'<div class="warning-box">⚠️ {w}</div>', unsafe_allow_html=True)
else:
    st.success("✅ No allergy conflicts or health warnings detected for your profile.")

# ── Staff view (waiter copilot) ───────────────────────────────────────────────
if staff_summary:
    with st.expander("🧑‍🍳 Waiter Briefing (Staff View)", expanded=False):
        st.caption("This is what the AI shows the waiter before they approach your table.")
        st.markdown(f'<div class="staff-box">{staff_summary}</div>', unsafe_allow_html=True)

# ── Cart quick-order ─────────────────────────────────────────────────────────
cart = st.session_state.get("cart", [])
if cart:
    st.markdown("---")
    st.markdown(f"**🛒 {len(cart)} item(s) in cart**")
    if st.button("✅ Place Order", type="primary"):
        item_ids = [c["id"] for c in cart]
        with st.spinner("Placing order…"):
            order_result, order_status = create_order(token, item_ids)
        if order_status == 201:
            st.success(f"🎉 Order placed! {order_result.get('total')} item(s).")
            st.session_state["cart"] = []
            st.balloons()
            st.rerun()
        else:
            st.error(order_result.get("detail", "Order failed."))
