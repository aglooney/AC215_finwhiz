"""
Assemble a compact context object for downstream LLM calls.
"""
from typing import Iterable, Optional

from .. import models, schemas

def build_context(*, session: models.Session, messages, document):
    """
    Convert SQLAlchemy models into serializable context for the query pipeline.
    """

    message_list = list(messages)[::-1]

    recent_messages = [
        schemas.ChatTurn(role=msg.role, content=msg.content, created_at=msg.created_at)
        for msg in message_list
    ]

    w2_fields = None
    form1099_fields = None

    if document and document.raw_metadata:
        doc_type = document.document_type.lower()
        if doc_type == "w2":
            w2_fields = schemas.W2Fields.model_validate_json(document.raw_metadata)
        elif doc_type in ["1099", "1099-int"]:
            form1099_fields = schemas.Form1099Fields.model_validate_json(document.raw_metadata)

    return schemas.SessionContext(
        session_id=str(session.id),
        user_id=str(session.user_id),
        recent_messages=recent_messages,
        w2_fields=w2_fields,
        form1099_fields=form1099_fields,
        summary=None,
    )