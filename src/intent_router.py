class IntentRouter:
    INTENT_KEYWORDS = {
        "group_dna": ["dna", "strategy", "culture", "autonomy", "non-negotiable", "ceo"],
        "competency_framework": ["competency", "behavior", "vision", "entrepreneurship", "passion", "trust"],
        "feedback_coaching": ["360", "feedback", "coaching", "survey", "rater"],
        "talent_mobility": ["mobility", "succession", "rotation"],
        "regional_rollout": ["regional", "rollout", "communication", "trainer", "localization", "adoption"],
    }

    PRIMARY_BY_INTENT = {
        "group_dna": "gucci_group_ceo",
        "competency_framework": "gucci_group_chro",
        "feedback_coaching": "gucci_group_chro",
        "talent_mobility": "gucci_group_chro",
        "regional_rollout": "regional_comms_manager",
    }

    SUPPORTING_BY_INTENT = {
        "group_dna": ["gucci_group_chro"],
        "competency_framework": ["gucci_group_ceo"],
        "feedback_coaching": ["regional_comms_manager"],
        "talent_mobility": ["gucci_group_ceo"],
        "regional_rollout": ["gucci_group_chro"],
    }

    def route(
        self,
        user_message: str,
        target_agent_id: str | None,
        shared_state: dict[str, object],
        retrieved_context: list[dict],
    ) -> dict[str, object]:
        intent = self._detect_intent(user_message)
        primary_agent = target_agent_id or self.PRIMARY_BY_INTENT.get(intent, "gucci_group_chro")
        supporting_agents = [
            agent_id
            for agent_id in self.SUPPORTING_BY_INTENT.get(intent, [])
            if agent_id != primary_agent
        ]

        if target_agent_id and primary_agent == target_agent_id:
            natural_primary = self.PRIMARY_BY_INTENT.get(intent)
            if natural_primary and natural_primary != target_agent_id and natural_primary not in supporting_agents:
                supporting_agents.insert(0, natural_primary)

        return {
            "intent": intent,
            "primary_agent": primary_agent,
            "supporting_agents": supporting_agents[:2],
            "rag_query": self._build_rag_query(user_message, intent, shared_state),
        }

    def _detect_intent(self, user_message: str) -> str:
        normalized = user_message.lower()
        for intent, keywords in self.INTENT_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                return intent
        return "general_guidance"

    def _build_rag_query(self, user_message: str, intent: str, shared_state: dict[str, object]) -> str:
        return " ".join(
            str(item)
            for item in [
                user_message,
                intent,
                shared_state.get("current_module"),
                shared_state.get("active_deliverable"),
            ]
            if item
        )
