import os
from typing import Dict, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.core.vector_store import vectorstore
from src.core.engine import llm
from src.config import Config
from datetime import datetime

def extract_metadata_from_langchain_doc(doc) -> Dict:
    """Extract and normalize metadata from LangChain document"""
    metadata = doc.metadata.copy()
    
    # Normalize metadata keys
    normalized = {
        "source": os.path.basename(metadata.get("source", "unknown")),
        "file_type": os.path.splitext(metadata.get("source", ""))[1],
        "producer": metadata.get("producer"),
        "creator": metadata.get("creator"),
        "author": metadata.get("author"),
        "title": metadata.get("title"),
        "subject": metadata.get("subject"),
        "keywords": metadata.get("keywords"),
        "creation_date": metadata.get("creationdate"),
        "modification_date": metadata.get("moddate"),
        "total_pages": metadata.get("total_pages"),
        "page_number": metadata.get("page"),
        "page_label": metadata.get("page_label"),
        "owner": metadata.get("source", "").replace(".pdf", "").lower(),
        "indexed_at": datetime.utcnow().isoformat()
    }
    
    return {k: v for k, v in normalized.items() if v is not None}


async def get_answer_service(
    query: str, 
    person: Optional[str] = None,
    top_k: int = 5,
    include_sources: bool = True
) -> Dict:
    """
    Get answer from documents using RAG
    
    Args:
        query: User's question
        person: Filter by owner
        top_k: Number of documents to retrieve
        include_sources: Include source documents in response
    """
    
    # Build filter
    filter_dict = {}
    if person:
        filter_dict["owner"] = person.lower()
    
    # Search for relevant documents
    docs = vectorstore.similarity_search(
        query=query,
        k=top_k,
        filter_dict=filter_dict if filter_dict else None
    )
    
    if not docs:
        return {
            "query": query,
            "answer": "No relevant information found in the uploaded documents.",
            "sources": [],
            "metadata": {"documents_found": 0}
        }
    
    # Build context from retrieved documents
    context_parts = []
    sources = []
    
    for i, hit in enumerate(docs, 1):
        source = hit['_source']
        content = source.get('page_content', '')
        metadata = source.get('metadata', {})
        score = hit.get('_score', 0)
        
        context_parts.append(
            f"[Document {i} - Source: {metadata.get('source', 'unknown')}, "
            f"Page: {metadata.get('page_number', 'N/A')}]\n{content}"
        )
        
        if include_sources:
            sources.append({
                "source": metadata.get('source', 'unknown'),
                "file_type": metadata.get('file_type', 'unknown'),
                "page_number": metadata.get('page_number'),
                "page_label": metadata.get('page_label'),
                "score": round(score, 4),
                "content_preview": content[:300] + "..." if len(content) > 300 else content
            })
    
    context = "\n\n".join(context_parts)
    
    # Create prompt for LLM
    prompt = f"""You are a helpful AI assistant analyzing insurance and regulatory documents.

Answer the user's question based strictly on the context provided below.

Guidelines:
- Provide accurate, specific information from the documents
- Cite which document and page your information comes from
- If the information is not in the context, clearly state "This information is not mentioned in the provided documents"
- For questions about trends or graphs, describe what data is available but note if visualization is not possible
- Be concise but comprehensive

Context:
{context}

Question: {query}

Answer:"""
    
    # Get response from Gemini
    try:
        response = await llm.ainvoke(prompt)
        answer = response.content
    except Exception as e:
        answer = f"Error generating answer: {str(e)}"
    
    return {
        "query": query,
        "answer": answer,
        "sources": sources if include_sources else None,
        "metadata": {
            "documents_found": len(docs),
            "filter_applied": filter_dict if filter_dict else None
        }
    }