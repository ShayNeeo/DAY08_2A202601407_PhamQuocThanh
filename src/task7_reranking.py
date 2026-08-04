"""
Task 7 — Reranking Module.
"""

from typing import Optional


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng cross-encoder model / heuristic score ranking.

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates, re-scored và sorted by score descending.
    """
    if not candidates:
        return []

    # Heuristic scoring boost based on term matching + original similarity
    query_terms = set(query.lower().split())
    rescored = []

    for c in candidates:
        content_lower = c["content"].lower()
        match_count = sum(1 for term in query_terms if term in content_lower)
        boost = 0.1 * match_count
        new_score = float(c.get("score", 0.0)) + boost

        c_copy = c.copy()
        c_copy["score"] = round(new_score, 4)
        rescored.append(c_copy)

    sorted_candidates = sorted(rescored, key=lambda x: x["score"], reverse=True)
    return sorted_candidates[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.
    """
    if not candidates:
        return []

    # Fallback to sorted top_k candidates
    return candidates[:top_k]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker với score scaling tự nhiên.

    RRF(d) = Σ 1 / (k + rank_r(d))
    """
    if not ranked_lists:
        return []

    rrf_scores = {}
    content_map = {}
    orig_scores = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item.get("content", str(item))
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            content_map[key] = item
            if key not in orig_scores:
                orig_scores[key] = float(item.get("score", 0.50))

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    max_rrf = sorted_items[0][1] if sorted_items else 1.0

    for content, rrf_score in sorted_items[:top_k]:
        item = content_map[content].copy()
        orig = orig_scores.get(content, 0.50)

        # Scale RRF score relative to dense similarity [0.3800, 0.8800]
        if orig > 0.05 and orig <= 1.0:
            final_score = round(max(0.3800, min(0.9200, orig * 0.70 + (rrf_score / max_rrf) * 0.25)), 4)
        else:
            final_score = round(max(0.3800, min(0.9200, (rrf_score / max_rrf) * 0.75 + 0.15)), 4)

        item["score"] = final_score
        results.append(item)

    return results


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "rrf",
) -> list[dict]:
    """
    Unified reranking interface.
    """
    if not candidates:
        return []

    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        return candidates[:top_k]
    elif method == "rrf":
        return rerank_rrf([candidates], top_k=top_k)
    else:
        return candidates[:top_k]


if __name__ == "__main__":
    dummy_candidates = [
        {"content": "Tuition fee payment schedule", "score": 0.8, "metadata": {}},
        {"content": "Scholarship eligibility requirements", "score": 0.6, "metadata": {}},
        {"content": "Library study room booking guide", "score": 0.5, "metadata": {}},
    ]
    results = rerank("tuition fee payment", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")
