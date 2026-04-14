
import streamlit as st # type: ignore
import os

def init_session():
    defaults = {
        "onboarded": False,
        "user_profile": None,
        "chat_messages": [],
        "stress_history": [],
        "current_routine": None,
        "api_key":os.getenv("ANTHROPIC_API_KEY", "") ,
        "stress_agent": None,
        "coach_agent": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_agents():
    """Lazy-load agents only when API key is set."""
    from agents.stress_detector import StressDetectorAgent
    from agents.wellness_coach import WellnessCoachAgent

    api_key = st.session_state.get("api_key", "")
    if not api_key:
        return None, None

    if not st.session_state.get("stress_agent"):
        st.session_state.stress_agent = StressDetectorAgent(api_key=api_key)
    if not st.session_state.get("coach_agent"):
        st.session_state.coach_agent = WellnessCoachAgent(api_key=api_key)

    return st.session_state.stress_agent, st.session_state.coach_agent
