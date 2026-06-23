from dataclasses import dataclass, asdict
from uuid import uuid4


@dataclass
class BusMessage:
    message_id: str
    session_id: str
    from_agent: str
    to_agent: str
    visibility: str
    message_type: str
    content: str
    requires_response: bool = False


class MessageBus:
    def __init__(self) -> None:
        self._messages: list[BusMessage] = []

    def publish(
        self,
        session_id: str,
        from_agent: str,
        to_agent: str,
        visibility: str,
        message_type: str,
        content: str,
        requires_response: bool = False,
    ) -> dict[str, object]:
        message = BusMessage(
            message_id=str(uuid4()),
            session_id=session_id,
            from_agent=from_agent,
            to_agent=to_agent,
            visibility=visibility,
            message_type=message_type,
            content=content,
            requires_response=requires_response,
        )
        self._messages.append(message)
        return asdict(message)

    def list_session(self, session_id: str, visibility: str | None = None) -> list[dict[str, object]]:
        messages = [message for message in self._messages if message.session_id == session_id]
        if visibility:
            messages = [message for message in messages if message.visibility == visibility]
        return [asdict(message) for message in messages]
