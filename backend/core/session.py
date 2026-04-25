from typing import Dict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from datetime import datetime, timedelta

# In-memory session store (substituir por Redis em produção)
_sessions: Dict[str, dict] = {}
SESSION_TTL_MINUTES = 60


def get_session(session_id: str) -> List[BaseMessage]:
    session = _sessions.get(session_id)
    if not session:
        return []
    if datetime.now() > session["expires_at"]:
        del _sessions[session_id]
        return []
    return session["messages"]


def save_session(session_id: str, messages: List[BaseMessage]):
    _sessions[session_id] = {
        "messages": messages,
        "expires_at": datetime.now() + timedelta(minutes=SESSION_TTL_MINUTES),
        "updated_at": datetime.now(),
    }


def clear_session(session_id: str):
    _sessions.pop(session_id, None)


def append_messages(session_id: str, new_messages: List[BaseMessage]) -> List[BaseMessage]:
    history = get_session(session_id)
    updated = history + new_messages
    # Manter no máximo 50 mensagens para não explodir o contexto
    if len(updated) > 50:
        updated = updated[-50:]
    save_session(session_id, updated)
    return updated
