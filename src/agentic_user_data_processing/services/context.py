"""
Assemble a compact context object for downstream LLM calls.
"""
from typing import Iterable, Optional

from .. import models, schemas


def build_context(
    *,
    session: models.Session,
    messages: Iterable,
    document: Optional,
) -> schemas.SessionContext:
    """
    Convert SQLAlchemy models into serializable context for the query pipeline.
    """
    # messages is expected in newest-first order; present oldest-first to LLM.
    message_list = list(messages)[::-1]

    recent_messages = [
        schemas.ChatTurn(role=msg.role, content=msg.content, created_at=msg.created_at)
        for msg in message_list
    ]

    w2_fields = None
    if document and document.raw_metadata:
        w2_fields = schemas.W2Fields.model_validate_json(document.raw_metadata)

    summary = None  # Placeholder: future work can summarize long transcripts.

    return schemas.SessionContext(
        session_id=session.id,
        user_id=session.user_id,
        recent_messages=recent_messages,
        w2_fields=w2_fields,
        summary=summary,
    )
