from datetime import date
from uuid import UUID 
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    conversation_id: str | None = None
    ticker: str = Field(..., min_length=1, max_length=10)
    year: int
    question: str = Field(..., min_length=3, max_length=2000)
    mode: str = Field(default="text")
    limit: int = Field(default=8, ge=1, le=20)


class ChunkResult(BaseModel):
    chunk_id: UUID
    ticker: str
    doc_type: str
    doc_id: str
    filing_date: date | None = None
    section_name: str | None = None
    chunk_order: int
    chunk_text: str
    similarity: float | None = None


class RetrievalSummary(BaseModel):
    ticker: str
    year: int
    question: str
    requested_limit: int
    returned_chunks: int
    top_similarity: float | None = None
    doc_types: list[str]


class AskResponse(BaseModel):
    answer: str | None = None
    chunks: list[ChunkResult]
    retrieval_summary: RetrievalSummary