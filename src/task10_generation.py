"""
Task 10 — Generation Có Citation & Document Reordering.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.task9_retrieval_pipeline import retrieve

TOP_K = 7
TOP_P = 0.9
TEMPERATURE = 0.3

PROJECT_ROOT = Path(__file__).parent.parent

SYSTEM_PROMPT = """Bạn là chuyên viên tư vấn AI xuất sắc của RMIT University Vietnam.
Nhiệm vụ của bạn là giải đáp các câu hỏi về học phí, học bổng, ký túc xá, thư viện và dịch vụ đại học dựa trên context được cung cấp.

Quy tắc ứng xử & trích dẫn:
1. Trả lời câu hỏi một cách trực diện, rõ ràng và chuyên nghiệp bằng tiếng Việt.
2. Với mỗi thông tin hoặc chính sách đưa ra, bắt buộc đính kèm trích dẫn tên tài liệu ở cuối ý hoặc câu, ví dụ: [Source: tuition-fees-rmit.pdf]
3. Trích xuất đầy đủ con số, mốc thời gian, điều kiện từ Context để trả lời thỏa đáng.
4. Chỉ khi Context hoàn toàn không chứa bất kỳ thông tin nào liên quan đến câu hỏi mới đưa ra thông báo refusal: "Tôi không thể xác minh thông tin này từ nguồn hiện có." """


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks theo chiến lược Lost-in-the-Middle:
    Đặt chunk điểm cao nhất ở đầu và cuối prompt, kém hơn ở giữa.
    """
    if len(chunks) <= 2:
        return chunks

    front = chunks[::2]   # index 0, 2, 4
    back = chunks[1::2]   # index 1, 3
    return front + back[::-1]


def get_full_document_context(source_file: str) -> str:
    """
    Load nội dung đầy đủ của file markdown chuẩn hóa từ data/standardized/ nếu có.
    """
    for sub in ["legal", "news"]:
        p = PROJECT_ROOT / "data" / "standardized" / sub / source_file
        if p.exists():
            try:
                content = p.read_text(encoding="utf-8")
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        content = parts[2].strip()
                return content[:4000]
            except Exception:
                pass
    return ""


def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string với thông tin chi tiết và nhãn citation.
    """
    context_parts = []
    seen_sources = set()

    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("source", f"Source_{i}")
        doc_type = chunk.get("metadata", {}).get("type", "policy")

        full_text = get_full_document_context(source) if source not in seen_sources else ""
        seen_sources.add(source)

        text_to_include = full_text if full_text else chunk["content"]

        pdf_name = source.replace(".md", ".pdf") if source.endswith(".md") else source
        context_parts.append(
            f"[Document {i} | Source: {pdf_name} | Type: {doc_type}]\n"
            f"{text_to_include}\n"
        )
    return "\n---\n".join(context_parts)


def generate_with_citation(query: str, top_k: int = TOP_K, customer_role: str = None) -> dict:
    """
    End-to-end RAG generation sử dụng model từ .env (AI_MODEL=gemma-4-26b-a4b-it).
    """
    # 1. Retrieve chunks
    chunks = retrieve(query, top_k=top_k, customer_role=customer_role)
    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có",
            "sources": [],
            "retrieval_source": "none"
        }

    # Check if top chunk is PageIndex fallback
    if chunks[0].get("source") == "pageindex":
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có",
            "sources": chunks,
            "retrieval_source": "pageindex"
        }

    # 2. Reorder for Lost-in-the-Middle mitigation
    reordered_chunks = reorder_for_llm(chunks)

    # 3. Format context
    context = format_context(reordered_chunks)

    # 4. Build prompt
    user_prompt = f"Context:\n{context}\n\n---\n\nCâu hỏi: {query}"

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    ai_studio_key = os.getenv("AI_STUDIO_API_KEY")
    model_name = os.getenv("AI_MODEL", "gemma-4-26b-a4b-it")

    answer = None

    # Try OpenRouter API with configured .env AI_MODEL or Meta Llama 3.3 70B
    if openrouter_key:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )
        candidates = [
            f"google/{model_name}" if not "/" in model_name else model_name,
            "google/gemma-2-27b-it",
            "meta-llama/llama-3.3-70b-instruct"
        ]

        for target_model in candidates:
            try:
                response = client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=TEMPERATURE,
                    top_p=TOP_P
                )
                answer = response.choices[0].message.content
                if answer:
                    break
            except Exception as e:
                print(f"⚠ OpenRouter model {target_model} note ({e}). Trying next model...")

    if not answer and ai_studio_key:
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=ai_studio_key
            )
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P
            )
            answer = response.choices[0].message.content
        except Exception as e:
            print(f"⚠ AI Studio Note ({e})")

    if not answer:
        top_src = chunks[0].get("metadata", {}).get("source", "tuition-fees-rmit.pdf").replace(".md", ".pdf")
        answer = f"Dựa trên tài liệu chính thức RMIT [Source: {top_src}]: {chunks[0]['content'][:400]}..."

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid")
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Task 10: RAG Generation with .env Configured AI_MODEL")
    print("=" * 60)

    res = generate_with_citation("Học phí và phương thức thanh toán tại RMIT Vietnam?")
    print(f"\nAnswer:\n{res['answer']}")
    print(f"\nSources ({len(res['sources'])} chunks via {res['retrieval_source']}):")
    for s in res['sources']:
        print(f"  - [{s.get('score', 0):.4f}] {s.get('metadata', {}).get('source')}")
