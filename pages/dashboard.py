
import streamlit as st
from agents.session_state import get_agents


def show_dashboard():
    profile = st.session_state.user_profile
    name = profile.get("name", "Étudiant")

    st.markdown(f"## 👋 Bonjour, **{name}** !")
    st.caption(f"{profile.get('field')} · {profile.get('year')}")
    st.divider()

    
    col1, col2, col3, col4 = st.columns(4)
    history = st.session_state.stress_history

    with col1:
        avg_stress = sum(h["score"] for h in history) / len(history) if history else 0
        color = "normal" if avg_stress < 40 else "inverse"
        st.metric("Stress moyen", f"{avg_stress:.0f}/100", delta=f"{len(history)} messages analysés")

    with col2:
        routine = st.session_state.current_routine
        status = "✅ Active" if routine else "⚠️ Non créée"
        st.metric("Routine bien-être", status)

    with col3:
        sessions = len([m for m in st.session_state.chat_messages if m["role"] == "user"])
        st.metric("Sessions de chat", sessions)

    with col4:
        high_stress = len([h for h in history if h["score"] >= 70])
        st.metric("Alertes stress élevé", high_stress)

    st.divider()


    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 🎯 Ton objectif")
        st.info(f"**{profile.get('goal', 'Non défini')}**")

        if profile.get("concerns"):
            st.markdown("### ⚠️ Préoccupations")
            st.warning(profile.get("concerns"))

        st.markdown("### 💡 Actions recommandées")
        actions = []
        if not routine:
            actions.append(("", "Créer ta routine personnalisée", "Va dans 'Ma Routine'"))
        if sessions == 0:
            actions.append(("", "Commencer une session de coaching", "Va dans 'Chat & Analyse'"))
        if avg_stress > 60:
            actions.append(("", "Stress élevé détecté", "Essaie une technique de respiration maintenant"))
        if not actions:
            actions.append(("", "Tout va bien !", "Continue sur ta lancée"))

        for icon, title, desc in actions:
            st.markdown(f"""
            <div style="background:#1A1A24; border:1px solid #2A2A38; border-radius:12px; padding:16px; margin:8px 0;">
            <strong>{icon} {title}</strong><br><span style="color:#9090A0; font-size:14px;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        st.markdown("###  Stress récent")
        if history:
            import pandas as pd
            scores = [h["score"] for h in history[-10:]]
            df = pd.DataFrame({"Niveau de stress": scores})
            st.line_chart(df, height=200)
        else:
            st.info("Lance une conversation pour voir ton historique de stress ici.")

        st.markdown("### 🧬 Ton profil")
        if profile.get("strengths"):
            st.markdown("**Points forts:**")
            for s in profile.get("strengths", []):
                st.markdown(f"✅ {s}")
        if profile.get("weaknesses"):
            st.markdown("**À travailler:**")
            for w in profile.get("weaknesses", []):
                st.markdown(f"🎯 {w}")


    st.divider()
    st.markdown("### ⚡ Check stress rapide")
    quick_msg = st.text_input("Comment tu te sens en ce moment ? (1-2 phrases)")
    if st.button("Analyser maintenant", use_container_width=False) and quick_msg:
        stress_agent, coach_agent = get_agents()
        if stress_agent:
            with st.spinner("Analyse..."):
                result = stress_agent.quick_scan(quick_msg)
                score = result.get("score", 0)
                level = result.get("level", "low")
                colors = {"low": "#5DCAA5", "medium": "#FAC775", "high": "#F09595", "critical": "#E24B4A"}
                color = colors.get(level, "#5DCAA5")
                st.markdown(f"""
                <div style="background:#1A1A24; border:2px solid {color}; border-radius:12px; padding:16px;">
                <h4 style="color:{color}">Score de stress: {score}/100</h4>
                <p>Niveau: <strong style="color:{color}">{level.upper()}</strong></p>
                </div>
                """, unsafe_allow_html=True)
