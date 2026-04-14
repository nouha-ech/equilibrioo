import streamlit as st # type: ignore
from agents.stress_detector import StressDetectorAgent
from agents.wellness_coach import WellnessCoachAgent
from agents.session_state import init_session
from pages.onboarding import show_onboarding
from pages.dashboard import show_dashboard
from pages.chat import show_chat
from dotenv import load_dotenv
load_dotenv()
st.set_page_config(
    page_title="Equilibirio — Student Wellness Coach",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Sora:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3 { font-family: 'Sora', sans-serif; }

.stApp { background: #0F0F14; color: #E8E6F0; }

.stress-badge-low    { background: #1a3a2a; color: #5DCAA5; border: 1px solid #1D9E75; padding: 4px 12px; border-radius: 20px; font-size: 13px; }
.stress-badge-medium { background: #3a2a10; color: #FAC775; border: 1px solid #BA7517; padding: 4px 12px; border-radius: 20px; font-size: 13px; }
.stress-badge-high   { background: #3a1010; color: #F09595; border: 1px solid #A32D2D; padding: 4px 12px; border-radius: 20px; font-size: 13px; }

.metric-card {
    background: #1A1A24;
    border: 1px solid #2A2A38;
    border-radius: 16px;
    padding: 20px;
    margin: 8px 0;
}

.routine-card {
    background: linear-gradient(135deg, #1A1A24, #1E1A2E);
    border: 1px solid #2A2A40;
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Init session ───────────────────────────────────────────────────────────────
init_session()

# ── Sidebar navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 MindFlow")
    st.markdown("*Student Wellness AI Coach*")
    st.divider()

    if not st.session_state.get("onboarded"):
        page = "Onboarding"
    else:
        page = st.radio(
            "Navigation",
            ["Dashboard", "Chat & Analysis", "Ma Routine",  " Classroom", "Profil"],
            index=0
        )
        st.divider()
        if st.session_state.get("user_profile"):
            p = st.session_state.user_profile
            st.markdown(f"**{p.get('name', 'Étudiant')}**")
            st.caption(f"{p.get('field', '')} · {p.get('year', '')}")

# ── Routing ───────────────────────────────────────────────────────────────────
if not st.session_state.get("onboarded"):
    show_onboarding()
elif page == "Dashboard":
    show_dashboard()
elif page == "Chat & Analysis":
    show_chat()
elif page == "Ma Routine":
    from pages.routine import show_routine
    show_routine()
elif page == "Classroom":
    from pages.classroom import show_classroom
    show_classroom()
elif page == "Profil":
    from pages.profile import show_profile
    show_profile()
