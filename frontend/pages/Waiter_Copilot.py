import streamlit as st
from config import APP_NAME, APP_ICON, PRIMARY_COLOR
from utils.auth_guard import require_auth, render_sidebar
from api.recommendation_api import run_agent_pipeline

st.set_page_config(
    page_title=f"Waiter Copilot — {APP_NAME}",
    page_icon=APP_ICON,
    layout="wide",
)

token = require_auth()
render_sidebar(active_page="Waiter Copilot")

st.markdown(f"""
<style>
    .waiter-header {{
        background: linear-gradient(135deg, #1A1A2E, #2C3E50);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        color: white;
        margin-bottom: 1.5rem;
    }}
    .waiter-header h3 {{ color: white; margin: 0 0 0.3rem 0; }}
    .waiter-header p  {{ color: rgba(255,255,255,0.7); margin: 0; }}

    .customer-banner {{
        background: #F8F9FA;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        border-left: 5px solid {PRIMARY_COLOR};
        margin-bottom: 1rem;
    }}
    .customer-name {{ font-size: 1.4rem; font-weight: 700; color: #1A1A2E; }}
    .customer-sub  {{ font-size: 0.85rem; color: #666; margin-top: 0.2rem; }}

    .alert-critical {{
        background: #FFEBEE;
        border: 2px solid #E53935;
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        color: #B71C1C;
        font-weight: 700;
        font-size: 0.92rem;
        margin-bottom: 0.6rem;
    }}
    .alert-warning {{
        background: #FFF8E1;
        border: 1px solid #FFC107;
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        color: #856404;
        font-size: 0.88rem;
        margin-bottom: 0.5rem;
    }}

    .staff-brief {{
        background: #1A1A2E;
        color: #E0E0E0;
        border-radius: 12px;
        padding: 1.4rem 1.8rem;
        font-family: monospace;
        font-size: 0.88rem;
        line-height: 1.7;
        white-space: pre-wrap;
    }}

    .pref-tag {{
        display: inline-block;
        border-radius: 12px;
        padding: 0.25rem 0.75rem;
        font-size: 0.78rem;
        margin: 0.2rem;
        font-weight: 600;
    }}
    .pref-diet   {{ background: #E8F5E9; color: #2E7D32; }}
    .pref-spice  {{ background: #FFF3E0; color: #E65100; }}
    .pref-cuisine{{ background: #E3F2FD; color: #1565C0; }}
    .pref-goal   {{ background: #F3E5F5; color: #6A1B9A; }}
    .pref-allergy{{ background: #FFEBEE; color: #C62828; }}

    .rec-row {{
        background: white;
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.07);
        display: flex; gap: 1rem; align-items: center;
    }}
    .rec-rank {{
        width: 2rem; height: 2rem; border-radius: 50%;
        background: {PRIMARY_COLOR}; color: white;
        font-weight: 700; font-size: 0.85rem;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }}
    .rec-name {{ font-weight: 700; color: #1A1A2E; font-size: 0.95rem; }}
    .rec-meta {{ font-size: 0.76rem; color: #888; margin-top: 0.2rem; }}
    .rec-hs   {{
        font-size: 1.1rem; font-weight: 700; color: {PRIMARY_COLOR};
        text-align: right; min-width: 3rem;
    }}
    .hs-lbl {{ font-size: 0.62rem; color: #aaa; text-align: right; }}

    .hist-row {{
        background: white;
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 5px rgba(0,0,0,0.06);
        font-size: 0.88rem;
        display: flex; justify-content: space-between; align-items: center;
    }}
    .hist-name {{ font-weight: 600; color: #1A1A2E; }}
    .hist-meta {{ font-size: 0.76rem; color: #888; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="waiter-header">
    <h3>🧑‍🍳 Waiter Copilot</h3>
    <p>Look up any customer by phone number to get their AI-generated briefing before approaching the table.</p>
</div>
""", unsafe_allow_html=True)

col_phone, col_btn, col_clear = st.columns([4, 1, 1])
with col_phone:
    phone_input = st.text_input(
        "Customer Phone",
        placeholder="e.g. 9876543210",
        label_visibility="collapsed",
        key="waiter_phone_input",
    )
with col_btn:
    lookup_clicked = st.button("🔍 Look Up", type="primary", use_container_width=True)
