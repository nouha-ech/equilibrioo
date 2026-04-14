

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
import json
import os

class WellnessCoachAgent:
    def __init__(self, api_key: str):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-latest",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            temperature=0.7,
            max_tokens=3000
        )
        self.conversation_history = []

    def _clean_json(self, text: str) -> dict:
        
        if "```" in text:
            text = text.split("```")[1].split("```")[0]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())

    def generate_routine(self, student_profile: dict) -> dict:
       

        # ── Étape 1: Analyse ─────────────────────────────
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un coach en bien-être spécialisé pour les étudiants.
Analyse le profil et retourne un JSON structuré."""),

            ("human", """Profil:
- Nom: {name}
- Filière: {field}
- Niveau: {year}
- Objectif: {goal}
- Préoccupations: {concerns}
- Points forts: {strengths}
- Points faibles: {weaknesses}
- Habitudes: {habits}
- Temps dispo: {available_time}
- Réveil: {wake_time}
- Sommeil: {sleep_time}

Retourne JSON:
{
  "needs": [],
  "risk_factors": [],
  "recommended_focus": ""
}""")
        ])

        analysis_chain = analysis_prompt | self.llm
        analysis_response = analysis_chain.invoke(student_profile)
        analysis = self._clean_json(analysis_response.content)

       
        routine_prompt = ChatPromptTemplate.from_messages([
            ("system", "Tu es un coach. Crée une routine réaliste. JSON uniquement."),

            ("human", """Besoins: {needs}
Risques: {risk_factors}
Focus: {recommended_focus}

Crée JSON:
{
  "routine_name": "",
  "morning": [],
  "study_blocks": [],
  "breaks": [],
  "evening": [],
  "weekly_goals": [],
  "motivation_message": "",
  "difficulty_level": "",
  "estimated_impact": {}
}""")
        ])

        routine_chain = routine_prompt | self.llm
        routine_response = routine_chain.invoke({
            "needs": analysis.get("needs", []),
            "risk_factors": analysis.get("risk_factors", []),
            "recommended_focus": analysis.get("recommended_focus", "")
        })

        routine = self._clean_json(routine_response.content)
        routine["analysis"] = analysis

        return routine

    def chat(self, user_message: str, student_profile: dict) -> str:
        """Chat avec mémoire simple"""

        system_context = f"""Tu es un coach bien-être pour étudiants.
Profil:
- Nom: {student_profile.get('name')}
- Objectif: {student_profile.get('goal')}
- Problèmes: {student_profile.get('concerns')}
Réponds en français, empathique et pratique."""

        messages = [HumanMessage(content=system_context)]

        # Historique
        for msg in self.conversation_history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_message))

        response = self.llm.invoke(messages)
        assistant_message = response.content

        # Sauvegarde
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": assistant_message})

        return assistant_message

    def adapt_routine(self, current_routine: dict, feedback: str, student_profile: dict) -> dict:
        """Adapte la routine selon feedback"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Adapte la routine. Réponds en JSON."),

            ("human", """Routine: {routine}
Feedback: {feedback}

Retourne JSON complet avec 'adaptation_note'""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "routine": json.dumps(current_routine, ensure_ascii=False),
            "feedback": feedback
        })

        return self._clean_json(response.content)