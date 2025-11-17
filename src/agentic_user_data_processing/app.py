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

import os
from .services import yfinance_service
import json
from datetime import datetime
import re

from pydantic import BaseModel
import requests

class CustomAllocation(BaseModel):
    stocks: int
    bonds: int
    cash: int

class AssetTarget(BaseModel):
    ticker: str
    target_percent: float
    current_percent: float = 0
    action: str  # "buy", "sell", "hold"
    shares_to_trade: float = 0
    dollar_amount: float = 0

class AssetAllocationTarget(BaseModel):
    targets: list[AssetTarget]
    cash_target_percent: float = 0
    ai_rationale: str = ""

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

# ==================== Custom Allocation Endpoints ====================

@app.post("/sessions/{session_id}/allocation")
def save_custom_allocation(
    session_id: str, 
    allocation: CustomAllocation,
    db: Session = Depends(get_db)
):
    """Save user's custom portfolio allocation from AI recommendation."""
    logger.info(f"[save_custom_allocation] Saving allocation for session {session_id}: {allocation}")
    
    session_obj = models.Session.get(db, session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Store as a special document type
    allocation_data = allocation.model_dump_json()
    
    # Check if allocation already exists
    existing = db.query(models.Document).filter(
        models.Document.session_id == session_id,
        models.Document.document_type == "custom_allocation"
    ).first()
    
    if existing:
        # Update existing
        existing.raw_metadata = allocation_data
        db.commit()
        logger.info(f"[save_custom_allocation] Updated existing allocation")
    else:
        # Create new
        models.Document.create(
            db,
            session_id=session_id,
            document_type="custom_allocation",
            gcs_uri="internal://custom_allocation",
            raw_metadata=allocation_data
        )
        logger.info(f"[save_custom_allocation] Created new allocation")
    
    return {"status": "success", "allocation": allocation}


@app.get("/sessions/{session_id}/allocation")
def get_custom_allocation(session_id: str, db: Session = Depends(get_db)):
    """Get user's custom portfolio allocation if exists."""
    logger.info(f"[get_custom_allocation] Getting allocation for session {session_id}")
    
    session_obj = models.Session.get(db, session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    allocation_doc = db.query(models.Document).filter(
        models.Document.session_id == session_id,
        models.Document.document_type == "custom_allocation"
    ).first()
    
    if not allocation_doc or not allocation_doc.raw_metadata:
        raise HTTPException(status_code=404, detail="No custom allocation found")
    
    try:
        allocation_data = json.loads(allocation_doc.raw_metadata)
        return {"allocation": allocation_data}
    except Exception as e:
        logger.error(f"[get_custom_allocation] Error parsing allocation: {e}")
        raise HTTPException(status_code=500, detail="Error reading allocation")


# ==================== Portfolio Analysis Endpoint ====================

@app.post("/sessions/{session_id}/portfolio/analyze")
async def analyze_portfolio(session_id: str, db: Session = Depends(get_db)):
    """
    Analyze portfolio and generate AI recommendations based on actual holdings.
    Returns specific, actionable advice rather than generic percentages.
    """
    logger.info(f"[analyze_portfolio] Analyzing portfolio for session {session_id}")
    
    session_obj = models.Session.get(db, session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get portfolio document
    portfolio_doc = db.query(models.Document).filter(
        models.Document.session_id == session_id,
        models.Document.document_type == "portfolio"
    ).order_by(models.Document.created_at.desc()).first()
    
    if not portfolio_doc or not portfolio_doc.raw_metadata:
        raise HTTPException(status_code=404, detail="No portfolio found")
    
    try:
        portfolio_data = json.loads(portfolio_doc.raw_metadata)
        holdings = portfolio_data.get('holdings', [])
        
        if not holdings:
            raise HTTPException(status_code=400, detail="No holdings to analyze")
        
        # Get live data
        live_data = yfinance_service.get_portfolio_live_data(holdings)
        analytics = yfinance_service.get_portfolio_analytics(live_data['holdings'])
        
        # Calculate asset class breakdown
        total_value = live_data['total_current_value']
        
        # Build detailed portfolio summary for LLM
        portfolio_summary = f"""PORTFOLIO ANALYSIS REQUEST

Total Portfolio Value: ${live_data['total_current_value']:,.2f}
Total Gain/Loss: ${live_data['total_gain_loss']:,.2f} ({live_data['total_gain_loss_percent']:.2f}%)

Current Holdings ({len(live_data['holdings'])} positions):
"""
        for h in live_data['holdings']:
            pct_of_portfolio = (h['current_value'] / total_value * 100) if total_value > 0 else 0
            portfolio_summary += f"- {h['ticker']} ({h['name']}): ${h['current_value']:,.2f} ({pct_of_portfolio:.1f}% of portfolio)\n"
            portfolio_summary += f"  Current Price: ${h['current_price']:.2f}, Shares: {h['shares']:.0f}\n"
            portfolio_summary += f"  Performance: {h['gain_loss_percent']:+.2f}% gain/loss, Day Change: {h['day_change_percent']:+.2f}%\n\n"
        
        portfolio_summary += f"""
Risk Metrics:
- Number of Holdings: {analytics['risk_metrics']['number_of_holdings']}
- Concentration Risk: {analytics['risk_metrics']['concentration_risk']}
- Largest Single Holding: {analytics['risk_metrics']['largest_holding_percent']:.1f}% of portfolio

Top Performers:
"""
        for performer in analytics['top_performers'][:3]:
            portfolio_summary += f"- {performer['ticker']}: {performer['gain_loss_percent']:+.2f}%\n"
        
        if analytics['bottom_performers']:
            portfolio_summary += "\nUnderperformers:\n"
            for performer in analytics['bottom_performers'][:3]:
                portfolio_summary += f"- {performer['ticker']}: {performer['gain_loss_percent']:+.2f}%\n"
        
        portfolio_summary += """
Based on this portfolio, please provide a comprehensive analysis with:

1. **Asset Class & Sector Analysis**: 
   - Identify which sectors these stocks belong to (tech, finance, healthcare, etc.)
   - Calculate the sector concentration
   - Determine if the portfolio is stock-heavy, bond-heavy, or balanced

2. **Diversification Assessment**:
   - Is the portfolio over-concentrated in any single stock or sector?
   - What asset classes or sectors are missing?
   - Geographic diversification (US vs international)

3. **Specific Rebalancing Recommendations**:
   - Which specific stocks to reduce (sell X shares of TICKER)
   - Which stocks or ETFs to add (buy TICKER for diversification)
   - Suggested target allocations for each holding

4. **Risk-Adjusted Suggestions**:
   - How to reduce concentration risk
   - Dividend yield optimization
   - Volatility concerns

5. **Action Items**:
   - Prioritized list of specific trades to make
   - Timeline for rebalancing

Please be specific with ticker symbols, share counts, and percentages. Provide actionable recommendations, not generic advice.
"""
        
        logger.info(f"[analyze_portfolio] Sending query to LLM service")
        
        # Call LLM service
        llm_url = os.getenv("LLM_URL", "http://llm:8001")
        response = requests.post(
            f"{llm_url}/query",
            json={
                "query": portfolio_summary,
                "session_id": session_id,
                "top_k": 5
            },
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"[analyze_portfolio] LLM service returned {response.status_code}")
            raise HTTPException(status_code=500, detail="LLM service error")
        
        llm_response = response.json()
        logger.info(f"[analyze_portfolio] Successfully received LLM analysis")
        
        # ============ PARSE STRUCTURED RECOMMENDATIONS ============
        import re
        analysis_text = llm_response['answer']
        
        # Pattern: ticker followed by percentage (e.g., "AAPL: 25%" or "reduce AAPL to 25%")
        ticker_pattern = r'([A-Z]{1,5}):?\s*(?:to\s+)?(\d+(?:\.\d+)?)%'
        matches = re.findall(ticker_pattern, analysis_text)
        
        suggested_targets = {}
        for ticker, percentage in matches:
            # Only include if it's a valid ticker (1-5 uppercase letters)
            if len(ticker) <= 5:
                suggested_targets[ticker] = float(percentage)
        
        logger.info(f"[analyze_portfolio] Extracted {len(suggested_targets)} target suggestions")
        # ============ END PARSING ============
        
        return {
            "analysis": llm_response['answer'],
            "portfolio_summary": {
                "total_value": live_data['total_current_value'],
                "total_gain_loss": live_data['total_gain_loss'],
                "total_gain_loss_percent": live_data['total_gain_loss_percent'],
                "holdings_count": len(live_data['holdings']),
                "concentration_risk": analytics['risk_metrics']['concentration_risk'],
                "largest_holding_percent": analytics['risk_metrics']['largest_holding_percent']
            },
            "top_performers": analytics['top_performers'][:3],
            "bottom_performers": analytics['bottom_performers'][:3] if analytics['bottom_performers'] else [],
            "holdings_breakdown": [
                {
                    "ticker": h['ticker'],
                    "name": h['name'],
                    "value": h['current_value'],
                    "percent_of_portfolio": (h['current_value'] / total_value * 100) if total_value > 0 else 0
                }
                for h in live_data['holdings']
            ],
            "suggested_targets": suggested_targets  # NEW: AI-extracted target percentages
        }
        
    except requests.RequestException as e:
        logger.error(f"[analyze_portfolio] Request error: {e}")
        raise HTTPException(status_code=503, detail="Unable to connect to LLM service")
    except json.JSONDecodeError as e:
        logger.error(f"[analyze_portfolio] JSON decode error: {e}")
        raise HTTPException(status_code=500, detail="Invalid portfolio data")
    except Exception as e:
        logger.error(f"[analyze_portfolio] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
# ==================== Asset-Specific Target Allocation ====================

@app.post("/sessions/{session_id}/allocation/assets")
def save_asset_allocation_target(
    session_id: str,
    allocation: AssetAllocationTarget,
    db: Session = Depends(get_db)
):
    """Save user's asset-specific target allocation from AI recommendation."""
    logger.info(f"[save_asset_allocation_target] Saving asset targets for session {session_id}")
    
    session_obj = models.Session.get(db, session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Store as a special document type
    allocation_data = allocation.model_dump_json()
    
    # Check if target already exists
    existing = db.query(models.Document).filter(
        models.Document.session_id == session_id,
        models.Document.document_type == "asset_allocation_target"
    ).first()
    
    if existing:
        # Update existing
        existing.raw_metadata = allocation_data
        db.commit()
        logger.info(f"[save_asset_allocation_target] Updated existing targets")
    else:
        # Create new
        models.Document.create(
            db,
            session_id=session_id,
            document_type="asset_allocation_target",
            gcs_uri="internal://asset_allocation_target",
            raw_metadata=allocation_data
        )
        logger.info(f"[save_asset_allocation_target] Created new targets")
    
    return {"status": "success", "allocation": allocation}


@app.get("/sessions/{session_id}/allocation/assets")
def get_asset_allocation_target(session_id: str, db: Session = Depends(get_db)):
    """Get user's asset-specific target allocation if exists."""
    logger.info(f"[get_asset_allocation_target] Getting asset targets for session {session_id}")
    
    session_obj = models.Session.get(db, session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    target_doc = db.query(models.Document).filter(
        models.Document.session_id == session_id,
        models.Document.document_type == "asset_allocation_target"
    ).first()
    
    if not target_doc or not target_doc.raw_metadata:
        raise HTTPException(status_code=404, detail="No asset allocation target found")
    
    try:
        allocation_data = json.loads(target_doc.raw_metadata)
        return {"allocation": allocation_data}
    except Exception as e:
        logger.error(f"[get_asset_allocation_target] Error parsing allocation: {e}")
        raise HTTPException(status_code=500, detail="Error reading allocation")


@app.post("/sessions/{session_id}/allocation/assets/calculate")
def calculate_asset_targets_from_current(
    session_id: str,
    target_percentages: dict[str, float],  # {"AAPL": 25.0, "MSFT": 20.0, ...}
    db: Session = Depends(get_db)
):
    """
    Calculate specific buy/sell actions needed to reach target percentages.
    Takes target percentages and current portfolio, returns specific trade actions.
    """
    logger.info(f"[calculate_asset_targets] Calculating targets for session {session_id}")
    
    session_obj = models.Session.get(db, session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get current portfolio
    portfolio_doc = db.query(models.Document).filter(
        models.Document.session_id == session_id,
        models.Document.document_type == "portfolio"
    ).order_by(models.Document.created_at.desc()).first()
    
    if not portfolio_doc or not portfolio_doc.raw_metadata:
        raise HTTPException(status_code=404, detail="No portfolio found")
    
    try:
        portfolio_data = json.loads(portfolio_doc.raw_metadata)
        holdings = portfolio_data.get('holdings', [])
        
        # Get live data
        live_data = yfinance_service.get_portfolio_live_data(holdings)
        total_value = live_data['total_current_value']
        
        # Calculate current percentages
        current_holdings = {}
        for h in live_data['holdings']:
            current_holdings[h['ticker']] = {
                'current_value': h['current_value'],
                'current_percent': (h['current_value'] / total_value * 100) if total_value > 0 else 0,
                'current_price': h['current_price'],
                'current_shares': h['shares']
            }
        
        # Calculate targets
        targets = []
        
        for ticker, target_pct in target_percentages.items():
            current = current_holdings.get(ticker, {
                'current_value': 0,
                'current_percent': 0,
                'current_price': 0,
                'current_shares': 0
            })
            
            target_value = total_value * (target_pct / 100)
            current_value = current['current_value']
            dollar_change = target_value - current_value
            
            # Get current price for new positions
            if ticker not in current_holdings:
                quote = yfinance_service.get_stock_quote(ticker)
                if quote:
                    current['current_price'] = quote['price']
            
            if current['current_price'] > 0:
                shares_to_trade = dollar_change / current['current_price']
            else:
                shares_to_trade = 0
            
            action = "hold"
            if shares_to_trade > 0.5:
                action = "buy"
            elif shares_to_trade < -0.5:
                action = "sell"
            
            targets.append({
                "ticker": ticker,
                "target_percent": target_pct,
                "current_percent": current['current_percent'],
                "action": action,
                "shares_to_trade": round(shares_to_trade, 2),
                "dollar_amount": round(dollar_change, 2)
            })
        
        return {
            "targets": targets,
            "total_portfolio_value": total_value
        }
        
    except Exception as e:
        logger.error(f"[calculate_asset_targets] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")