with col_clear:
    if st.button("✖ Clear", use_container_width=True):
        st.session_state.pop("waiter_result", None)
        st.session_state.pop("waiter_lookup_phone", None)
        st.rerun()

st.markdown("---")

if lookup_clicked and phone_input.strip():
    phone = phone_input.strip()
    with st.spinner(f"Running AI pipeline for {phone}…"):
        result, status = run_agent_pipeline(token, phone)
    if status == 200:
        st.session_state["waiter_result"] = result
        st.session_state["waiter_lookup_phone"] = phone
        st.rerun()
    else:
        err = result.get("detail", "Pipeline failed.")
        st.error(f"❌ {err}")

elif lookup_clicked and not phone_input.strip():
    st.warning("Please enter a customer phone number.")

result = st.session_state.get("waiter_result")

if result is None:
    st.info("Enter a customer's phone number above and click **Look Up** to pull their AI briefing.")
    st.stop()

# Extract state fields
customer_name   = result.get("user_name") or "Unknown Customer"
is_new          = result.get("is_new_user", False)
visit_count     = result.get("visit_count", 0)
preferences     = result.get("preferences") or {}
health_goals    = result.get("health_goals", [])
dietary_filters = result.get("dietary_filters", {})
recommendations = result.get("recommendations", [])
rec_text        = result.get("recommendation_text", "")
health_warnings = result.get("health_warnings", [])
staff_summary   = result.get("staff_summary", "")
order_history   = result.get("order_history", [])
lookup_phone    = st.session_state.get("waiter_lookup_phone", "")

repeat = "Repeat customer" if visit_count > 1 else "First visit"
st.markdown(f"""
<div class="customer-banner">
    <div class="customer-name">{'👋 New Customer' if is_new else f'👤 {customer_name}'}</div>
    <div class="customer-sub">
        📱 {lookup_phone} &nbsp;|&nbsp;
        🍽️ Visit #{visit_count} &nbsp;|&nbsp;
        {'🆕 No order history' if visit_count == 0 else f'🔄 {repeat}'}
    </div>
</div>
""", unsafe_allow_html=True)
allergies = preferences.get("allergies", [])
if allergies:
    for a in allergies:
        st.markdown(f'<div class="alert-critical">🚨 ALLERGY ALERT: {a.upper()}</div>', unsafe_allow_html=True)

if health_warnings:
    for w in health_warnings:
        st.markdown(f'<div class="alert-warning">⚠️ {w}</div>', unsafe_allow_html=True)

if not allergies and not health_warnings:
    st.success("✅ No allergy alerts. No health warnings for this customer.")

st.markdown("<br>", unsafe_allow_html=True)

tab_overview, tab_recs, tab_history = st.tabs([
    "📋 Overview",
    f"🏆 Recommendations ({len(recommendations)})",
    f"📦 Order History ({len(order_history)})",
])

with tab_overview:
    col_brief, col_pref = st.columns([3, 2])

    with col_brief:
        st.markdown("#### 🤖 AI Staff Briefing")
        st.caption("Generated by the Waiter Copilot node (GPT, temperature 0.4 for consistency)")
        if staff_summary:
            st.markdown(f'<div class="staff-brief">{staff_summary}</div>', unsafe_allow_html=True)
        else:
            st.info("No staff briefing available (new customer or pipeline incomplete).")

    with col_pref:
        st.markdown("#### 🔖 Customer Preferences")

        if is_new or not preferences:
            st.warning("No preferences on file — customer may not have set them up yet.")
        else:
            # Diet type
            diet = preferences.get("diet_type", "")
            if diet:
                st.markdown(f'<span class="pref-tag pref-diet">🥗 {diet.title()}</span>', unsafe_allow_html=True)

            # Spice level
            spice = preferences.get("spice_level", "")
            if spice:
                st.markdown(f'<span class="pref-tag pref-spice">🌶️ {spice.title()} spice</span>', unsafe_allow_html=True)

            # Favorite cuisines
            cuisines = preferences.get("favorite_cuisines", [])
            if cuisines:
                st.markdown("**Cuisines they love:**")
                for c in cuisines:
                    st.markdown(f'<span class="pref-tag pref-cuisine">🌍 {c}</span>', unsafe_allow_html=True)

            # Health goals
            if health_goals:
                st.markdown("**Health goals:**")
                for g in health_goals:
                    st.markdown(f'<span class="pref-tag pref-goal">💪 {g}</span>', unsafe_allow_html=True)

            # Allergies (shown again here for quick reference)
            if allergies:
                st.markdown("**Allergies (avoid these ingredients):**")
                for a in allergies:
                    st.markdown(f'<span class="pref-tag pref-allergy">🚨 {a}</span>', unsafe_allow_html=True)

        # Qdrant dietary filter summary
        if dietary_filters:
            st.markdown("**Active menu filters:**")
            for k, v in dietary_filters.items():
                st.caption(f"• `{k}`: `{v}`")

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Visits", visit_count)
    m2.metric("Orders in History", len(order_history))
    m3.metric("Recommendations", len(recommendations))
    m4.metric("Health Warnings", len(health_warnings),
              delta="⚠️ Check above" if health_warnings else None,
              delta_color="inverse")

