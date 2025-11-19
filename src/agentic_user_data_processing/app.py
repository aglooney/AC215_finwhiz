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
from .services import extraction_portfolio as extraction_portfolio_service
from .services import pdf_utils

from .services import yfinance_service
import json
from datetime import datetime


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


# health check
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/sessions/", response_model=schemas.SessionResponse)
def create_session(payload: schemas.SessionCreate, db: Session = Depends(get_db)):
    user = models.User.get_or_create(db, user_id=payload.user_id, external_id=str(payload.user_id))
    session = models.Session.create(db, user_id=user.id)
    return schemas.SessionResponse.from_orm(session)


@app.post("/sessions/{session_id}/messages", response_model=schemas.MessageResponse)
def append_message(session_id: str, payload: schemas.MessageCreate, db: Session = Depends(get_db)):
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


@app.post("/sessions/{session_id}/portfolio", response_model=schemas.DocumentResponse)
async def upload_portfolio(
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and process a Fidelity portfolio summary for a session."""
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

    # Use the dedicated portfolio extractor
    extracted = await extraction_portfolio_service.extract_portfolio_fields(flattened)

    document = models.Document.create(
        db,
        session_id=session_id,
        document_type="portfolio",
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

@app.get("/sessions/{session_id}/portfolio/live")
def get_live_portfolio(session_id: str, db: Session = Depends(get_db)):
    """
    Get live portfolio data with current market prices.
    Follows the same pattern as get_session_context endpoint.
    """
    logger.info(f"[get_live_portfolio] Fetching live portfolio for session {session_id}")
    
    session_obj = models.Session.get(db, session_id)
    if session_obj is None:
        logger.warning(f"[get_live_portfolio] Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get the latest portfolio document (matches Document.latest_for_session pattern)
    portfolio_doc = db.query(models.Document).filter(
        models.Document.session_id == session_id,
        models.Document.document_type == "portfolio"
    ).order_by(models.Document.created_at.desc()).first()
    
    if not portfolio_doc or not portfolio_doc.raw_metadata:
        logger.warning(f"[get_live_portfolio] No portfolio found for session {session_id}")
        raise HTTPException(status_code=404, detail="No portfolio found for this session")
    
    try:
        portfolio_data = json.loads(portfolio_doc.raw_metadata)
        holdings = portfolio_data.get('holdings', [])
        
        if not holdings:
            logger.info(f"[get_live_portfolio] No holdings in portfolio for session {session_id}")
            return {
                "message": "No holdings found in portfolio",
                "total_current_value": 0,
                "total_original_value": portfolio_data.get('total_portfolio_value', 0),
                "holdings": []
            }
        
        logger.info(f"[get_live_portfolio] Processing {len(holdings)} holdings")
        live_data = yfinance_service.get_portfolio_live_data(holdings)
        
        # Include original portfolio metadata
        live_data['account_name'] = portfolio_data.get('account_name')
        live_data['account_number'] = portfolio_data.get('account_number')
        live_data['account_type'] = portfolio_data.get('account_type')
        live_data['statement_date'] = portfolio_data.get('statement_date')
        
        logger.info(f"[get_live_portfolio] Successfully calculated live portfolio value: ${live_data['total_current_value']}")
        return live_data
        
    except json.JSONDecodeError as e:
        logger.error(f"[get_live_portfolio] Invalid JSON in portfolio metadata: {e}")
        raise HTTPException(status_code=500, detail="Invalid portfolio data format")
    except Exception as e:
        logger.error(f"[get_live_portfolio] Error processing portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing portfolio: {str(e)}")


@app.get("/sessions/{session_id}/portfolio/analytics")
def get_portfolio_analytics(session_id: str, db: Session = Depends(get_db)):
    """Get portfolio analytics and insights."""
    logger.info(f"[get_portfolio_analytics] Fetching analytics for session {session_id}")
    
    session_obj = models.Session.get(db, session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get the latest portfolio document
    portfolio_doc = db.query(models.Document).filter(
        models.Document.session_id == session_id,
        models.Document.document_type == "portfolio"
    ).order_by(models.Document.created_at.desc()).first()
    
    if not portfolio_doc or not portfolio_doc.raw_metadata:
        raise HTTPException(status_code=404, detail="No portfolio found for this session")
    
    try:
        portfolio_data = json.loads(portfolio_doc.raw_metadata)
        holdings = portfolio_data.get('holdings', [])
        
        # Get live data first
        live_data = yfinance_service.get_portfolio_live_data(holdings)
        
        # Get analytics
        analytics = yfinance_service.get_portfolio_analytics(live_data['holdings'])
        
        logger.info(f"[get_portfolio_analytics] Analytics calculated for {len(live_data['holdings'])} holdings")
        return analytics
        
    except Exception as e:
        logger.error(f"[get_portfolio_analytics] Error calculating analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing analytics: {str(e)}")


@app.get("/market/quote/{ticker}")
def get_market_quote(ticker: str):
    """Get current quote for a specific ticker."""
    logger.info(f"[get_market_quote] Fetching quote for {ticker}")
    
    quote = yfinance_service.get_stock_quote(ticker.upper())
    if not quote:
        logger.warning(f"[get_market_quote] Unable to fetch data for {ticker}")
        raise HTTPException(status_code=404, detail=f"Unable to fetch data for {ticker}")
    
    return quote


@app.get("/market/indices")
def get_market_indices():
    """Get current data for major market indices."""
    logger.info("[get_market_indices] Fetching market indices")
    
    indices = yfinance_service.get_market_indices()
    if not indices:
        logger.error("[get_market_indices] Failed to fetch any market indices")
        raise HTTPException(status_code=500, detail="Unable to fetch market indices")
    
    return {"indices": indices, "updated_at": datetime.now().isoformat()}


@app.get("/market/history/{ticker}")
def get_stock_history(ticker: str, period: str = "1mo"):
    """
    Get historical price data for a stock.
    
    Query params:
        period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    logger.info(f"[get_stock_history] Fetching {period} history for {ticker}")
    
    history = yfinance_service.get_stock_history(ticker.upper(), period)
    if not history:
        logger.warning(f"[get_stock_history] Unable to fetch history for {ticker}")
        raise HTTPException(status_code=404, detail=f"Unable to fetch history for {ticker}")
    
    return {"ticker": ticker, "period": period, "history": history}






    
