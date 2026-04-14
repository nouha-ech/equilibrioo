
import streamlit as st


def show_profile():
    profile = st.session_state.user_profile
    st.markdown("## 👤 Mon Profil")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Nom:** {profile.get('name')}")
        st.markdown(f"**Filière:** {profile.get('field')}")
        st.markdown(f"**Niveau:** {profile.get('year')}")
    with col2:
        st.markdown(f"**Réveil:** {profile.get('wake_time')}")
        st.markdown(f"**Coucher:** {profile.get('sleep_time')}")
        st.markdown(f"**Temps dispo:** {profile.get('available_time')} min/jour")

    st.markdown(f"**Objectif:** {profile.get('goal')}")
    st.markdown(f"**Préoccupations:** {profile.get('concerns')}")

    st.divider()
    api_key = st.text_input("Modifier la clé API", type="password", value=st.session_state.api_key)
    if st.button("Sauvegarder"):
        st.session_state.api_key = api_key
        st.session_state.stress_agent = None
        st.session_state.coach_agent = None
        st.success("Sauvegardé !")

    st.divider()
    if st.button(" Réinitialiser le profil", type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
