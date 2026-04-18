from fastapi import FastAPI
from src.rag.routes import rag_router
from src.middleware import register_middleware

version = "v1"

app = FastAPI(
    version=version,
    title="RAG Application API",
    description="Retrieval-Augmented Generation API with Elasticsearch and Gemini"
)

register_middleware(app)

# Register RAG router
app.include_router(rag_router, prefix=f"/api/{version}/rag", tags=["RAG"])

@app.get("/")
async def root():
    return {
        "message": "RAG Application API",
        "version": version,
        "docs": "/docs"
    }