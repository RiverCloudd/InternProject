from .llm_client import BaseLLMClient


class Synthesizer:
    def __init__(self, llm_client: BaseLLMClient) -> None:
        self.llm_client = llm_client

    def synthesize(
        self,
        user_message: str,
        mode: str,
        agent_outputs: list[dict[str, str]],
        shared_state: dict[str, object],
    ) -> str:
        if mode in {"panel", "debate"}:
            lines = [f"{output['agent_id']}: {output['content']}" for output in agent_outputs]
            return (
                "Here is the stakeholder synthesis:\n\n"
                + "\n\n".join(lines)
                + "\n\nNext step: convert the strongest critique into one concrete revision of your deliverable."
            )

        if agent_outputs:
            return agent_outputs[0]["content"]
        return self.llm_client.generate(user_message)
