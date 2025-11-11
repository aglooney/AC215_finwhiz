"""
FastAPI entrypoint for the agentic user data processing service.

The service manages chat sessions, message history, and user-uploaded
financial documents (e.g., W-2 PDFs). It exposes a small REST API that
other microservices can call to record interactions and fetch enriched
context for downstream LLM prompts.
"""
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from . import models, schemas
from .db import get_db, init_db
from .services import context as context_service
from .services import storage as storage_service
from .services import extraction as extraction_service
from .services import extraction_1099 as extraction_1099_service
from .services import pdf_utils

app = FastAPI(title="Agentic User Data Processing Service")
logger = logging.getLogger(__name__)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup() -> None:
    """Ensure database tables exist when the service starts."""
    init_db()

#health check
@app.get("/health")
def health_check():
    return {"status": "ok"}



@app.post("/sessions/", response_model=schemas.SessionResponse)
def create_session(payload: schemas.SessionCreate, db: Session = Depends(get_db)):
    user = models.User.get_or_create(db, user_id=payload.user_id, external_id=str(payload.user_id))
    session = models.Session.create(db, user_id=user.id)
    return schemas.SessionResponse.from_orm(session)


@app.post("/sessions/{session_id}/messages", response_model=schemas.MessageResponse)
def append_message(
    session_id: str, payload: schemas.MessageCreate, db: Session = Depends(get_db)
):
    session = models.Session.get(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    message = models.Message.create(
        db,
        session_id=session_id,
        role=payload.role,
        content=payload.content,
    )
    return schemas.MessageResponse.from_orm(message)


@app.post("/sessions/{session_id}/w2", response_model=schemas.DocumentResponse)
async def upload_w2(
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    session = models.Session.get(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    contents = await file.read()
    flattened = pdf_utils.flatten_pdf(contents)

    gcs_uri = storage_service.save_document_bytes(
        session_id=session_id,
        filename=file.filename,
        contents=flattened,
        content_type=file.content_type,
    )
    extracted = await extraction_service.extract_w2_fields(flattened)

    document = models.Document.create(
        db,
        session_id=session_id,
        document_type="w2",
        gcs_uri=gcs_uri,
        raw_metadata=extracted.model_dump_json(),
    )
    return schemas.DocumentResponse.from_orm(document)

@app.post("/sessions/{session_id}/1099", response_model=schemas.DocumentResponse)
async def upload_1099(
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    session = models.Session.get(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    contents = await file.read()
    flattened = pdf_utils.flatten_pdf(contents)

    gcs_uri = storage_service.save_document_bytes(
        session_id=session_id,
        filename=file.filename,
        contents=flattened,
        content_type=file.content_type,
    )

    # Use the dedicated 1099 extractor
    extracted = await extraction_1099_service.extract_1099_fields(flattened)

    document = models.Document.create(
        db,
        session_id=session_id,
        document_type="1099",
        gcs_uri=gcs_uri,
        raw_metadata=extracted.model_dump_json(),
    )

    return schemas.DocumentResponse.from_orm(document)


@app.get("/sessions/{session_id}/context", response_model=schemas.SessionContext)
def get_session_context(session_id: str, db: Session = Depends(get_db)):
    session = models.Session.get(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = models.Message.latest_for_session(db, session_id=session_id, limit=20)
    documents = db.query(models.Document).filter(models.Document.session_id == session_id).all()
    return context_service.build_context(session=session, messages=messages, documents=documents)
