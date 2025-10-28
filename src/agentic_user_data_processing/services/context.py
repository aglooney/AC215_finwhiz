import json
import logging
from .. import schemas, models  # adjust import as needed

logger = logging.getLogger(__name__)

def build_context(*, session, messages, documents):
    #build messages
    try:
        message_list = list(messages)[::-1] if messages else []
        recent_messages = [
            schemas.ChatTurn(
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in message_list
        ]
    except Exception as e:
        logger.exception(f"Failed building recent_messages: {e}")
        raise

    # build doc files
    w2_fields = None
    form1099_fields = None
    try:
        for doc in documents or []:
            if not doc.raw_metadata:
                continue
            logger.info(f"Processing document {doc.id} type={doc.document_type}")
            doc_type = (doc.document_type or "").lower()

            if doc_type == "w2":
                w2_fields = schemas.W2Fields.model_validate_json(doc.raw_metadata)
            elif doc_type in {"1099", "1099-int"}:
                form1099_fields = schemas.Form1099Fields.model_validate_json(doc.raw_metadata)
    except Exception as e:
        logger.exception(f"Failed parsing documents: {e}")
        raise

    # build session context
    try:
        ctx = schemas.SessionContext(
            session_id=str(session.id),
            user_id=str(session.user_id),
            recent_messages=recent_messages or [],
            w2_fields=w2_fields,
            form1099_fields=form1099_fields,
            summary=None,
        )
        logger.info("Successfully built SessionContext")
        return ctx
    except Exception as e:
        logger.exception(f"Failed building SessionContext: {e}")
        raise
