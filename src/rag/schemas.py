from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

class DocumentMetadata(BaseModel):
    """Metadata for indexed documents"""
    source: str = Field(..., description="Source filename")
    file_type: str = Field(..., description="File extension (.pdf, .zip, etc.)")
    producer: Optional[str] = None
    creator: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    total_pages: Optional[int] = None
    page_number: Optional[int] = None
    page_label: Optional[str] = None
    owner: Optional[str] = None
    indexed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class DocumentChunk(BaseModel):
    """A chunk of document content"""
    page_content: str
    metadata: DocumentMetadata
    chunk_index: Optional[int] = None

class AskRequest(BaseModel):
    query: str = Field(..., description="User's question")
    person: Optional[str] = Field(None, description="Filter by owner (e.g., 'pranali_bedaka')")
    top_k: Optional[int] = Field(5, description="Number of documents to retrieve", ge=1, le=20)
    include_sources: Optional[bool] = Field(True, description="Include source documents in response")

class AskResponse(BaseModel):
    query: str
    answer: str
    sources: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None