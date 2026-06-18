import streamlit as st
from config import APP_NAME, APP_ICON, PRIMARY_COLOR
from utils.auth_guard import require_auth, render_sidebar
from api.menu_api import get_menu_items, create_order

st.set_page_config(
    page_title=f"Menu — {APP_NAME}",
    page_icon=APP_ICON,
    layout="wide",
)

token = require_auth()
render_sidebar(active_page="Menu")

st.markdown(f"""
<style>
    .menu-card {{
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        height: 100%;
        border-top: 3px solid {PRIMARY_COLOR};
        margin-bottom: 1rem;
    }}
    .item-name {{ font-size: 1.05rem; font-weight: 700; color: #1A1A2E; margin: 0.3rem 0; }}
    .item-desc {{ font-size: 0.82rem; color: #666; margin-bottom: 0.6rem;
                  display: -webkit-box; -webkit-line-clamp: 2;
                  -webkit-box-orient: vertical; overflow: hidden; }}
    .badge {{
        display: inline-block; border-radius: 12px;
        padding: 0.15rem 0.6rem; font-size: 0.75rem; font-weight: 600; margin: 0.1rem;
    }}
    .veg   {{ background:#E8F5E9; color:#2E7D32; border:1px solid #A5D6A7; }}
    .nonveg{{ background:#FFEBEE; color:#C62828; border:1px solid #EF9A9A; }}
    .spice {{ background:#FFF3E0; color:#E65100; border:1px solid #FFCC80; }}
    .macro {{ font-size: 0.78rem; color: #777; margin: 0.4rem 0; }}
    .price {{ font-size: 1.1rem; font-weight: 700; color: {PRIMARY_COLOR}; }}
    .cart-bar {{
        position: sticky; bottom: 0;
        background: #1A1A2E; color: white;
        border-radius: 12px; padding: 1rem 1.5rem;
        display: flex; justify-content: space-between; align-items: center;
        margin-top: 2rem;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown("## 📋 Menu")
st.caption("Browse our full menu. Add items to your cart and place an order.")

if "all_menu_items" not in st.session_state:
    items, status = get_menu_items(token)
    if status == 200:
        st.session_state["all_menu_items"] = items
    else:
        st.error("Could not load menu. Is the backend running?")
        st.stop()

all_items: list[dict] = st.session_state.get("all_menu_items", [])

# Cart is a list of item dicts: [{id, name, price}, ...]
if "cart" not in st.session_state:
    st.session_state["cart"] = []

st.markdown("#### 🔎 Filter & Search")
f1, f2, f3, f4, f5 = st.columns([2, 1.5, 1.5, 1.5, 1.5])

with f1:
    search_text = st.text_input("Search", placeholder="paneer, biryani…", label_visibility="collapsed")

with f2:
    categories = ["All"] + sorted({i.get("category", "") for i in all_items if i.get("category")})
    selected_cat = st.selectbox("Category", categories, label_visibility="collapsed")

with f3:
    diet_choice = st.selectbox("Diet", ["All", "🟢 Veg", "🔴 Non-Veg"], label_visibility="collapsed")

with f4:
    spice_levels = ["All", "none", "mild", "medium", "hot", "extra_hot"]
    selected_spice = st.selectbox("Spice", spice_levels, label_visibility="collapsed")

with f5:
    max_cal = st.slider("Max Cal", min_value=0, max_value=700, value=700, step=50)

st.markdown("---")

def matches_filters(item: dict) -> bool:
    if search_text and search_text.lower() not in item.get("name", "").lower():
        return False
    if selected_cat != "All" and item.get("category") != selected_cat:
        return False
    if diet_choice == "🟢 Veg" and not item.get("is_veg"):
        return False
    if diet_choice == "🔴 Non-Veg" and item.get("is_veg"):
        return False
    if selected_spice != "All" and item.get("spice_level") != selected_spice:
        return False
    if item.get("calories") and item["calories"] > max_cal:
        return False
    return True

filtered = [i for i in all_items if matches_filters(i)]
st.caption(f"Showing **{len(filtered)}** of {len(all_items)} items")

def add_to_cart(item: dict) -> None:
    # Prevent duplicate entries in cart
    existing_ids = [c["id"] for c in st.session_state["cart"]]
    if item["id"] not in existing_ids:
        st.session_state["cart"].append({
            "id": item["id"],
            "name": item["name"],
            "price": item.get("price", 0),
        })

def remove_from_cart(item_id: int) -> None:
    st.session_state["cart"] = [c for c in st.session_state["cart"] if c["id"] != item_id]

COLS = 3
cart_ids = {c["id"] for c in st.session_state["cart"]}

if not filtered:
    st.info("No items match your filters. Try adjusting the search or filters.")
else:
    for row_start in range(0, len(filtered), COLS):
        row_items = filtered[row_start : row_start + COLS]
        cols = st.columns(COLS, gap="medium")

        for col, item in zip(cols, row_items):
            with col:
                item_id   = item.get("id")
                is_veg    = item.get("is_veg", True)
                spice     = item.get("spice_level", "medium")
                veg_badge = '<span class="badge veg">🟢 Veg</span>' if is_veg else '<span class="badge nonveg">🔴 Non-Veg</span>'
                spice_badge = f'<span class="badge spice">🌶️ {spice.title()}</span>'

                st.markdown(f"""
                <div class="menu-card">
                    {veg_badge} {spice_badge}
                    <div class="item-name">{item.get('name', '')}</div>
                    <div class="item-desc">{item.get('description', '')}</div>
                    <div class="macro">
                        🔥 {item.get('calories','?')} kcal &nbsp;|&nbsp;
                        💪 {item.get('protein_g','?')}g protein &nbsp;|&nbsp;
                        🏷️ {item.get('category','?')}
                    </div>
                    <div class="price">₹{item.get('price','?')}</div>
                </div>
                """, unsafe_allow_html=True)

                # Cart toggle button
                if item_id in cart_ids:
                    if st.button(f"✅ In Cart", key=f"rm_{item_id}", use_container_width=True):
                        remove_from_cart(item_id)
                        st.rerun()
                else:
                    if st.button(f"+ Add to Cart", key=f"add_{item_id}", use_container_width=True, type="primary"):
                        add_to_cart(item)
                        st.rerun()

st.markdown("---")
st.markdown("### 🛒 Cart")

cart = st.session_state["cart"]
if not cart:
    st.caption("Your cart is empty. Add items from the menu above.")
else:
    total_price = sum(c.get("price", 0) for c in cart)

    for c in cart:
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"🍽️ **{c['name']}** &nbsp;&nbsp; ₹{c['price']}")
        with c2:
            if st.button("Remove", key=f"del_{c['id']}"):
                remove_from_cart(c["id"])
                st.rerun()

    st.markdown(f"**Total: ₹{total_price:.2f}** ({len(cart)} item{'s' if len(cart) > 1 else ''})")

    col_place, col_clear = st.columns([2, 1])
    with col_place:
        if st.button("✅ Place Order", type="primary", use_container_width=True):
            item_ids = [c["id"] for c in cart]
            with st.spinner("Placing order…"):
                result, status = create_order(token, item_ids)

            if status == 201:
                placed = result.get("total", len(item_ids))
                st.success(f"🎉 Order placed! {placed} item(s) added to your history.")
                st.session_state["cart"] = []
                # Bust order history cache so Dashboard refreshes
                st.session_state.pop("all_menu_items", None)
                st.balloons()
                st.rerun()
            else:
                st.error(result.get("detail", "Failed to place order. Please try again."))

    with col_clear:
        if st.button("🗑️ Clear Cart", use_container_width=True):
            st.session_state["cart"] = []
            st.rerun()
