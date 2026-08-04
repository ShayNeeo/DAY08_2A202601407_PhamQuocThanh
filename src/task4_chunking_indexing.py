"""
Task 4 — Chunking & Indexing vào Vector Store (ChromaDB).
"""

import os
import shutil
import re
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
from langchain_text_splitters import RecursiveCharacterTextSplitter

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "data" / "processed" / "chroma_db"
ALT_CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
CHUNKING_METHOD = "recursive"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

VECTOR_STORE = "chromadb"
COLLECTION_NAME = "university_services_docs"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Tách YAML frontmatter và body markdown."""
    metadata = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            for line in fm_text.strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    metadata[key.strip()] = val.strip().strip('"').strip("'")
    return metadata, body


def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/ (legal/ và news/).

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str, 'customer_role': str, 'url': str}}
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        print(f"⚠ Thư mục {STANDARDIZED_DIR} không tồn tại.")
        return documents

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        raw_text = md_file.read_text(encoding="utf-8")
        fm_meta, body_text = parse_frontmatter(raw_text)

        doc_type = "legal" if "legal" in str(md_file) else "news"
        customer_role = fm_meta.get("customer_role", "both")
        url = fm_meta.get("url", "")
        title = fm_meta.get("title", md_file.stem)

        documents.append({
            "content": body_text if body_text else raw_text,
            "metadata": {
                "source": md_file.name,
                "type": doc_type,
                "customer_role": customer_role,
                "url": url,
                "title": title
            }
        })

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo RecursiveCharacterTextSplitter.

    Returns:
        List of {'content': str, 'metadata': dict}
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""]
    )

    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            if chunk_text.strip():
                chunks.append({
                    "content": chunk_text.strip(),
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index": i
                    }
                })

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng sentence-transformers/all-MiniLM-L6-v2.
    """
    model = SentenceTransformer(EMBEDDING_MODEL, token=os.getenv("HF_TOKEN"))
    texts = [c["content"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False)

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist()

    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào ChromaDB ở data/processed/chroma_db và chroma_db.
    """
    for target_dir in [CHROMA_DIR, ALT_CHROMA_DIR]:
        target_dir.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(target_dir))

        # Recreate clean collection
        try:
            client.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass

        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        ids = [f"{c['metadata']['source']}_chunk_{c['metadata']['chunk_index']}" for c in chunks]
        docs = [c["content"] for c in chunks]
        embs = [c["embedding"] for c in chunks]
        metas = [c["metadata"] for c in chunks]

        collection.upsert(
            ids=ids,
            documents=docs,
            embeddings=embs,
            metadatas=metas
        )

        print(f"✓ Indexed {len(chunks)} chunks vào ChromaDB tại: {target_dir}")


def run_pipeline():
    """Chạy toàn bộ pipeline Task 4: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing (RMIT Vietnam)")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Pipeline Task 4 hoàn tất!")


if __name__ == "__main__":
    run_pipeline()
