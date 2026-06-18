import re
import streamlit as st
from config import APP_NAME, APP_ICON, PRIMARY_COLOR
from utils.auth_guard import require_auth, render_sidebar
from api.search_api import semantic_search
from api.user_api import get_profile, get_preferences
from api.menu_api import create_order

st.set_page_config(
    page_title=f"Health Assistant — {APP_NAME}",
    page_icon=APP_ICON,
    layout="wide",
)

token = require_auth()
render_sidebar(active_page="Health Assistant")

st.markdown(f"""
<style>
    .assistant-header {{
        background: linear-gradient(135deg, #27AE6015, #2ECC7115);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1rem;
        border-left: 4px solid #27AE60;
    }}
    .dish-inline {{
        background: white;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin: 0.4rem 0;
        box-shadow: 0 1px 6px rgba(0,0,0,0.07);
        border-left: 3px solid {PRIMARY_COLOR};
    }}
    .dish-inline-name {{ font-weight: 700; color: #1A1A2E; font-size: 0.95rem; }}
    .dish-inline-meta {{ font-size: 0.78rem; color: #777; margin-top: 0.2rem; }}
    .quick-chip {{
        display: inline-block;
        background: #F0FFF4;
        border: 1px solid #27AE60;
        color: #27AE60;
        border-radius: 20px;
        padding: 0.3rem 0.9rem;
        font-size: 0.8rem;
        margin: 0.2rem;
        cursor: pointer;
    }}
</style>
""", unsafe_allow_html=True)

if "profile" not in st.session_state:
    profile_data, _ = get_profile(token)
    st.session_state["profile"] = profile_data
    st.session_state["user_name"] = profile_data.get("name") or "Guest"

if "preferences" not in st.session_state:
    pref_data, pref_status = get_preferences(token)
    st.session_state["preferences"] = pref_data if pref_status == 200 else None

prefs     = st.session_state.get("preferences") or {}
user_name = st.session_state.get("user_name", "Guest")

st.markdown(f"""
<div class="assistant-header">
    <h3>💚 Health Assistant</h3>
    <p style="color:#555; margin:0">
        Ask me anything about what to eat today.
        I know your preferences and will filter recommendations just for you.
    </p>
</div>
""", unsafe_allow_html=True)

diet_type = prefs.get("diet_type", "")
if diet_type:
    goals = ", ".join(prefs.get("health_goals", [])) or "none"
    st.caption(
        f"🔒 Auto-filters active: **{diet_type.title()}** diet · "
        f"Goals: **{goals}** · Allergies: **{', '.join(prefs.get('allergies', [])) or 'none'}**"
    )

st.markdown("---")

if "health_chat" not in st.session_state:
    st.session_state["health_chat"] = []

QUICK_QUESTIONS = [
    "What should I eat today?",
    "Meals under 400 calories",
    "High protein options for me",
    "Something light for dinner",
    "Best starter for weight loss",
    "Rich comfort food tonight",
]

if not st.session_state["health_chat"]:
    st.markdown("**💡 Try asking:**")
    cols = st.columns(3)
    for i, q in enumerate(QUICK_QUESTIONS):
        with cols[i % 3]:
            if st.button(q, key=f"qq_{i}", use_container_width=True):
                st.session_state["_pending_question"] = q
                st.rerun()

