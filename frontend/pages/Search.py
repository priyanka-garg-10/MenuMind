import streamlit as st
from config import APP_NAME, APP_ICON, PRIMARY_COLOR
from utils.auth_guard import require_auth, render_sidebar
from api.search_api import semantic_search
from api.menu_api import create_order

st.set_page_config(
    page_title=f"Search — {APP_NAME}",
    page_icon=APP_ICON,
    layout="wide",
)

token = require_auth()
render_sidebar(active_page="Search")

st.markdown(f"""
<style>
    .search-hero {{
        background: linear-gradient(135deg, {PRIMARY_COLOR}15, #F5A62315);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }}
    .search-hero h2 {{ color: #1A1A2E; margin-bottom: 0.3rem; }}
    .search-hero p  {{ color: #666; }}

    .result-card {{
        background: white;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        margin-bottom: 1rem;
        border-left: 4px solid {PRIMARY_COLOR};
    }}
    .result-name  {{ font-size: 1.1rem; font-weight: 700; color: #1A1A2E; }}
    .result-desc  {{ font-size: 0.82rem; color: #666; margin: 0.3rem 0; }}
    .result-macro {{ font-size: 0.82rem; color: #555; }}
    .score-label  {{
        font-size: 0.85rem; font-weight: 700;
        color: {PRIMARY_COLOR}; float: right;
    }}
    .tag {{
        display: inline-block; border-radius: 10px;
        padding: 0.15rem 0.6rem; font-size: 0.72rem;
        margin: 0.1rem;
    }}
    .tag-veg    {{ background:#E8F5E9; color:#2E7D32; }}
    .tag-nonveg {{ background:#FFEBEE; color:#C62828; }}
    .tag-spice  {{ background:#FFF3E0; color:#E65100; }}
    .tag-cat    {{ background:#E3F2FD; color:#1565C0; }}

    .example-pill {{
        display: inline-block;
        background: white;
        border: 1px solid {PRIMARY_COLOR};
        color: {PRIMARY_COLOR};
        border-radius: 20px;
        padding: 0.3rem 1rem;
        font-size: 0.82rem;
        margin: 0.3rem;
        cursor: pointer;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="search-hero">
    <h2>🔍 Semantic Menu Search</h2>
    <p>Search in plain English. Our AI understands meaning, not just keywords.</p>
</div>
""", unsafe_allow_html=True)

EXAMPLES = [
    "High protein vegetarian food",
    "Light low calorie dinner",
    "Spicy Indian main course",
    "Something refreshing to drink",
    "Healthy iron-rich starter",
    "Rich creamy comfort food",
]

st.caption("✨ Try one of these:")
example_cols = st.columns(len(EXAMPLES))
for col, example in zip(example_cols, EXAMPLES):
    with col:
        if st.button(example, use_container_width=True, key=f"ex_{example}"):
            st.session_state["search_query"] = example
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Use session_state to persist the query across reruns triggered by example buttons
default_query = st.session_state.get("search_query", "")

search_col, btn_col = st.columns([5, 1])
with search_col:
    query = st.text_input(
        "Search",
        value=default_query,
        placeholder="e.g. high protein vegetarian food under 400 calories",
        label_visibility="collapsed",
    )
with btn_col:
    search_clicked = st.button("Search →", type="primary", use_container_width=True)

with st.expander("⚙️ Optional Filters", expanded=False):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        diet_filter = st.selectbox("Diet", ["Any", "Veg only", "Non-Veg only"])
    with fc2:
        max_cal_filter = st.slider("Max Calories", 0, 700, 700, step=50)
    with fc3:
        min_prot_filter = st.slider("Min Protein (g)", 0, 50, 0, step=5)

st.markdown("---")

is_veg_filter  = True  if diet_filter == "Veg only"     else (
                  False if diet_filter == "Non-Veg only" else None)
max_cal_value  = max_cal_filter  if max_cal_filter  < 700 else None
min_prot_value = min_prot_filter if min_prot_filter > 0   else None

run_search = search_clicked or (
    st.session_state.get("search_query") and
    st.session_state.get("_last_searched") != st.session_state.get("search_query")
)

