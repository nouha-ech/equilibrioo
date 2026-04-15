#  EduWell — AI Agent de Coaching & Bien-être Étudiant

EduWell est une application **AI Agent intelligente multi-modules** conçue pour accompagner les étudiants dans :

-  Gestion du stress en temps réel
-  Coaching personnalisé IA
-  Suivi des cours via un module Classroom
-  Analyse comportementale et émotionnelle
-  Génération de routines intelligentes

Le projet combine **LangChain + Anthropic Claude + Streamlit + classroom API** pour créer une expérience d’assistant étudiant complet.

---

#  Démo du projet

> EduWell agit comme un **AI Copilot étudiant** disponible 24/7 pour :
- analyser le stress
- proposer des solutions immédiates
- organiser les études
- suivre les cours
- améliorer la productivité

---

#  Architecture du projet

## Architecture

```
student_wellness_coach/
├── app.py                          # Point d'entrée Streamlit
├── requirements.txt
├── agents/
│   ├── stress_detector.py          # Agent détection stress (LangChain + Claude)
│   └── wellness_coach.py           # Agent coach bien-être (LangChain + Claude)
├── pages/
│   ├── onboarding.py               # Profil étudiant
│   ├── dashboard.py                # Vue d'ensemble
│   ├── chat.py                     # Chat + analyse stress temps réel
│   ├── routine.py                  # Routine personnalisée
│   └── profile.py                  # Gestion du profil
└── utils/
    └── session_state.py            # Gestion de l'état Streamlit
```

## Pipeline Agentic AI
---

# 🤖 Technologies utilisées

## 🧠 Intelligence artificielle
- **LangChain** → orchestration des agents IA
- **Anthropic Claude API** → modèle de langage principal
- Prompt engineering avancé pour coaching et analyse émotionnelle

## 🎨 Frontend
- **Streamlit** → interface utilisateur interactive et rapide

## 🎓 Classroom System
- **Classroom API (custom module)** →
  - suivi académique intelligent
  - intégration avec les agents IA

---

# 🤖 Architecture des Agents IA
---  

### StressDetectorAgent
1. **Quick scan** — Score stress rapide (0-100) sur chaque message
2. **Full analysis** — Analyse complète si score ≥ 50 :
   - Indicateurs de stress détectés
   - Stresseur primaire identifié
   - État émotionnel
   - Techniques de gestion adaptées au profil
   - Message empathique personnalisé

### WellnessCoachAgent
1. **Étape 1** — Analyse du profil → identification des besoins prioritaires
2. **Étape 2** — Construction de la routine quotidienne structurée
3. **Chat conversationnel** — Maintien du contexte sur 10 messages
4. **Adaptation** — Modification de la routine selon les retours

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

add ANTROPIC_API to .env file add client_secret.json file to the project folder

### Steps to get client_secret.json
Go to the Google Cloud Console.

Select your project (or create a new one).

Enable the Google Classroom API.
[link](https://console.cloud.google.com)
In the left menu, go to APIs & Services → Credentials.

Click Create Credentials → OAuth client ID.

Application type: Desktop app (since you’re running locally).

Download the JSON file. It will look like client_secret_xxx.json.

Rename it to client_secret.json (or update your script to match the filename).

Place it in the same directory as your Streamlit script 


## Fonctionnalités

- ✅ Onboarding profil étudiant complet (filière, niveau, objectifs, habitudes)
- ✅ Détection stress en temps réel dans le chat (score 0-100)
- ✅ Analyse complète du stress avec techniques adaptées (CBT, mindfulness, respiration)
- ✅ Coaching conversationnel avec mémoire contextuelle
- ✅ Génération de routine quotidienne personnalisée (pipeline 2 étapes)
- ✅ Adaptation de la routine selon les retours
- ✅ Dashboard avec métriques et historique
- ✅ Interface dark mode soignée

---