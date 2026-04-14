from langchain_anthropic import ChatAnthropic # type: ignore
from langchain_core.prompts import ChatPromptTemplate # pyright: ignore[reportMissingImports]
from langchain_core.output_parsers import PydanticOutputParser # pyright: ignore[reportMissingImports]
from langchain_core.runnables import RunnablePassthrough # pyright: ignore[reportMissingImports]
from pydantic import BaseModel, Field # pyright: ignore[reportMissingImports]
from typing import Optional
import json
import os


class StressAnalysis(BaseModel):
    stress_level: str = Field(description="low | medium | high | critical")
    stress_score: int = Field(description="Score de stress 0-100")
    stress_indicators: list[str] = Field(description="Indicateurs détectés dans le message")
    primary_stressor: str = Field(description="Source principale du stress")
    emotional_state: str = Field(description="État émotionnel global")
    techniques: list[dict] = Field(description="Liste de techniques adaptées [{nom, description, durée, type}]")
    urgent_support_needed: bool = Field(description="Si support urgent requis")
    empathy_message: str = Field(description="Message empathique personnalisé pour l'étudiant")


# ── Agent ──
class StressDetectorAgent:
    def __init__(self, api_key: str):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            temperature=0.3,
            max_tokens=2000
        )
        self.parser = PydanticOutputParser(pydantic_object=StressAnalysis)
        self._build_chain()

    def _build_chain(self):
        system_prompt = """Tu es un expert en psychologie du bien-être étudiant et en détection des signaux de stress.
Ton rôle est d'analyser les messages des étudiants pour détecter les niveaux de stress, 
les facteurs déclencheurs, et proposer des techniques de gestion adaptées au contexte académique.

Contexte étudiant : {student_context}

Analyse le message suivant et réponds UNIQUEMENT avec un JSON valide correspondant à ce format :
{format_instructions}

Techniques disponibles selon le niveau de stress :
- LOW: Mindfulness rapide, journaling, micro-pause
- MEDIUM: Respiration 4-7-8, technique Pomodoro, marche consciente, EFT tapping
- HIGH: RAINSTORM technique, grounding 5-4-3-2-1, appel à un proche, TCC exercice
- CRITICAL: Ressources d'urgence, hotline bien-être, consultation psychologue universitaire

Pour le profil de l'étudiant, adapte les techniques à son domaine ({field}) et ses préoccupations."""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Message de l'étudiant : {message}")
        ])

        self.chain = (
            {
                "message": RunnablePassthrough(),
                "student_context": lambda x: x.get("context", "Étudiant universitaire"),
                "field": lambda x: x.get("field", "Non spécifié"),
                "format_instructions": lambda x: self.parser.get_format_instructions()
            }
            | self.prompt
            | self.llm
        )

    def analyze(self, message: str, student_profile: dict = None) -> StressAnalysis:
        """Analyse le stress dans un message étudiant."""
        context = ""
        field = "Non spécifié"

        if student_profile:
            context = f"""
            - Nom: {student_profile.get('name', 'Étudiant')}
            - Filière: {student_profile.get('field', 'Non spécifié')}
            - Niveau: {student_profile.get('year', 'Non spécifié')}
            - Objectif: {student_profile.get('goal', 'Non spécifié')}
            - Points forts: {', '.join(student_profile.get('strengths', []))}
            - Points faibles: {', '.join(student_profile.get('weaknesses', []))}
            - Préoccupations: {student_profile.get('concerns', 'Non spécifié')}
            """
            field = student_profile.get('field', 'Non spécifié')

        response = self.chain.invoke({
            "message": message,
            "context": context,
            "field": field
        })

        raw_text = response.content
        
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        data = json.loads(raw_text)
        return StressAnalysis(**data)

    def quick_scan(self, message: str) -> dict:
        """Scan rapide pour badge de stress dans le chat."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Tu es un détecteur de stress. Réponds UNIQUEMENT avec un JSON: {\"level\": \"low|medium|high|critical\", \"score\": 0-100}"),
            ("human", "{message}")
        ])
        chain = prompt | self.llm
        response = chain.invoke({"message": message})
        raw = response.content
        if "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        return json.loads(raw)