if run_search and query.strip():
    st.session_state["search_query"] = query.strip()
    st.session_state["_last_searched"] = query.strip()

    with st.spinner("Searching with AI…"):
        results, status = semantic_search(
            token=token,
            query=query.strip(),
            limit=8,
            is_veg=is_veg_filter,
            max_calories=max_cal_value,
            min_protein=min_prot_value,
        )

    st.session_state["search_results"] = results
    st.session_state["search_status"] = status

results = st.session_state.get("search_results")
status  = st.session_state.get("search_status")

if results is None:
    st.info("Enter a search query above to find dishes using AI-powered semantic search.")

elif status not in (200, None):
    st.error("Search failed. Please check that the backend and Qdrant are running.")

elif len(results) == 0:
    st.warning("No results found. Try broadening your query or removing filters.")

else:
    st.markdown(f"### 🎯 {len(results)} Result{'s' if len(results) > 1 else ''} Found")
    st.caption(f'For query: *"{st.session_state.get("search_query", "")}"*')
    st.markdown("<br>", unsafe_allow_html=True)

    # Cart init
    if "cart" not in st.session_state:
        st.session_state["cart"] = []
    cart_ids = {c["id"] for c in st.session_state["cart"]}

    for item in results:
        score      = item.get("score", 0.0)
        pct        = int(score * 100)
        is_veg     = item.get("is_veg", True)
        item_id    = item.get("mysql_id")   # Qdrant results use mysql_id
        name       = item.get("name", "")

        # Score colour: green ≥80%, amber 60–79%, grey <60%
        score_color = ("#27AE60" if pct >= 80 else "#F5A623" if pct >= 60 else "#999")

        veg_tag   = f'<span class="tag tag-veg">🟢 Veg</span>'   if is_veg else f'<span class="tag tag-nonveg">🔴 Non-Veg</span>'
        spice_tag = f'<span class="tag tag-spice">🌶️ {item.get("spice_level","").title()}</span>'
        cat_tag   = f'<span class="tag tag-cat">{item.get("category","")}</span>'

        col_info, col_score, col_action = st.columns([5, 1, 1])

        with col_info:
            st.markdown(f"""
            <div class="result-card">
                {veg_tag} {spice_tag} {cat_tag}
                <div class="result-name">{name}</div>
                <div class="result-desc">{item.get('description','')}</div>
                <div class="result-macro">
                    🔥 {item.get('calories','?')} kcal &nbsp;|&nbsp;
                    💪 {item.get('protein_g','?')}g protein &nbsp;|&nbsp;
                    ₹{item.get('price','?')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_score:
            st.markdown(f"<br>", unsafe_allow_html=True)
            st.markdown(
                f'<div style="text-align:center; font-size:1.4rem; font-weight:700; color:{score_color}">'
                f'{pct}%</div>'
                f'<div style="text-align:center; font-size:0.7rem; color:#999">match</div>',
                unsafe_allow_html=True,
            )
            # Visual score bar using st.progress()
            st.progress(score)

        with col_action:
            st.markdown("<br>", unsafe_allow_html=True)
            if item_id:
                if item_id in cart_ids:
                    if st.button("✅ In Cart", key=f"sr_{item_id}", use_container_width=True):
                        st.session_state["cart"] = [
                            c for c in st.session_state["cart"] if c["id"] != item_id
                        ]
                        st.rerun()
                else:
                    if st.button("+ Cart", key=f"sa_{item_id}", use_container_width=True, type="primary"):
                        st.session_state["cart"].append({
                            "id": item_id,
                            "name": name,
                            "price": item.get("price", 0),
                        })
                        st.rerun()

    cart = st.session_state.get("cart", [])
    if cart:
        st.markdown("---")
        st.markdown(f"**🛒 Cart: {len(cart)} item(s)** — Go to [Menu](Menu) to manage your cart, or:")
        if st.button("✅ Place Order Now", type="primary"):
            item_ids = [c["id"] for c in cart]
            with st.spinner("Placing order…"):
                result, status = create_order(token, item_ids)
            if status == 201:
                st.success(f"🎉 Order placed! {result.get('total')} item(s) ordered.")
                st.session_state["cart"] = []
                st.balloons()
                st.rerun()
            else:
                st.error(result.get("detail", "Failed to place order."))
