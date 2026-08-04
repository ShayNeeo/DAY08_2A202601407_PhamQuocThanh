"""
Task 7 — Reranking Module (RRF, MMR & OpenRouter Cross-Encoder).
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion (RRF) — gộp kết quả từ nhiều ranker (Dense + Sparse).

    RRF(d) = Σ 1 / (k + rank_r(d))
    """
    if not ranked_lists:
        return []

    rrf_scores = {}  # content -> score
    content_map = {}  # content -> full item dict

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (k + rank))
            if key not in content_map:
                content_map[key] = item

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content, score in sorted_items[:top_k]:
        item = content_map[content].copy()
        item["score"] = round(score, 6)
        results.append(item)

    return results


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng OpenRouter Reranker (nvidia/llama-nemotron-rerank-vl-1b-v2:free)
    hoặc Jina Reranker API.
    """
    if not candidates:
        return []

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    reranker_model = os.getenv("OPENROUTER_RERANKER_MODEL", "nvidia/llama-nemotron-rerank-vl-1b-v2:free")

    if openrouter_key:
        try:
            import requests
            response = requests.post(
                "https://openrouter.ai/api/v1/rerank",
                headers={
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": reranker_model,
                    "query": query,
                    "documents": [c["content"] for c in candidates],
                    "top_n": top_k
                },
                timeout=8
            )
            if response.status_code == 200:
                reranked = response.json().get("results", [])
                results = []
                for r in reranked:
                    item = candidates[r["index"]].copy()
                    item["score"] = round(float(r.get("relevance_score", r.get("score", 0.0))), 4)
                    results.append(item)
                return results
        except Exception as e:
            print(f"⚠ OpenRouter Reranker API note ({e}), using RRF score ranking.")

    # Fallback to RRF / Score sorting
    sorted_candidates = sorted(candidates, key=lambda x: x.get("score", 0.0), reverse=True)
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

    import numpy as np

    def cosine_sim(a, b):
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    selected = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = None
        best_score = float('-inf')

        for idx in remaining:
            cand_emb = candidates[idx].get("embedding")
            if not cand_emb:
                relevance = candidates[idx].get("score", 0.0)
            else:
                relevance = cosine_sim(query_embedding, cand_emb)

            max_sim_to_selected = 0.0
            for sel_idx in selected:
                sel_emb = candidates[sel_idx].get("embedding")
                if cand_emb and sel_emb:
                    sim = cosine_sim(cand_emb, sel_emb)
                    max_sim_to_selected = max(max_sim_to_selected, sim)

            mmr_score = lambda_param * relevance - (1.0 - lambda_param) * max_sim_to_selected

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is not None:
            selected.append(best_idx)
            remaining.remove(best_idx)

    return [candidates[i] for i in selected]


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "rrf",
) -> list[dict]:
    """
    Unified reranking interface.
    """
    if isinstance(candidates, list) and len(candidates) > 0 and isinstance(candidates[0], list):
        return rerank_rrf(candidates, top_k=top_k)

    if method == "rrf":
        return rerank_rrf([candidates], top_k=top_k)
    elif method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        return rerank_mmr([], candidates, top_k)
    else:
        return candidates[:top_k]


if __name__ == "__main__":
    print("=" * 50)
    print("Task 7: RRF & OpenRouter Reranking Test")
    print("=" * 50)
    list1 = [
        {"content": "Tuition fee payment schedule 2026", "score": 0.85, "metadata": {}},
        {"content": "Scholarship eligibility requirements", "score": 0.60, "metadata": {}},
    ]
    list2 = [
        {"content": "Tuition fee payment schedule 2026", "score": 12.5, "metadata": {}},
        {"content": "Library borrowing rules", "score": 8.0, "metadata": {}},
    ]
    fused = rerank_rrf([list1, list2], top_k=3)
    for i, r in enumerate(fused, 1):
        print(f"{i}. [{r['score']:.6f}] {r['content']}")
