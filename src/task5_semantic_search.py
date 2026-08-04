"""
Task 5 — Semantic Search Module (Dense Cosine Similarity + HyDE).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Setup HuggingFace Token for authenticated model downloads
hf_token = os.getenv("HF_TOKEN")
if hf_token:
    os.environ["HF_TOKEN"] = hf_token
    os.environ["HUGGING_FACE_HUB_TOKEN"] = hf_token

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = Path(__file__).parent.parent / "data" / "processed" / "chroma_db"
ALT_CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "university_services_docs"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_model = None
_collection = None


def get_embedding_model():
    """Singleton helper cho SentenceTransformer model với HF_TOKEN."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL, token=os.getenv("HF_TOKEN"))
    return _model


def get_collection():
    """Singleton helper cho ChromaDB collection."""
    global _collection
    if _collection is None:
        target_path = CHROMA_DIR if CHROMA_DIR.exists() else ALT_CHROMA_DIR
        client = chromadb.PersistentClient(path=str(target_path))
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def generate_hypothetical_document(query: str) -> str:
    """Tạo giả định câu trả lời (HyDE) để mở rộng query embedding."""
    try:
        from openai import OpenAI
        load_dotenv()

        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("AI_STUDIO_API_KEY")
        if not api_key:
            return query

        if os.getenv("OPENROUTER_API_KEY"):
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
            model_name = "meta-llama/llama-3.3-70b-instruct"
        else:
            client = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=api_key)
            model_name = "gemini-2.0-flash"

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a university advisor writing a hypothetical detailed paragraph answering a student query."},
                {"role": "user", "content": f"Write a hypothetical paragraph answering this query: {query}"}
            ],
            temperature=0.3,
            max_tokens=150
        )
        hypothesis = response.choices[0].message.content
        return f"{query}\n{hypothesis}"
    except Exception as e:
        print(f"⚠ HyDE generation skipped ({e}), falling back to raw query.")
        return query


def semantic_search(query: str, top_k: int = 10, customer_role: str = None, use_hyde: bool = False) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity (Dense Retrieval).

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa
        customer_role: Filter theo vai trò ('applicant' | 'student' | None)
        use_hyde: Cờ kích hoạt Hypothetical Document Embeddings

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score [0, 1]
            'metadata': dict     # source, doc_type, customer_role, chunk_index
        }
        Sorted by score descending.
    """
    model = get_embedding_model()
    collection = get_collection()

    search_text = generate_hypothetical_document(query) if use_hyde else query
    query_vector = model.encode(search_text).tolist()

    where_filter = None
    if customer_role and customer_role in ["applicant", "student"]:
        where_filter = {"customer_role": customer_role}

    kwargs = {
        "query_embeddings": [query_vector],
        "n_results": min(top_k, collection.count()) if collection.count() > 0 else top_k,
        "include": ["documents", "metadatas", "distances"]
    }
    if where_filter and collection.count() > 0:
        kwargs["where"] = where_filter

    results = collection.query(**kwargs)

    if not results or not results.get("documents") or not results["documents"][0]:
        return []

    output = []
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    for doc, meta, dist in zip(docs, metas, dists):
        # Convert cosine distance (0=exact, 2=opposite) to similarity (1=exact, 0=opposite)
        score = max(0.0, 1.0 - float(dist))
        output.append({
            "content": doc,
            "score": round(score, 4),
            "metadata": meta
        })

    # Sort descending by score
    output.sort(key=lambda x: x["score"], reverse=True)
    return output[:top_k]


if __name__ == "__main__":
    print("=" * 50)
    print("Task 5: Semantic Search Test")
    print("=" * 50)
    results = semantic_search("what is the tuition fee for undergraduate", top_k=5)
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['score']:.4f}] ({r['metadata'].get('source')}) {r['content'][:100]}...")
