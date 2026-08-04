"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Module-level cache — build once, reuse across calls
_bm25: BM25Okapi | None = None
_corpus: list[dict] = []


def _load_corpus() -> list[dict]:
    """Đọc toàn bộ .md files từ data/standardized/ làm corpus cho BM25."""
    docs = []
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file) else "news"
        docs.append({"content": content, "metadata": {"source": md_file.name, "type": doc_type}})
    return docs


def _get_bm25() -> tuple[BM25Okapi, list[dict]]:
    """Lazy-init BM25 index (chỉ build lần đầu gọi)."""
    global _bm25, _corpus
    if _bm25 is None:
        _corpus = _load_corpus()
        if not _corpus:
            raise RuntimeError("Corpus rỗng — hãy chạy Task 3 trước để có data/standardized/")
        tokenized = [doc["content"].lower().split() for doc in _corpus]
        _bm25 = BM25Okapi(tokenized)
    return _bm25, _corpus


def build_bm25_index(corpus: list[dict]) -> BM25Okapi:
    """
    Xây dựng BM25 index từ corpus bên ngoài (dùng cho test / Task 9).

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    global _bm25, _corpus
    _corpus = corpus
    tokenized = [doc["content"].lower().split() for doc in corpus]
    _bm25 = BM25Okapi(tokenized)
    return _bm25


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
        Sorted by score descending.
    """
    bm25, corpus = _get_bm25()

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append({
                "content": corpus[idx]["content"],
                "score": float(scores[idx]),
                "metadata": corpus[idx]["metadata"],
            })
    return results


if __name__ == "__main__":
    results = lexical_search("tuition fee payment methods", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['metadata']['source']} — {r['content'][:100]}...")
