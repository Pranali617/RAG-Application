from fastapi import APIRouter, HTTPException
from src.rag.schemas import AskRequest, AskResponse
from src.rag.service import get_answer_service
from src.core.vector_store import vectorstore

rag_router = APIRouter()

@rag_router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    Ask a question about the indexed documents
    
    Examples:
    - "Are these advertisement filings in Texas?"
    - "How has rates changed for product X in the last 10 years?"
    - "Give me files that have Form ABCD"
    """
    try:
        result = await get_answer_service(
            query=request.query,
            person=request.person,
            top_k=request.top_k,
            include_sources=request.include_sources
        )
        return AskResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@rag_router.get("/stats")
async def get_stats():
    """Get index statistics"""
    try:
        stats = vectorstore.get_index_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@rag_router.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "vector_store": "elasticsearch",
        "embedding_model": "all-MiniLM-L6-v2"
    }