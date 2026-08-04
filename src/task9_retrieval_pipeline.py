"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh (Hybrid Search + RRF + PageIndex Fallback).
"""

from src.task5_semantic_search import semantic_search
from src.task6_lexical_search import lexical_search
from src.task7_reranking import rerank, rerank_rrf
from src.task8_pageindex_vectorless import pageindex_search

SCORE_THRESHOLD = 0.48  # Ngưỡng Cosine gốc để trigger fallback
DEFAULT_TOP_K = 5
RERANK_METHOD = "rrf"


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
    customer_role: str = None,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với fallback logic.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả cuối cùng
        score_threshold: Ngưỡng điểm Cosine gốc tối thiểu (KHÔNG so với RRF score)
        use_reranking: Có áp dụng RRF reranking hay không
        customer_role: Filter theo vai trò người dùng ('applicant' | 'student' | None)

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # Step 1: Run Semantic Search (Dense) and Lexical Search (Sparse)
    dense_results = semantic_search(query, top_k=top_k * 2, customer_role=customer_role)
    sparse_results = lexical_search(query, top_k=top_k * 2, customer_role=customer_role)

    # Check original Cosine score for fallback trigger
    best_dense_score = dense_results[0]["score"] if dense_results else 0.0

    if best_dense_score < score_threshold:
        print(f"  ⚠ Cosine score ({best_dense_score:.4f}) < threshold ({score_threshold}). Triggering PageIndex fallback...")
        fallback = pageindex_search(query, top_k=top_k)
        if fallback:
            return fallback

    # Step 2: Merge results using RRF (Reciprocal Rank Fusion)
    if dense_results and sparse_results:
        merged = rerank_rrf([dense_results, sparse_results], top_k=top_k * 2)
    elif dense_results:
        merged = dense_results
    elif sparse_results:
        merged = sparse_results
    else:
        return pageindex_search(query, top_k=top_k)

    for item in merged:
        item["source"] = "hybrid"

    # Step 3: Rerank / Trim to top_k
    if use_reranking and len(merged) > 1:
        final_results = merged[:top_k]
    else:
        final_results = merged[:top_k]

    return final_results


if __name__ == "__main__":
    print("=" * 60)
    print("Task 9: Hybrid Retrieval Pipeline Test")
    print("=" * 60)

    test_queries = [
        "What is the tuition fee at RMIT Vietnam?",
        "How do I apply for scholarships?",
        "xyznonsenseunrelatedquery123",
    ]

    for q in test_queries:
        print(f"\nQuery: '{q}'")
        res = retrieve(q, top_k=3)
        for i, r in enumerate(res, 1):
            print(f"  {i}. [{r['score']:.4f}] [source: {r.get('source')}] {r['content'][:80]}...")
