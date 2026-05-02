from dataclasses import dataclass, field
from datetime import date


@dataclass(slots=True)
class ConversationTurn:
    role: str
    message: str


@dataclass(slots=True)
class ConversationContext:
    turns: list[ConversationTurn] = field(default_factory=list)
    last_discussed_date: date | None = None
    last_appointment_id: str | None = None


class InMemoryConversationContextStore:
    def __init__(self, max_turns: int = 12) -> None:
        self._max_turns = max_turns
        self._contexts: dict[str, ConversationContext] = {}

    async def get(self, user_id: str) -> ConversationContext:
        context = self._contexts.get(user_id)
        if context is None:
            context = ConversationContext()
            self._contexts[user_id] = context
        return context

    async def save(self, user_id: str, context: ConversationContext) -> None:
        if len(context.turns) > self._max_turns:
            context.turns = context.turns[-self._max_turns :]
        self._contexts[user_id] = context
