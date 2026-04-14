"""
Google Classroom Integration Page
Connexion OAuth2 → Cours, Devoirs, Annonces, Notes
+ Analyse IA de la charge de travail via Claude
"""
import streamlit as st
import json
from datetime import datetime, timezone
from agents.session_state import get_agents


try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    import google.auth.exceptions
    GOOGLE_LIBS_OK = True
except ImportError:
    GOOGLE_LIBS_OK = False

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
]

# ── Couleurs statuts ───────────────────────────────────────────────────────────
STATUS_STYLE = {
    "TURNED_IN":   ("✅", "#5DCAA5", "#0A1A0A", "Rendu"),
    "CREATED":     ("📝", "#FAC775", "#1A1000", "À faire"),
    "RETURNED":    ("📬", "#AFA9EC", "#1A1A2A", "Corrigé"),
    "RECLAIMED_BY_STUDENT": ("↩️", "#F09595", "#2A0F0F", "Récupéré"),
    "NEW":         ("🆕", "#7AB8E8", "#0F1A2A", "Nouveau"),
}

COURSE_COLORS = [
    "#7F77DD", "#1D9E75", "#BA7517", "#A32D2D",
    "#185FA5", "#639922", "#D4537E", "#5DCAA5"
]


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: build service
# ─────────────────────────────────────────────────────────────────────────────
def _build_service(creds_data: dict):
    creds = Credentials(
        token=creds_data.get("token"),
        refresh_token=creds_data.get("refresh_token"),
        token_uri=creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=creds_data.get("client_id"),
        client_secret=creds_data.get("client_secret"),
        scopes=creds_data.get("scopes", SCOPES),
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        st.session_state.classroom_creds = json.loads(creds.to_json())
    return build("classroom", "v1", credentials=creds)


def _parse_date(iso_str: str | None) -> datetime | None:
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except Exception:
        return None


def _days_until(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    now = datetime.now(timezone.utc)
    return (dt - now).days


def _urgency_color(days: int | None) -> str:
    if days is None:
        return "#5A5A7A"
    if days < 0:
        return "#E24B4A"   # En retard
    if days <= 2:
        return "#F09595"   # Urgent
    if days <= 5:
        return "#FAC775"   # Bientôt
    return "#5DCAA5"        # OK


# ─────────────────────────────────────────────────────────────────────────────
#  Fetch helpers
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_courses(_creds_json: str) -> list:
    svc = _build_service(json.loads(_creds_json))
    result = svc.courses().list(studentId="me", courseStates=["ACTIVE"]).execute()
    return result.get("courses", [])


@st.cache_data(ttl=300, show_spinner=False)
def fetch_coursework(_creds_json: str, course_id: str) -> list:
    svc = _build_service(json.loads(_creds_json))
    try:
        cw = svc.courses().courseWork().list(courseId=course_id).execute()
        work_items = cw.get("courseWork", [])
        # Fetch submission status for each
        subs = svc.courses().courseWork().studentSubmissions().list(
            courseId=course_id, courseWorkId="-", userId="me"
        ).execute().get("studentSubmissions", [])
        sub_map = {s["courseWorkId"]: s for s in subs}
        for item in work_items:
            sub = sub_map.get(item["id"], {})
            item["_state"] = sub.get("state", "CREATED")
            item["_grade"] = sub.get("assignedGrade")
            item["_draftGrade"] = sub.get("draftGrade")
        return work_items
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_announcements(_creds_json: str, course_id: str) -> list:
    svc = _build_service(json.loads(_creds_json))
    try:
        res = svc.courses().announcements().list(
            courseId=course_id, orderBy="updateTime desc", pageSize=10
        ).execute()
        return res.get("announcements", [])
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
#  AI workload analysis
# ─────────────────────────────────────────────────────────────────────────────
def analyze_workload_with_ai(all_work: list, profile: dict) -> str:
    """Analyse la charge de travail via Claude et donne des recommandations."""
    _, coach = get_agents()
    if not coach:
        return ""

    pending = [w for w in all_work if w.get("_state") == "CREATED"]
    overdue = []
    upcoming = []
    now = datetime.now(timezone.utc)

    for w in pending:
        due = _parse_date(w.get("dueDate") and
                          f"{w['dueDate'].get('year', 2025)}-{w['dueDate'].get('month', 1):02d}-{w['dueDate'].get('day', 1):02d}T23:59:00Z")
        if due and due < now:
            overdue.append(w.get("title", "Devoir inconnu"))
        elif due:
            days = _days_until(due)
            upcoming.append(f"{w.get('title', '?')} (dans {days}j)")

    prompt = f"""En tant que coach bien-être pour étudiants, analyse cette charge de travail :

Étudiant: {profile.get('name')} - {profile.get('field')} {profile.get('year')}
Objectif: {profile.get('goal', 'Non défini')}

Devoirs EN RETARD ({len(overdue)}): {', '.join(overdue) if overdue else 'Aucun'}
Devoirs À VENIR ({len(upcoming)}): {', '.join(upcoming[:5]) if upcoming else 'Aucun'}
Total devoirs en cours: {len(pending)}

Donne:
1. Une évaluation rapide de la charge (faible/modérée/élevée/critique)
2. 2-3 conseils concrets et actionnables pour gérer cette charge
3. Un message encourageant personnalisé

Sois bref, direct et bienveillant. Max 150 mots."""

    try:
        response = coach.llm.invoke([{"role": "user", "content": prompt}])
        return response.content
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
#  UI Components
# ─────────────────────────────────────────────────────────────────────────────
def render_course_card(course: dict, idx: int, is_selected: bool) -> bool:
    color = COURSE_COLORS[idx % len(COURSE_COLORS)]
    name = course.get("name", "Cours sans nom")
    section = course.get("section", "")
    teacher = course.get("descriptionHeading", "")
    room = course.get("room", "")

    border = f"2px solid {color}" if is_selected else f"1px solid #1A1A28"
    bg = "#12121E" if is_selected else "#111118"

    clicked = st.button(
        f"{'▶ ' if is_selected else ''}{name}",
        key=f"course_btn_{course['id']}",
        use_container_width=True,
    )

    st.markdown(f"""
    <div style="background:{bg};border:{border};border-radius:10px;padding:12px;
                margin:-8px 0 8px;border-top:none;border-top-left-radius:0;border-top-right-radius:0;">
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px">
            <div style="width:10px;height:10px;background:{color};border-radius:50%;margin-top:4px;flex-shrink:0"></div>
            <div>
                {'<div style="font-size:11px;color:#7070A0">'+section+'</div>' if section else ''}
                {'<div style="font-size:11px;color:#5A5A7A">'+room+'</div>' if room else ''}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    return clicked


def render_assignment_card(item: dict):
    title = item.get("title", "Sans titre")
    desc = item.get("description", "")
    max_pts = item.get("maxPoints")
    state = item.get("_state", "CREATED")
    grade = item.get("_grade")
    work_type = item.get("workType", "ASSIGNMENT")

    icon, txt_color, bg_color, label = STATUS_STYLE.get(state, ("📋", "#C0C0E0", "#111118", state))

    # Due date
    due_raw = item.get("dueDate")
    due_dt = None
    if due_raw:
        try:
            due_dt = _parse_date(
                f"{due_raw.get('year')}-{due_raw.get('month', 1):02d}-{due_raw.get('day', 1):02d}T23:59:00Z"
            )
        except Exception:
            pass

    days = _days_until(due_dt)
    urg_color = _urgency_color(days)
    due_str = due_dt.strftime("%d %b %Y") if due_dt else "Pas de date limite"

    type_labels = {
        "ASSIGNMENT": "Devoir",
        "SHORT_ANSWER_QUESTION": "Question courte",
        "MULTIPLE_CHOICE_QUESTION": "QCM",
        "QUIZ": "Quiz",
    }
    type_label = type_labels.get(work_type, work_type)

    grade_html = ""
    if grade is not None and max_pts:
        pct = int(grade / max_pts * 100)
        g_color = "#5DCAA5" if pct >= 70 else "#FAC775" if pct >= 50 else "#F09595"
        grade_html = f'<span style="color:{g_color};font-weight:500">{grade}/{max_pts} ({pct}%)</span>'

    days_html = ""
    if days is not None:
        if days < 0:
            days_html = f'<span style="color:#E24B4A">En retard de {abs(days)}j</span>'
        elif days == 0:
            days_html = '<span style="color:#F09595">Aujourd\'hui !</span>'
        else:
            days_html = f'<span style="color:{urg_color}">Dans {days} jour{"s" if days > 1 else ""}</span>'

    st.markdown(f"""
    <div style="background:#111118;border:1px solid #1A1A28;border-radius:10px;
                padding:14px 16px;margin-bottom:8px;border-left:3px solid {urg_color}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px">
            <div style="font-size:14px;font-weight:500;color:#D0D0E8;flex:1;margin-right:12px">{icon} {title}</div>
            <div style="display:flex;gap:6px;align-items:center;flex-shrink:0">
                <span style="background:{bg_color};color:{txt_color};border:1px solid {txt_color}40;
                             padding:2px 8px;border-radius:10px;font-size:11px">{label}</span>
                <span style="background:#1A1A28;color:#6060A0;padding:2px 8px;border-radius:10px;font-size:11px">{type_label}</span>
            </div>
        </div>
        <div style="display:flex;gap:16px;font-size:12px;flex-wrap:wrap">
            <span>📅 {due_str} &nbsp; {days_html}</span>
            {f'<span>🎯 {max_pts} pts</span>' if max_pts else ''}
            {f'<span>🏆 {grade_html}</span>' if grade_html else ''}
        </div>
        {f'<div style="font-size:12px;color:#5A5A7A;margin-top:8px;border-top:1px solid #1A1A28;padding-top:8px">{desc[:200]}{"..." if len(desc)>200 else ""}</div>' if desc else ''}
    </div>
    """, unsafe_allow_html=True)


def render_announcement(ann: dict):
    text = ann.get("text", "")
    updated = ann.get("updateTime", "")
    dt_str = ""
    if updated:
        try:
            dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            dt_str = dt.strftime("%d %b %Y à %H:%M")
        except Exception:
            dt_str = updated[:10]

    st.markdown(f"""
    <div style="background:#0F1218;border:1px solid #1A1A28;border-radius:10px;
                padding:14px 16px;margin-bottom:8px;border-left:3px solid #378ADD">
        <div style="font-size:12px;color:#5A5A7A;margin-bottom:6px">📢 {dt_str}</div>
        <div style="font-size:13px;color:#C0C0D8;line-height:1.6">{text[:400]}{"..." if len(text)>400 else ""}</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Main page
# ─────────────────────────────────────────────────────────────────────────────
def show_classroom():
    st.markdown("## 🎓 Google Classroom")
    profile = st.session_state.get("user_profile", {})

    if not GOOGLE_LIBS_OK:
        st.error("📦 Librairies Google manquantes. Lance : `pip install google-auth google-auth-oauthlib google-api-python-client`")
        st.code("pip install google-auth google-auth-oauthlib google-api-python-client", language="bash")
        return

    # ── CONNEXION ─────────────────────────────────────────────────────────────
    if not st.session_state.get("classroom_creds"):
        _show_connection_ui()
        return

    # ── CONNECTÉ ─────────────────────────────────────────────────────────────
    creds_json = json.dumps(st.session_state.classroom_creds)

    with st.spinner("Chargement des cours..."):
        try:
            courses = fetch_courses(creds_json)
        except Exception as e:
            st.error(f"Erreur de connexion : {e}")
            if st.button("🔄 Se reconnecter"):
                st.session_state.classroom_creds = None
                st.rerun()
            return

    if not courses:
        st.info("Aucun cours actif trouvé dans ton Google Classroom.")
        _disconnect_btn()
        return

    # ── SIDEBAR cours ─────────────────────────────────────────────────────────
    col_courses, col_main = st.columns([1, 3])

    with col_courses:
        st.markdown("### 📚 Mes cours")
        st.caption(f"{len(courses)} cours actifs")

        if "selected_course_id" not in st.session_state:
            st.session_state.selected_course_id = courses[0]["id"]

        for i, course in enumerate(courses):
            is_sel = st.session_state.selected_course_id == course["id"]
            if render_course_card(course, i, is_sel):
                st.session_state.selected_course_id = course["id"]
                st.rerun()

        st.divider()
        _disconnect_btn()

    with col_main:
        sel_id = st.session_state.selected_course_id
        sel_course = next((c for c in courses if c["id"] == sel_id), courses[0])

        course_name = sel_course.get("name", "Cours")
        section = sel_course.get("section", "")
        desc = sel_course.get("description", "")
        link = sel_course.get("alternateLink", "")

        # Header du cours
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            st.markdown(f"### {course_name}")
            if section:
                st.caption(section)
        with col_h2:
            if link:
                st.link_button("Ouvrir dans Classroom ↗", link, use_container_width=True)

        if desc:
            st.markdown(f"*{desc[:200]}*")

        # Tabs
        tab_work, tab_ann, tab_ai = st.tabs(["📋 Devoirs & Travaux", "📢 Annonces", "🤖 Analyse IA"])

        with tab_work:
            with st.spinner("Chargement des devoirs..."):
                work_items = fetch_coursework(creds_json, sel_id)

            if not work_items:
                st.info("Aucun devoir pour ce cours.")
            else:
                # Filtres
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    filter_state = st.selectbox(
                        "Statut", ["Tous", "À faire", "Rendu", "Corrigé"],
                        key=f"filter_state_{sel_id}"
                    )
                with col_f2:
                    sort_by = st.selectbox(
                        "Trier par", ["Date limite", "Création", "Titre"],
                        key=f"sort_{sel_id}"
                    )
                with col_f3:
                    show_count = st.slider("Afficher", 5, 50, 20, key=f"count_{sel_id}")

                # Filter + sort
                state_map = {"À faire": "CREATED", "Rendu": "TURNED_IN", "Corrigé": "RETURNED"}
                filtered = work_items
                if filter_state != "Tous":
                    target = state_map.get(filter_state, "CREATED")
                    filtered = [w for w in work_items if w.get("_state") == target]

                def sort_key(w):
                    if sort_by == "Titre":
                        return w.get("title", "")
                    if sort_by == "Création":
                        return w.get("creationTime", "")
                    due = w.get("dueDate")
                    if not due:
                        return "9999"
                    return f"{due.get('year',9999)}-{due.get('month',12):02d}-{due.get('day',31):02d}"

                filtered.sort(key=sort_key)

                # Stats row
                pending_ct = len([w for w in work_items if w.get("_state") == "CREATED"])
                done_ct = len([w for w in work_items if w.get("_state") == "TURNED_IN"])
                graded_ct = len([w for w in work_items if w.get("_grade") is not None])

                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Total", len(work_items))
                mc2.metric("À faire", pending_ct, delta=f"-{pending_ct}" if pending_ct > 0 else None, delta_color="inverse")
                mc3.metric("Rendus", done_ct)
                mc4.metric("Notés", graded_ct)

                st.divider()

                for item in filtered[:show_count]:
                    render_assignment_card(item)

                if len(filtered) > show_count:
                    st.caption(f"+ {len(filtered) - show_count} autres devoirs masqués")

        with tab_ann:
            with st.spinner("Chargement des annonces..."):
                announcements = fetch_announcements(creds_json, sel_id)

            if not announcements:
                st.info("Aucune annonce pour ce cours.")
            else:
                st.caption(f"{len(announcements)} annonce(s) récente(s)")
                for ann in announcements:
                    render_announcement(ann)

        with tab_ai:
            st.markdown("#### 🤖 Analyse de ta charge de travail")
            st.caption("Claude analyse tous tes devoirs et te donne des recommandations personnalisées.")

            if st.button("✨ Analyser ma charge avec l'IA", use_container_width=True):
                # Collect all work from all courses
                all_work = []
                with st.spinner("Récupération de tous les devoirs..."):
                    for course in courses:
                        cw = fetch_coursework(creds_json, course["id"])
                        for item in cw:
                            item["_course_name"] = course.get("name", "")
                        all_work.extend(cw)

                with st.spinner("Claude analyse ta charge de travail..."):
                    analysis = analyze_workload_with_ai(all_work, profile)

                if analysis:
                    st.markdown(f"""
                    <div style="background:#0F1A10;border:1px solid #1D6A45;border-radius:12px;
                                padding:20px;margin:12px 0;border-left:4px solid #5DCAA5">
                        <div style="font-size:12px;color:#5DCAA5;margin-bottom:10px">🤖 Analyse MindFlow</div>
                        <div style="font-size:14px;color:#C0D4C0;line-height:1.7">{analysis.replace(chr(10), '<br>')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Impossible d'obtenir l'analyse IA. Vérifie ta clé API Anthropic.")

            # Vue globale tous cours
            st.divider()
            st.markdown("#### 📊 Vue globale — Tous les cours")
            if st.button("Charger tous les devoirs", use_container_width=True, key="load_all"):
                all_work = []
                with st.spinner("Chargement..."):
                    for course in courses:
                        cw = fetch_coursework(creds_json, course["id"])
                        for item in cw:
                            item["_course_name"] = course.get("name", "")
                        all_work.extend(cw)
                st.session_state.all_classroom_work = all_work

            if st.session_state.get("all_classroom_work"):
                all_work = st.session_state.all_classroom_work
                pending = [w for w in all_work if w.get("_state") == "CREATED"]
                overdue = []
                for w in pending:
                    due = w.get("dueDate")
                    if due:
                        try:
                            dt = _parse_date(f"{due.get('year')}-{due.get('month',1):02d}-{due.get('day',1):02d}T23:59:00Z")
                            if dt and dt < datetime.now(timezone.utc):
                                overdue.append(w)
                        except Exception:
                            pass

                c1, c2, c3 = st.columns(3)
                c1.metric("Total devoirs", len(all_work))
                c2.metric("En attente", len(pending))
                c3.metric("En retard 🔴", len(overdue))

                if overdue:
                    st.markdown("**🔴 Devoirs en retard :**")
                    for w in overdue:
                        st.markdown(f"- **{w.get('_course_name')}** — {w.get('title', '?')}")


def _show_connection_ui():
    """UI de connexion OAuth2 Google Classroom."""
    st.markdown("""
    <div style="background:#111118;border:1px solid #1A1A28;border-radius:16px;padding:32px;max-width:600px;margin:0 auto">
        <div style="text-align:center;margin-bottom:24px">
            <div style="font-size:48px;margin-bottom:12px">🎓</div>
            <h3 style="font-family:'Sora',sans-serif;color:#D0D0E8;margin-bottom:8px">Connecte ton Google Classroom</h3>
            <p style="color:#6060A0;font-size:14px">Accède à tes cours, devoirs et annonces directement depuis MindFlow</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    method = st.radio(
        "Méthode de connexion",
        ["🔑 Credentials JSON (recommandé)", "📋 Token manuel (avancé)"],
        horizontal=True
    )

    if method == "🔑 Credentials JSON (recommandé)":
        st.markdown("""
        **Comment obtenir ton fichier credentials.json :**
        1. Va sur [Google Cloud Console](https://console.cloud.google.com)
        2. Crée un projet → Active **Google Classroom API**
        3. Identifiants → **Créer des identifiants** → OAuth 2.0 Client IDs
        4. Type : **Application de bureau**
        5. Télécharge le JSON et colle son contenu ici
        """)

        creds_json_raw = st.text_area(
            "Colle le contenu de ton credentials.json",
            height=150,
            placeholder='{"installed": {"client_id": "...", "client_secret": "..."}}'
        )

        redirect_uri = st.text_input(
            "Redirect URI",
            value="urn:ietf:wg:oauth:2.0:oob",
            help="Laisse la valeur par défaut pour une app de bureau"
        )

        if st.button("🚀 Générer le lien d'autorisation", use_container_width=True):
            if not creds_json_raw.strip():
                st.error("Colle d'abord le credentials.json")
            else:
                try:
                    creds_data = json.loads(creds_json_raw)
                    key = "installed" if "installed" in creds_data else "web"
                    client_config = creds_data.get(key, creds_data)

                    flow = Flow.from_client_config(
                        {key: client_config},
                        scopes=SCOPES,
                        redirect_uri=redirect_uri
                    )
                    auth_url, state = flow.authorization_url(
                        access_type="offline",
                        include_granted_scopes="true",
                        prompt="consent"
                    )
                    st.session_state._oauth_flow_config = {
                        "client_config": {key: client_config},
                        "redirect_uri": redirect_uri,
                        "state": state
                    }
                    st.success("Lien généré !")
                    st.link_button("🔗 Ouvrir Google pour autoriser", auth_url)
                    st.markdown("Après autorisation, copie le **code** affiché par Google :")
                    auth_code = st.text_input("Code d'autorisation Google")
                    if st.button("✅ Valider le code") and auth_code:
                        _exchange_code(auth_code)
                except json.JSONDecodeError:
                    st.error("JSON invalide. Vérifie le format.")
                except Exception as e:
                    st.error(f"Erreur : {e}")

    else:
        st.markdown("""
        **Token manuel** — Si tu as déjà un access token Google valide :
        """)
        with st.form("manual_token_form"):
            access_token = st.text_input("Access Token", type="password")
            refresh_token = st.text_input("Refresh Token (optionnel)", type="password")
            client_id = st.text_input("Client ID")
            client_secret = st.text_input("Client Secret", type="password")

            if st.form_submit_button("✅ Connecter", use_container_width=True):
                if access_token and client_id:
                    st.session_state.classroom_creds = {
                        "token": access_token,
                        "refresh_token": refresh_token or None,
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "scopes": SCOPES
                    }
                    st.success("Connecté !")
                    st.rerun()
                else:
                    st.error("Access Token et Client ID sont requis.")


def _exchange_code(code: str):
    """Échange le code OAuth contre des tokens."""
    try:
        flow_config = st.session_state.get("_oauth_flow_config", {})
        client_config = flow_config.get("client_config", {})
        redirect_uri = flow_config.get("redirect_uri", "urn:ietf:wg:oauth:2.0:oob")

        key = "installed" if "installed" in client_config else "web"
        flow = Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=redirect_uri)
        flow.fetch_token(code=code)

        creds = flow.credentials
        st.session_state.classroom_creds = json.loads(creds.to_json())
        st.success("✅ Connecté à Google Classroom !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur lors de l'échange du code : {e}")


def _disconnect_btn():
    if st.button("🔌 Déconnecter", use_container_width=True):
        st.session_state.classroom_creds = None
        st.session_state.pop("selected_course_id", None)
        st.session_state.pop("all_classroom_work", None)
        fetch_courses.clear()
        fetch_coursework.clear()
        fetch_announcements.clear()
        st.rerun()
