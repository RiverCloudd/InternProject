import re

from .memory import SessionState


class Supervisor:
    MODULE_KEYWORDS = {
        "group_dna": ["dna", "strategy", "culture", "non-negotiable", "autonomy"],
        "competency_model": ["competency", "behavior", "vision", "entrepreneurship", "passion", "trust"],
        "feedback_coaching": ["360", "feedback", "coaching", "survey", "questionnaire"],
        "regional_rollout": ["regional", "communication", "comms", "trainer", "rollout", "localization", "adoption"],
        "talent_mobility": ["mobility", "rotation", "succession"],
        "executive_recommendation": ["ceo", "executive", "recommendation", "rollout", "kpi"],
    }

    DELIVERABLE_KEYWORDS = {
        "group_dna": ["dna"],
        "competency_model": ["competency", "behavior indicator", "leadership model"],
        "360_feedback_plan": ["360", "feedback"],
        "coaching_program": ["coaching"],
        "talent_mobility_plan": ["mobility", "rotation", "succession"],
        "regional_rollout_plan": ["regional", "rollout", "trainer", "communication"],
        "measurement_plan": ["kpi", "measurement", "dashboard", "adoption"],
    }

    def analyze(
        self,
        user_message: str,
        state: SessionState,
        safety_flags: dict[str, bool],
        agent_id: str = "gucci_group_chro",
    ) -> dict[str, object]:
        normalized = user_message.lower()
        module = self._detect_module(normalized) or state.current_module
        vague = self._is_vague(normalized)
        completed = self._detect_completed_deliverables(normalized)
        status = self._status(vague, safety_flags)
        return {
            "agent_id": agent_id,
            "status": status,
            "module": module,
            "stuck": vague or safety_flags["asks_final_work"],
            "vague": vague,
            "challenge_needed": self._needs_brand_autonomy_challenge(normalized),
            "completed_deliverables": completed,
            "redirect_needed": safety_flags["needs_redirect"],
            "prompt_extraction": safety_flags.get("prompt_extraction", False),
        }

    def _status(self, vague: bool, safety_flags: dict[str, bool]) -> str:
        if safety_flags.get("prompt_extraction"):
            return "safety_violation"
        if safety_flags["asks_final_work"]:
            return "learning_guardrail"
        if safety_flags["needs_redirect"]:
            return "off_track"
        if vague:
            return "stuck"
        return "on_track"

    def _detect_module(self, normalized: str) -> str | None:
        for module, keywords in self.MODULE_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                return module
        return None

    def _is_vague(self, normalized: str) -> bool:
        cleaned = re.sub(r"[^a-z0-9 ]", " ", normalized).strip()
        vague_phrases = ["help me", "i am stuck", "what should i do", "give me idea", "not sure"]
        return len(cleaned.split()) <= 4 or any(phrase in cleaned for phrase in vague_phrases)

    def _needs_brand_autonomy_challenge(self, normalized: str) -> bool:
        standardize_terms = ["same for every brand", "one model for all", "fully standardize", "global template"]
        autonomy_terms = ["autonomy", "brand identity", "local", "region"]
        return any(term in normalized for term in standardize_terms) and not any(term in normalized for term in autonomy_terms)

    def _detect_completed_deliverables(self, normalized: str) -> list[str]:
        completion_terms = ["completed", "finished", "drafted", "done", "finalized", "i have", "i've"]
        if not any(term in normalized for term in completion_terms):
            return []
        return [
            name
            for name, keywords in self.DELIVERABLE_KEYWORDS.items()
            if any(keyword in normalized for keyword in keywords)
        ]