with tab_recs:
    if not recommendations:
        if is_new:
            st.warning("New customer — no preferences saved yet, so no personalized recommendations are available.")
        else:
            st.info("No recommendations returned by the pipeline.")
    else:
        st.markdown("#### 🏆 Health-Ranked Suggestions")
        st.caption(
            "Dishes ranked by nutritional fit to this customer's health goals. "
            "Suggest these proactively."
        )
        if rec_text:
            with st.expander("💬 AI Narrative (what the AI would tell the customer)", expanded=False):
                st.markdown(rec_text)

        for rank, item in enumerate(recommendations, 1):
            name         = item.get("name", "Unknown")
            calories     = item.get("calories", "?")
            protein      = item.get("protein_g", "?")
            price        = item.get("price", "?")
            health_score = item.get("health_score", 0.0)
            spice        = item.get("spice_level", "?")
            is_veg       = item.get("is_veg", True)
            cuisine      = item.get("cuisine", "")
            description  = item.get("description", "")

            veg_icon = "🟢" if is_veg else "🔴"

            row_col, score_col = st.columns([5, 1])
            with row_col:
                st.markdown(f"""
                <div class="rec-row">
                    <div class="rec-rank">#{rank}</div>
                    <div style="flex:1">
                        <div class="rec-name">{veg_icon} {name}</div>
                        <div class="rec-meta">
                            🔥 {calories} kcal &nbsp;|&nbsp;
                            💪 {protein}g protein &nbsp;|&nbsp;
                            🌶️ {spice} &nbsp;|&nbsp;
                            🌍 {cuisine} &nbsp;|&nbsp;
                            ₹{price}
                        </div>
                        <div class="rec-meta" style="margin-top:0.3rem; color:#555">{description}</div>
                    </div>
                    <div>
                        <div class="rec-hs">{health_score}</div>
                        <div class="hs-lbl">health score</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

with tab_history:
    if not order_history:
        if is_new:
            st.info("New customer — no order history on file.")
        else:
            st.info("No recent orders found for this customer.")
    else:
        st.markdown("#### 📦 Recent Orders")
        st.caption(
            f"Last {len(order_history)} orders — use this to understand their taste and avoid repeating "
            "what they've already had."
        )

        for i, order in enumerate(order_history, 1):
            # order dict keys depend on what memory_agent returns
            # common fields: item_name, price, created_at, category
            item_name  = order.get("item_name") or order.get("name") or f"Order #{i}"
            price      = order.get("price", "?")
            ordered_at = order.get("created_at", "")
            category   = order.get("category", "")

            # Format the date if present
            date_str = ""
            if ordered_at:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(str(ordered_at).replace("Z", "+00:00"))
                    date_str = dt.strftime("%b %d, %Y %I:%M %p")
                except Exception:
                    date_str = str(ordered_at)[:10]

            st.markdown(f"""
            <div class="hist-row">
                <div>
                    <div class="hist-name">🍽️ {item_name}</div>
                    <div class="hist-meta">{category}{' · ' if category and date_str else ''}{date_str}</div>
                </div>
                <div style="font-weight:700; color:#1A1A2E">₹{price}</div>
            </div>
            """, unsafe_allow_html=True)

        # Summary insight for the waiter
        if len(order_history) >= 3:
            names = [o.get("item_name") or o.get("name", "") for o in order_history]
            most_recent = names[0] if names else ""
            st.markdown("---")
            st.caption(
                f"💡 **Waiter tip:** This customer's most recent order was **{most_recent}**. "
                "Consider recommending something complementary or something new from a category they haven't tried."
            )
