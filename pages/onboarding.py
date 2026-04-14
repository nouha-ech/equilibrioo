"""Onboarding — Collecte le profil étudiant."""
import streamlit as st


def show_onboarding():
    st.markdown("#  Bienvenue sur ")
    st.markdown("#### *Ton coach IA pour la stabilité mentale et la réussite académique*")
    st.divider()

    st.markdown("""
    MindFlow analyse ton niveau de stress en temps réel et crée une routine bien-être 
    **personnalisée** selon ton parcours, tes objectifs et tes habitudes.
    """)

    with st.form("onboarding_form"):
        st.markdown("###  Ton profil")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Ton prénom *", placeholder="Ex: Yassine")
            field = st.selectbox("Ta filière *", [
                "Médecine / Pharmacie",
                "Ingénierie / Sciences",
                "Droit / Sciences Politiques",
                "Économie / Gestion",
                "Lettres / Sciences Humaines",
                "Informatique / IA",
                "Architecture / Design",
                "Autre"
            ])
            year = st.selectbox("Niveau d'études *", [
                "1ère année (Bac+1)",
                "2ème année (Bac+2)",
                "Licence 3 (Bac+3)",
                "Master 1 (Bac+4)",
                "Master 2 (Bac+5)",
                "Doctorat",
                "Prépa / Classes prépa"
            ])

        with col2:
            wake_time = st.time_input("Heure de réveil habituelle", value=None)
            sleep_time = st.time_input("Heure de coucher habituelle", value=None)
            available_time = st.slider(
                "Temps disponible pour le bien-être (min/jour)",
                min_value=10, max_value=120, value=30, step=10
            )

        st.markdown(" Tes objectifs & préoccupations")

        goal = st.text_area(
            "Ton objectif principal cette année *",
            placeholder="Ex: Réussir mes examens de fin d'année, décrocher un stage, améliorer ma concentration...",
            height=80
        )

        concerns = st.text_area(
            "Tes préoccupations principales",
            placeholder="Ex: Anxiété des examens, procrastination, manque de sommeil, équilibre vie-études...",
            height=80
        )

        st.markdown(" Tes points forts & faibles")

        col3, col4 = st.columns(2)
        with col3:
            strengths = st.multiselect(
                "Points forts",
                ["Organisé(e)", "Motivé(e)", "Curieux/se", "Persévérant(e)",
                 "Créatif/ve", "Bon(ne) communicant(e)", "Analytique", "Discipliné(e)"],
                default=["Motivé(e)"]
            )
        with col4:
            weaknesses = st.multiselect(
                "Points à améliorer",
                ["Gestion du temps", "Procrastination", "Anxiété", "Concentration",
                 "Sommeil irrégulier", "Perfectionnisme", "Isolement social", "Fatigue chronique"],
                default=["Gestion du temps"]
            )

        

        habits = st.text_area(
            "Habitudes actuelles (sport, lecture, méditation...)",
            placeholder="Ex: Je fais du sport 2x par semaine, je lis avant de dormir...",
            height=60
        )

        submitted = st.form_submit_button(" Créer mon profil MindFlow", use_container_width=True)

        if submitted:
            if not name or not goal:
                st.error("Merci de remplir les champs obligatoires (*) et la clé API.")
            else:
                st.session_state.user_profile = {
                    "name": name,
                    "field": field,
                    "year": year,
                    "goal": goal,
                    "concerns": concerns,
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "habits": habits,
                    "available_time": available_time,
                    "wake_time": str(wake_time) if wake_time else "07:00",
                    "sleep_time": str(sleep_time) if sleep_time else "23:00",
                }
                
                st.session_state.onboarded = True

                # Initialize agents
                from agents.session_state import get_agents
                get_agents()

                st.success(f" Profil créé ! Bienvenue {name} 🎉")
                st.rerun()
