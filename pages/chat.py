
import streamlit as st
from agents.session_state import get_agents
import time


STRESS_COLORS = {
    "low": ("🟢", "#5DCAA5", "Faible"),
    "medium": ("🟡", "#FAC775", "Modéré"),
    "high": ("🔴", "#F09595", "Élevé"),
    "critical": ("🆘", "#E24B4A", "Critique")
}


def show_chat():
    st.markdown("## 💬 Chat & Analyse de Stress")
    st.caption("Parle librement — MindFlow analyse ton niveau de stress en temps réel et propose des techniques adaptées.")

    profile = st.session_state.user_profile
    stress_agent, coach_agent = get_agents()

    if not stress_agent:
        st.error("❌ Clé API non configurée. Va dans Profil pour la configurer.")
        return

    
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            role = msg["role"]
            content = msg["content"]
            stress_data = msg.get("stress")

            if role == "user":
                with st.chat_message("user"):
                    st.write(content)
                    if stress_data:
                        level = stress_data.get("level", "low")
                        score = stress_data.get("score", 0)
                        icon, color, label = STRESS_COLORS.get(level, ("🟢", "#5DCAA5", "Faible"))
                        st.markdown(
                            f'<span style="font-size:12px; color:{color};">{icon} Stress {label} · {score}/100</span>',
                            unsafe_allow_html=True
                        )
            else:
                with st.chat_message("assistant", avatar="🧠"):
                    st.write(content)

                    # Afficher les techniques si analyse complète
                    if msg.get("techniques"):
                        with st.expander("🛠️ Techniques recommandées"):
                            for tech in msg["techniques"]:
                                col1, col2 = st.columns([1, 3])
                                with col1:
                                    st.markdown(f"**{tech.get('nom', tech.get('name', ''))}**")
                                    st.caption(f"⏱ {tech.get('durée', tech.get('duration', ''))}")
                                with col2:
                                    st.write(tech.get('description', ''))

    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.chat_input(f"Comment tu vas aujourd'hui, {profile.get('name', '')} ?")

    if user_input:
        # Quick stress scan
        with st.spinner("Analyse en cours..."):
            try:
                quick_stress = stress_agent.quick_scan(user_input)
            except Exception:
                quick_stress = {"level": "low", "score": 20}

        
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input,
            "stress": quick_stress
        })

        
        stress_level = quick_stress.get("level", "low")
        stress_score = quick_stress.get("score", 0)

        with st.spinner("MindFlow réfléchit..."):
            techniques = []
            analysis = None

            
            if stress_score >= 50:
                try:
                    analysis = stress_agent.analyze(user_input, profile)
                    techniques = analysis.techniques if analysis else []
                except Exception as e:
                    pass

            #  response
            coach_response = coach_agent.chat(
                user_input,
                student_profile=profile
            )

        # stress history
        st.session_state.stress_history.append({
            "score": stress_score,
            "level": stress_level,
            "message_preview": user_input[:50]
        })

        # Save assistant response
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": coach_response,
            "techniques": techniques,
            "analysis": analysis.dict() if analysis else None
        })

        st.rerun()

   
    with st.sidebar:
        if st.session_state.stress_history:
            st.markdown("### 📊 Historique stress")
            scores = [h["score"] for h in st.session_state.stress_history[-10:]]
            if scores:
                import pandas as pd
                df = pd.DataFrame({"Score": scores})
                st.line_chart(df, height=100, use_container_width=True)

            avg = sum(scores) / len(scores)
            color = "#5DCAA5" if avg < 40 else "#FAC775" if avg < 70 else "#F09595"
            st.markdown(f"**Moyenne:** <span style='color:{color}'>{avg:.0f}/100</span>", unsafe_allow_html=True)

        st.divider()
        if st.button("🗑️ Effacer le chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.session_state.stress_history = []
            if st.session_state.coach_agent:
                st.session_state.coach_agent.conversation_history = []
            st.rerun()
