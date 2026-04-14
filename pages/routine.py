"""Ma Routine — Génération et affichage de la routine bien-être."""
import streamlit as st # type: ignore
from agents.session_state import get_agents # type: ignore


def show_routine():
    profile = st.session_state.user_profile
    stress_agent, coach_agent = get_agents()

    st.markdown("##  Ma Routine Bien-Être")

    if not coach_agent:
        st.error(" Clé API non configurée.")
        return

   
    if not st.session_state.current_routine:
        st.info(f"""
        **Crée ta routine personnalisée !**
        
        MindFlow va analyser ton profil et générer une routine quotidienne adaptée à :
        - Ta filière : **{profile.get('field')}**
        - Ton niveau : **{profile.get('year')}**
        - Ton objectif : *{profile.get('goal', 'Non défini')}*
        """)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✨ Générer ma routine personnalisée", use_container_width=True):
                with st.spinner("MindFlow crée ta routine optimale... (peut prendre 15-20 sec)"):
                    try:
                        routine = coach_agent.generate_routine(profile)
                        st.session_state.current_routine = routine
                        st.success("Routine créée avec succès !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de la génération: {str(e)}")
    else:
        routine = st.session_state.current_routine
        display_routine(routine, profile, coach_agent)


def display_routine(routine: dict, profile: dict, coach_agent):
    """Affiche la routine générée."""
    name = routine.get("routine_name", "Ta Routine MindFlow")
    st.markdown(f"### ✨ {name}")

    # Impact estimé
    impact = routine.get("estimated_impact", {})
    if impact:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📉 Réduction stress", impact.get("stress_reduction", "—"))
        with col2:
            st.metric("🎯 Amélioration focus", impact.get("focus_improvement", "—"))
        with col3:
            st.metric("😴 Qualité sommeil", impact.get("sleep_quality", "—"))

    st.divider()

    # Message de motivation
    if routine.get("motivation_message"):
        st.markdown(f"""
        <div style="background:#1A1A24; border-left:4px solid #7F77DD; border-radius:8px; padding:16px; margin:16px 0;">
        💬 <em>"{routine['motivation_message']}"</em>
        </div>
        """, unsafe_allow_html=True)

    # ── Sections de la routine ─────────────────────────────────────────────────
    tabs = st.tabs(["🌅 Matin", "📚 Travail", "☕ Pauses", "🌙 Soir", "🎯 Objectifs"])

    section_map = [
        ("morning", tabs[0]),
        ("study_blocks", tabs[1]),
        ("breaks", tabs[2]),
        ("evening", tabs[3]),
    ]

    for section_key, tab in section_map:
        with tab:
            items = routine.get(section_key, [])
            if not items:
                st.info("Section non disponible.")
                continue
            for item in items:
                render_activity_card(item)

    with tabs[4]:
        goals = routine.get("weekly_goals", [])
        st.markdown("### 🎯 Objectifs hebdomadaires")
        for i, goal in enumerate(goals, 1):
            checked = st.checkbox(goal, key=f"goal_{i}")

        analysis = routine.get("analysis", {})
        if analysis:
            st.divider()
            st.markdown("### 🔍 Analyse de ton profil")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Besoins identifiés:**")
                for need in analysis.get("needs", []):
                    st.markdown(f"• {need}")
            with col2:
                st.markdown("**Forces à exploiter:**")
                for strength in analysis.get("strengths_to_leverage", []):
                    st.markdown(f"✅ {strength}")

    # ── Adapter la routine ─────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔄 Adapter ma routine")
    feedback = st.text_area(
        "Un retour sur ta routine ?",
        placeholder="Ex: Je n'ai pas 30 min le matin, je préfère le soir, le yoga c'est pas pour moi...",
        height=80
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Adapter", use_container_width=True) and feedback:
            with st.spinner("Adaptation en cours..."):
                try:
                    profile = st.session_state.user_profile
                    adapted = coach_agent.adapt_routine(
                        st.session_state.current_routine,
                        feedback,
                        profile
                    )
                    st.session_state.current_routine = adapted
                    st.success("Routine adaptée !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")
    with col2:
        if st.button("🗑️ Recréer", use_container_width=True):
            st.session_state.current_routine = None
            st.rerun()


def render_activity_card(item: dict):
    """Affiche une carte d'activité."""
    icon = item.get("icon", "•")
    name = item.get("activity", "Activité")
    time_slot = item.get("time", "")
    duration = item.get("duration", 0)
    description = item.get("description", "")
    technique = item.get("technique", "")
    benefit = item.get("benefit", "")

    st.markdown(f"""
    <div style="background:#1A1A24; border:1px solid #2A2A38; border-radius:12px; padding:16px; margin:8px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <strong style="font-size:16px;">{icon} {name}</strong>
            <span style="background:#2A2A38; padding:4px 10px; border-radius:20px; font-size:12px; color:#9090A0;">⏱ {duration} min · {time_slot}</span>
        </div>
        <p style="color:#C0C0D0; font-size:14px; margin:4px 0;">{description}</p>
        <div style="display:flex; gap:8px; margin-top:8px; flex-wrap:wrap;">
            {f'<span style="background:#1E2A3A; color:#5DCAA5; padding:3px 10px; border-radius:20px; font-size:12px;">🔬 {technique}</span>' if technique else ''}
            {f'<span style="background:#2A1E3A; color:#AFA9EC; padding:3px 10px; border-radius:20px; font-size:12px;">✨ {benefit}</span>' if benefit else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)
