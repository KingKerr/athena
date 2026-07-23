import time
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.postgres import get_db
from models.api_models import AskRequest, AskResponse, ChunkResult, RetrievalSummary
from rag.service import summarize_ten_k_risks
from services.answer_service import build_grounded_answer
from services.retrieval_service import retrieve_chunks

router = APIRouter(prefix="/api", tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse:
    ticker = payload.ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required.")
    try:
        result = summarize_ten_k_risks(
            ticker=ticker,
            year=payload.year,
            question=payload.question,
            limit=getattr(payload, "limit", 8),
        )
        return AskResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG request failed: {str(e)}")
