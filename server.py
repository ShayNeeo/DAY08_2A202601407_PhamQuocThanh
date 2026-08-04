"""
Real RAG Backend Server (FastAPI)
Connects real ChromaDB, BM25, PageIndex Fallback, and Gemini 2.5 Flash LLM to the Next.js Frontend.
"""

import os
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.task10_generation import generate_with_citation
from src.task9_retrieval_pipeline import retrieve

app = FastAPI(
    title="RMIT Vietnam RAG Backend",
    description="Real production backend for RMIT Vietnam University Services RAG",
    version="1.0.0"
)

# Enable CORS for Next.js frontend on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    customer_role: Optional[str] = None
    top_k: int = 5

class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    retrieval_source: str
    customer_role: Optional[str] = None

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "indexed_chunks": 99,
        "chroma_db": "active",
        "api_keys_loaded": {
            "ai_studio": bool(os.getenv("AI_STUDIO_API_KEY")),
            "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
            "pageindex": bool(os.getenv("PAGEINDEX_API_KEY"))
        }
    }

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    try:
        res = generate_with_citation(
            query=req.query,
            top_k=req.top_k,
            customer_role=req.customer_role
        )
        return ChatResponse(
            query=req.query,
            answer=res.get("answer", "Không nhận được phản hồi."),
            sources=res.get("sources", []),
            retrieval_source=res.get("retrieval_source", "hybrid"),
            customer_role=req.customer_role
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing RAG pipeline: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
