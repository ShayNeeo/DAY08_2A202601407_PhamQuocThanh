"""
Task 6 — Lexical Search Module (BM25Okapi).
"""

from pathlib import Path
from rank_bm25 import BM25Okapi
from src.task4_chunking_indexing import load_documents, chunk_documents

_bm25_index = None
_chunks = []


def get_bm25_index():
    """Singleton helper để khởi tạo BM25 index từ chunks."""
    global _bm25_index, _chunks
    if _bm25_index is None:
        docs = load_documents()
        _chunks = chunk_documents(docs)
        tokenized_corpus = [c["content"].lower().split() for c in _chunks]
        _bm25_index = BM25Okapi(tokenized_corpus)
    return _bm25_index, _chunks


def build_bm25_index(corpus: list[dict]):
    """Xây dựng BM25 index từ danh sách corpus custom."""
    tokenized = [doc["content"].lower().split() for doc in corpus]
    return BM25Okapi(tokenized)


def lexical_search(query: str, top_k: int = 10, customer_role: str = None) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25 Okapi.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa
        customer_role: Filter theo vai trò ('applicant' | 'student' | None)

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    bm25, chunks = get_bm25_index()
    if not chunks:
        return []

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    results = []
    for idx, score in enumerate(scores):
        if score > 0.0:
            chunk_meta = chunks[idx]["metadata"]
            if customer_role and customer_role in ["applicant", "student"]:
                if chunk_meta.get("customer_role") not in [customer_role, "both"]:
                    continue
            results.append({
                "content": chunks[idx]["content"],
                "score": float(round(score, 4)),
                "metadata": chunk_meta
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    print("=" * 50)
    print("Task 6: BM25 Lexical Search Test")
    print("=" * 50)
    res = lexical_search("tuition fee payment deadline", top_k=5)
    for i, r in enumerate(res, 1):
        print(f"{i}. [{r['score']:.4f}] ({r['metadata'].get('source')}) {r['content'][:100]}...")
