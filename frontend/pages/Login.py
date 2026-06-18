import streamlit as st
from config import APP_NAME, APP_ICON, PRIMARY_COLOR
from api.auth_api import send_otp, verify_otp

st.set_page_config(
    page_title=f"Login — {APP_NAME}",
    page_icon=APP_ICON,
    layout="centered",   # centered layout works better for login forms
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    /* Hide sidebar on login page */
    [data-testid="stSidebar"] {{ display: none; }}
    [data-testid="stSidebarNav"] {{ display: none; }}

    .login-header {{
        text-align: center;
        padding: 2rem 0 1rem 0;
    }}
    .login-header h1 {{
        font-size: 2.5rem;
        color: {PRIMARY_COLOR};
        margin-bottom: 0.2rem;
    }}
    .login-header p {{
        color: #666;
        font-size: 1rem;
    }}
    .otp-box {{
        background: #FFF3EE;
        border: 1px solid {PRIMARY_COLOR};
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0 1rem 0;
        font-size: 1.5rem;
        font-weight: bold;
        letter-spacing: 6px;
        text-align: center;
        color: {PRIMARY_COLOR};
    }}
    .divider {{ color: #ccc; text-align: center; margin: 1rem 0; }}
</style>
""", unsafe_allow_html=True)

# ── If already logged in, redirect immediately ─────────────────────────────────
if st.session_state.get("token"):
    st.switch_page("pages/Dashboard.py")

# Header
st.markdown("""
<div class="login-header">
    <h1>🍽️ MenuMind</h1>
    <p>AI-Powered Restaurant Personalization</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

#  State initialisation
# Streamlit reruns the entire script on every user interaction.
# session_state is how we remember "which step the user is on" across reruns.
if "otp_sent" not in st.session_state:
    st.session_state["otp_sent"] = False
if "login_phone" not in st.session_state:
    st.session_state["login_phone"] = ""
if "dev_otp" not in st.session_state:
    st.session_state["dev_otp"] = ""

if not st.session_state["otp_sent"]:
    st.subheader("Welcome back 👋")
    st.caption("Enter your phone number to receive a one-time password.")

    phone = st.text_input(
        "Phone Number",
        placeholder="+919876543210",
        help="Include country code, e.g. +91 for India",
    )

    if st.button("Send OTP →", type="primary", use_container_width=True):
        if not phone.strip():
            st.error("Please enter a phone number.")
        else:
            with st.spinner("Sending OTP…"):
                data, status = send_otp(phone.strip())

            if status == 200:
                st.session_state["login_phone"] = phone.strip()
                st.session_state["otp_sent"] = True
                # Backend returns OTP directly (mock — no real SMS yet)
                st.session_state["dev_otp"] = str(data.get("otp", ""))
                # st.rerun() triggers a full script rerun so Step 2 renders
                st.rerun()
            else:
                st.error(data.get("detail", "Failed to send OTP. Please try again."))

else:
    phone = st.session_state["login_phone"]
    st.subheader("Enter your OTP")
    st.caption(f"OTP sent to **{phone}**")

    # Development helper — shows the OTP returned by the mock backend
    if st.session_state.get("dev_otp"):
        st.markdown(f"""
        <div class="otp-box">🔑 {st.session_state['dev_otp']}</div>
        """, unsafe_allow_html=True)
        st.caption("⚠️ Dev mode: OTP displayed above (real SMS not yet enabled)")

    otp_input = st.text_input(
        "6-Digit OTP",
        max_chars=6,
        placeholder="123456",
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            # Reset to step 1
            st.session_state["otp_sent"] = False
            st.session_state["dev_otp"] = ""
            st.rerun()

    with col2:
        if st.button("Verify OTP →", type="primary", use_container_width=True):
            if not otp_input.strip():
                st.error("Please enter the OTP.")
            elif len(otp_input.strip()) != 6:
                st.error("OTP must be exactly 6 digits.")
            else:
                with st.spinner("Verifying…"):
                    data, status = verify_otp(phone, otp_input.strip())

                if status == 200:
                    # Store auth state in session_state
                    st.session_state["token"] = data["access_token"]
                    st.session_state["is_new_user"] = data.get("is_new_user", False)

                    # Clean up login-specific state
                    st.session_state.pop("otp_sent", None)
                    st.session_state.pop("dev_otp", None)
                    st.session_state.pop("login_phone", None)

                    st.success("Login successful! Redirecting…")
                    st.switch_page("pages/Dashboard.py")
                else:
                    st.error(data.get("detail", "Invalid OTP. Please try again."))
