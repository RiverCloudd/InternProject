from .agent_loader import AgentLoader


class DirectorAgent:
    """Rule-based supervisor that decides which co-workers should be consulted."""

    COLLABORATOR_RULES = {
        "gucci_group_ceo": {
            "gucci_group_chro": ["competency", "360", "feedback", "coaching", "mobility", "succession"],
            "regional_comms_manager": ["rollout", "regional", "communication", "trainer", "adoption"],
        },
        "gucci_group_chro": {
            "gucci_group_ceo": ["strategy", "dna", "ceo", "executive", "autonomy", "standardize", "non-negotiable"],
            "regional_comms_manager": ["rollout", "regional", "communication", "trainer", "localization", "adoption"],
        },
        "regional_comms_manager": {
            "gucci_group_ceo": ["strategy", "dna", "autonomy", "standardize", "executive"],
            "gucci_group_chro": ["competency", "360", "feedback", "coaching", "mobility", "succession"],
        },
    }

    MODULE_COLLABORATORS = {
        "group_dna": ["gucci_group_ceo"],
        "competency_model": ["gucci_group_chro", "gucci_group_ceo"],
        "feedback_coaching": ["gucci_group_chro"],
        "talent_mobility": ["gucci_group_chro", "gucci_group_ceo"],
        "regional_rollout": ["regional_comms_manager", "gucci_group_chro"],
        "executive_recommendation": ["gucci_group_ceo"],
    }

    def __init__(self, loader: AgentLoader) -> None:
        self.loader = loader

    def plan(
        self,
        primary_agent_id: str,
        user_message: str,
        supervisor_signal: dict[str, object],
    ) -> dict[str, object]:
        normalized = user_message.lower()
        module = str(supervisor_signal.get("module", "orientation"))
        collaborators: list[str] = []

        for collaborator, keywords in self.COLLABORATOR_RULES.get(primary_agent_id, {}).items():
            if any(keyword in normalized for keyword in keywords):
                collaborators.append(collaborator)

        for collaborator in self.MODULE_COLLABORATORS.get(module, []):
            if collaborator != primary_agent_id and collaborator not in collaborators:
                collaborators.append(collaborator)

        if supervisor_signal.get("challenge_needed") and primary_agent_id != "gucci_group_ceo":
            if "gucci_group_ceo" not in collaborators:
                collaborators.insert(0, "gucci_group_ceo")

        collaborators = collaborators[:2]
        notes = [
            self._advisory_note(collaborator, module, normalized)
            for collaborator in collaborators
        ]

        return {
            "primary_agent_id": primary_agent_id,
            "collaborators": collaborators,
            "notes": notes,
        }

    def _advisory_note(self, agent_id: str, module: str, normalized_message: str) -> dict[str, str]:
        agent = self.loader.load(agent_id)
        if agent_id == "gucci_group_ceo":
            note = (
                "Pressure-test Group non-negotiables vs brand-level autonomy. Ask what strategic outcome "
                "the leadership system improves and what tradeoff the learner is choosing."
            )
        elif agent_id == "regional_comms_manager":
            note = (
                "Check rollout realism: region, audience, channel, trainer readiness, employee resistance, "
                "and feedback loop. One global narrative still needs local execution."
            )
        else:
            note = (
                "Anchor the design in observable competencies, development-oriented 360 feedback, coaching "
                "follow-through, trust, and internal mobility."
            )

        if module == "regional_rollout" and agent_id == "gucci_group_chro":
            note = (
                "Make sure regional rollout still protects HR integrity: manager enablement, confidentiality, "
                "development follow-through, and consistent competency definitions."
            )
        if module == "competency_model" and agent_id == "gucci_group_ceo":
            note = (
                "Check that the competency model does not become HR jargon. It should express Group-level "
                "leadership non-negotiables while preserving brand-specific examples."
            )

        return {
            "agent_id": agent_id,
            "agent_name": agent.display_name,
            "role": agent.role,
            "advisory_note": note,
        }