def extract_calorie_limit(text: str) -> int | None:
    """
    Simple regex to pull calorie numbers from free text.
    "under 500 calories" → 500
    "less than 400 cal"  → 400
    "500 cal meal"       → 500
    """
    match = re.search(r"(\d{3,4})\s*(?:cal|calorie|kcal)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    if re.search(r"under\s+500|less\s+than\s+500", text, re.IGNORECASE):
        return 500
    if re.search(r"under\s+400|less\s+than\s+400", text, re.IGNORECASE):
        return 400
    if re.search(r"light|low.?cal", text, re.IGNORECASE):
        return 450
    return None

def extract_min_protein(text: str) -> float | None:
    match = re.search(r"(\d+)\s*g?\s*protein", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    if re.search(r"high.?protein|protein.?rich", text, re.IGNORECASE):
        return 15.0
    return None

def build_assistant_reply(question: str, dishes: list) -> str:
    """Format a conversational response from the search results."""
    if not dishes:
        return (
            "I couldn't find dishes matching that query with your current filters. "
            "Try rephrasing or ask for something broader!"
        )

    lines = [f"Here are my top picks for **{question.lower()}**:\n"]
    for i, dish in enumerate(dishes[:3], 1):
        is_veg  = "🟢" if dish.get("is_veg") else "🔴"
        score   = int(dish.get("score", 0) * 100)
        lines.append(
            f"**{i}. {dish.get('name', '?')}** {is_veg} — "
            f"{dish.get('calories','?')} kcal · "
            f"{dish.get('protein_g','?')}g protein · "
            f"₹{dish.get('price','?')} · {score}% match"
        )
    return "\n".join(lines)

def process_question(question: str) -> None:
    """
    Called when the user submits a question.
    1. Appends user message to history.
    2. Calls semantic search with auto-applied health filters.
    3. Appends assistant response with dishes to history.
    """
    question = question.strip()
    if not question:
        return

    is_veg_filter  = diet_type in ("veg", "vegan", "jain") if diet_type else None
    max_cal        = extract_calorie_limit(question)
    min_prot       = extract_min_protein(question)

    if max_cal is None and "weight-loss" in (prefs.get("health_goals") or []):
        max_cal = 450
    if min_prot is None and "high-protein" in (prefs.get("health_goals") or []):
        min_prot = 12.0

    st.session_state["health_chat"].append({
        "role": "user",
        "content": question,
    })

    results, status = semantic_search(
        token=token,
        query=question,
        limit=5,
        is_veg=is_veg_filter,
        max_calories=max_cal,
        min_protein=min_prot,
    )

    if status != 200:
        reply = "⚠️ Search failed. Please ensure the backend is running."
        dishes = []
    else:
        reply  = build_assistant_reply(question, results)
        dishes = results[:3]

    st.session_state["health_chat"].append({
        "role": "assistant",
        "content": reply,
        "dishes": dishes,
        "filters_applied": {
            "is_veg": is_veg_filter,
            "max_calories": max_cal,
            "min_protein": min_prot,
        },
    })

if "_pending_question" in st.session_state:
    q = st.session_state.pop("_pending_question")
    process_question(q)
    st.rerun()

if "cart" not in st.session_state:
    st.session_state["cart"] = []
cart_ids = {c["id"] for c in st.session_state["cart"]}

for msg_idx, msg in enumerate(st.session_state["health_chat"]):
    with st.chat_message(msg["role"], avatar="🙋" if msg["role"] == "user" else "💚"):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and msg.get("dishes"):
            for dish in msg["dishes"]:
                item_id = dish.get("mysql_id")
                is_veg  = "🟢" if dish.get("is_veg") else "🔴"

                d_col, a_col = st.columns([5, 1])
                with d_col:
                    st.markdown(f"""
                    <div class="dish-inline">
                        <div class="dish-inline-name">{is_veg} {dish.get('name','')}</div>
                        <div class="dish-inline-meta">
                            🔥 {dish.get('calories','?')} kcal &nbsp;|&nbsp;
                            💪 {dish.get('protein_g','?')}g protein &nbsp;|&nbsp;
                            🌶️ {dish.get('spice_level','?').title()} &nbsp;|&nbsp;
                            ₹{dish.get('price','?')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with a_col:
                    if item_id:
                        key = f"hc_{msg_idx}_{item_id}"
                        if item_id in cart_ids:
                            st.button("✅", key=key, use_container_width=True)
                        else:
                            if st.button("+ Cart", key=key,
                                         use_container_width=True, type="primary"):
                                st.session_state["cart"].append({
                                    "id": item_id,
                                    "name": dish.get("name", ""),
                                    "price": dish.get("price", 0),
                                })
                                st.rerun()

            # Show filters that were applied to this message
            filters = msg.get("filters_applied", {})
            applied = [f"`{k}: {v}`" for k, v in filters.items() if v is not None]
            if applied:
                st.caption(f"Filters applied: {' · '.join(applied)}")

if prompt := st.chat_input("Ask me about food, nutrition, or what to eat…"):
    process_question(prompt)
    st.rerun()

if st.session_state["health_chat"]:
    st.markdown("---")
    col_clear, col_order = st.columns([1, 2])
    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state["health_chat"] = []
            st.rerun()
    with col_order:
        cart = st.session_state.get("cart", [])
        if cart:
            if st.button(f"✅ Place Order ({len(cart)} items)", type="primary", use_container_width=True):
                item_ids = [c["id"] for c in cart]
                result, status = create_order(token, item_ids)
                if status == 201:
                    st.success(f"🎉 Order placed!")
                    st.session_state["cart"] = []
                    st.balloons()
                    st.rerun()
                else:
                    st.error(result.get("detail", "Order failed."))
