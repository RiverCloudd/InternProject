from typing import Any


class ToolRouter:
    KEYWORD_HINTS = {
        "competency": ["competency", "behavior", "vision", "entrepreneurship", "passion", "trust"],
        "feedback": ["360", "feedback", "survey", "rater"],
        "coaching": ["coaching", "coach", "habit"],
        "mobility": ["mobility", "succession", "rotation"],
        "strategy": ["strategy", "dna", "standardize", "autonomy", "tradeoff"],
        "rollout": ["rollout", "regional", "communication", "trainer", "localization", "adoption"],
    }

    def __init__(self, tool_catalog: dict[str, Any]) -> None:
        tools = tool_catalog.get("tools", [])
        self.tools = tools if isinstance(tools, list) else []

    def tools_for_agent(self, agent_id: str) -> dict[str, Any]:
        allowed = [
            tool
            for tool in self.tools
            if isinstance(tool, dict) and agent_id in tool.get("allowed_agents", [])
        ]
        return {"tools": allowed}

    def suggest(self, agent_id: str, user_message: str) -> list[str]:
        allowed = self.tools_for_agent(agent_id)["tools"]
        normalized = user_message.lower()
        matched_topics = {
            topic
            for topic, keywords in self.KEYWORD_HINTS.items()
            if any(keyword in normalized for keyword in keywords)
        }

        suggestions: list[str] = []
        for tool in allowed:
            if not isinstance(tool, dict):
                continue
            tool_id = str(tool.get("tool_id", ""))
            if any(topic in tool_id for topic in matched_topics):
                suggestions.append(tool_id)

        if suggestions:
            return suggestions[:3]
        return [str(tool.get("tool_id")) for tool in allowed[:2] if isinstance(tool, dict)]
