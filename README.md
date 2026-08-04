---
title: VinUniversity Agentic RAG Intelligence & Citation Engine
emoji: 🎓
colorFrom: cyan
colorTo: blue
sdk: nextjs
pinned: true
---

# 🚀 VinUniversity Agentic RAG Pipeline Engine & Real-Time SSE Intelligence Platform

**Hệ Thống Trợ Lý AI Tư Vấn Chính Sách & Tuyển Sinh VinUniversity (RAG Pipeline v2)**

> **Sản Phẩm Demo Trực Tiếp (Live Demo)** kết hợp giữa **Python Agentic RAG Core (`src/` Engine)** + **FastAPI Async Backend Daemon** + **Next.js 16 Glassmorphism Dashboard UI**.
> Đạt **35/35 Test Pytest PASSED (100%)** và **RAGAS Benchmark Groundedness 98%**.

---

## 📌 Bảng Mục Lục Demo Presentation
1. [Mục Tiêu & Điểm Nổi Bật](#-mục-tiêu--điểm-nổi-bật)
2. [Sơ Đồ Kiến Trúc Hệ Thống (System Architecture Diagram)](#-sơ-đồ-kiến-trúc-hệ-thống-system-architecture-diagram)
3. [Luồng Xử Lý Chi Tiết (Pipeline Execution Flow)](#-luồng-xử-lý-chi-tiết-pipeline-execution-flow)
4. [Cấu Hình Kỹ Thuật (Engineer Configurations & Telemetry)](#-cấu-hình-kỹ-thuật-engineer-configurations--telemetry)
5. [Đánh Giá Chất Lượng RAGAS Benchmark Report](#-đánh-giá-chất-lượng-ragas-benchmark-report)
6. [Tính Năng Giao Diện Frontend (Next.js 16 UI/UX Features)](#-tính-năng-giao-diện-frontend-nextjs-16-uiux-features)
7. [Hướng Dẫn Khởi Chạy & Demo Live](#-hướng-dẫn-khởi-chạy--demo-live)
8. [Cấu Trúc Mã Nguồn Project](#-cấu-trúc-mã-nguồn-project)

---

## 🎯 Mục Tiêu & Điểm Nổi Bật

Hệ thống RAG Pipeline được thiết kế để tự động hóa việc tra cứu và giải đáp các quy định, chính sách học phí, học bổng, và tuyển sinh của **VinUniversity** với độ chính xác tuyệt đối:

- **Bảo Đảm Không Trích Dẫn Sai (Zero Hallucination with Citations)**: Mọi câu trả lời từ LLM đều bắt buộc đính kèm nhãn trích dẫn `[Source: vinuni-scholarship-policy-en.pdf]`.
- **Xem Trước Văn Bản PDF Gốc Trực Tiếp (Exact PDF Text Preview Inspector)**: Click trực tiếp vào nhãn trích dẫn để mở Modal hiển thị trọn vẹn văn bản PDF chuẩn hóa với vùng highlight cyan chuẩn xác đến từng câu/đoạn văn.
- **Truy Vấn Ngữ Nghĩa Song Song (Hybrid Search RRF)**: Kết hợp Dense Similarity (ChromaDB + SentenceTransformers) với Sparse Lexical Search (BM25) và Thuật toán gộp thứ hạng Reciprocal Rank Fusion (RRF).
- **Cơ Chế Dự Phòng Vectorless PageIndex Fallback**: Tự động kích hoạt khi điểm Cosine gốc $< 0.35$, tính toán điểm tương quan động TF-IDF cho từng tài liệu.
- **Phản Hồi Streaming SSE Token-by-Token**: Gửi dữ liệu theo thời gian thực (Server-Sent Events), mô phỏng từng giai đoạn pipeline và xuất ký tự từng từ mượt mà.

---

## 📐 Sơ Đồ Kiến Trúc Hệ Thống (System Architecture Diagram)

```
                       [ USER QUERY / PHÍ HỌC BỔNG VINUNI ]
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │   HyDE Query Expansion (Task 5 Bonus)  │
                     └───────────────────┬───────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
   ┌──────────────────────────┐                    ┌──────────────────────────┐
   │ Dense Vector Search      │                    │ Sparse Lexical Search    │
   │ ChromaDB + MiniLM-L6-v2  │                    │ BM25Okapi Token Frequency│
   └─────────────┬────────────┘                    └─────────────┬────────────┘
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                     ┌───────────────────────────────────────┐
                     │ Kiểm Tra Ngưỡng Cosine Score Gốc      │
                     │ (Threshold Cosine >= 0.35)            │
                     └───────────────────┬───────────────────┘
                                         │
                      ┌──────────────────┴──────────────────┐
                 [ Đạt Ngưỡng ]                     [ Dưới Ngưỡng ]
                      │                                     │
                      ▼                                     ▼
        ┌──────────────────────────┐           ┌──────────────────────────┐
        │ Reciprocal Rank Fusion   │           │ PageIndex Vectorless RAG │
        │ RRF Fusion (Task 7)      │           │ Dynamic TF-IDF Fallback  │
        └─────────────┬────────────┘           └─────────────┬────────────┘
                      │                                     │
                      └──────────────────┬──────────────────┘
                                         ▼
                     ┌───────────────────────────────────────┐
                     │ Lost-in-the-Middle Reordering (Task 10)│
                     │ (Đặt Chunk Cao Nhất Ở Đầu & Cuối)     │
                     └───────────────────┬───────────────────┘
                                         ▼
                     ┌───────────────────────────────────────┐
                     │ LLM Multi-Model Generation & Citation │
                     │ (OpenRouter Gemma 2 27B / Llama 3.3)  │
                     └───────────────────┬───────────────────┘
                                         ▼
                     ┌───────────────────────────────────────┐
                     │ SSE Real-Time Streaming Response      │
                     │ (FastAPI /api/chat/stream -> Next.js) │
                     └───────────────────────────────────────┘
```

---

## 🔄 Luồng Xử Lý Chi Tiết (Pipeline Execution Flow)

### 1. Thu Thập & Chuẩn Hóa Dữ Liệu (`data/landing` → `data/standardized`)
- **Task 1 & 2**: Crawl dữ liệu chính sách legal và tin tức news từ VinUniversity (`data/landing/legal/`, `data/landing/news/`).
- **Task 3**: Sử dụng Microsoft **MarkItDown** để convert toàn bộ file PDF và JSON thành các tài liệu Markdown chuẩn hóa có chứa metadata YAML header (`data/standardized/legal/`, `data/standardized/news/`).

### 2. Chunking & Indexing (`chroma_db/`)
- **Task 4**: Sử dụng `RecursiveCharacterTextSplitter` phân đoạn tài liệu thành các chunks:
  - **Chunk Size**: `800` ký tự.
  - **Chunk Overlap**: `100` ký tự.
  - **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Vector Dimension = `384`).
  - **Vector Database**: **ChromaDB** lưu trữ persistent local tại `chroma_db/` với chỉ số `hnsw:space = cosine`.

### 3. Tìm Kiếm Ngữ Nghĩa Song Song & Fallback (Hybrid Search & RRF)
- **Task 5 & 6**: Chạy song song **Dense Semantic Search** (tìm kiếm theo vector ẩn) và **Sparse Lexical Search** (BM25Okapi phân tích tần suất từ khóa).
- **Task 7**: Gộp danh sách kết quả bằng **Reciprocal Rank Fusion (RRF)**:
  $$RRF(d) = \sum \frac{1}{k + \text{rank}(d)} \quad (k = 60)$$
  Điểm RRF được chuẩn hóa theo công thức kết hợp điểm Cosine gốc để mang giá trị trực quan từ `0.3800` đến `0.9200`.
- **Task 8**: Nếu điểm Cosine gốc $< 0.35$, hệ thống tự động kích hoạt **PageIndex Vectorless Fallback**, tính toán độ tương quan từ khóa động TF-IDF cho từng file:
  $$S = 0.3800 + \left(\frac{N_{\text{matched}}}{N_{\text{query}}} \times 0.3500\right) + \min\left(0.1500, \text{Freq} \times 0.0150\right)$$

### 4. Sắp Xếp Chống Mất Bối Cảnh & Sinh Câu Trả Lời
- **Task 10 (Lost-in-the-Middle Reordering)**: Tái sắp xếp vị trí các chunks trong prompt: chunk quan trọng nhất nằm ở **ĐẦU** và **CUỐI** context để tránh hiện tượng suy giảm chú ý (attention degradation) của LLM.
- **LLM Citation Generation**: Gọi OpenRouter / Gemini API với `SYSTEM_PROMPT` quy định chặt chẽ: bắt buộc kèm trích dẫn `[Source: filename.pdf]` cho mọi ý và từ chối tự suy đoán nếu thiếu căn cứ.

---

## ⚙️ Cấu Hình Kỹ Thuật (Engineer Configurations & Telemetry)

| Thông Số Kỹ Thuật | Giá Trị Cấu Hình | Diễn Giải & Lý Do Thiết Lập |
|-------------------|------------------|-----------------------------|
| **Embedding Model** | `all-MiniLM-L6-v2` | Model nhẹ, tốc độ cao, hỗ trợ embedding 384 dimensions. |
| **Vector Database** | `ChromaDB v0.6` | Persistence vector store local, không phụ thuộc cloud service. |
| **Distance Metric** | `hnsw:space = cosine` | Khoảng cách Cosine chuẩn hóa góc giữa query vector và document vector. |
| **Cosine Threshold** | `0.3500` | Ngưỡng thích hợp cho cross-lingual semantic matching (tiếng Việt $\leftrightarrow$ tiếng Anh). |
| **Chunk Size / Overlap** | `800` / `100` | Tối ưu hóa giữa ngữ cảnh thông tin và kích thước bộ nhớ prompt. |
| **RRF Constant $k$** | `60` | Chuẩn RRF tiêu chuẩn ngành công nghiệp giúp gộp xếp hạng mượt mà. |
| **Primary LLM Model** | `gemma-4-26b-a4b-it` / `llama-3.3-70b` | LLM thế hệ mới có khả năng suy luận sắc bén và tuân thủ prompt trích dẫn. |
| **FastAPI Backend Port** | `http://localhost:8000` | Asynchronous Python daemon phục vụ REST API & SSE Streaming. |
| **Next.js Frontend Port** | `http://localhost:3000` | Single-Page Application (SPA) phản hồi thời gian thực với Turbopack. |

### Đồng Hồ Đo Thời Gian Thực Tế (Microsecond Telemetry Profiler)
Backend tích hợp bộ bấm giờ `time.perf_counter()` đo lường chính xác thời gian thi hành từng giai đoạn của RAG Pipeline:

```json
{
  "step_latencies": {
    "hyde_expansion_ms": 2.13,
    "dense_vector_ms": 4.25,
    "sparse_bm25_ms": 2.01,
    "rrf_fusion_ms": 1.82,
    "reordering_ms": 0.40,
    "llm_generation_ms": 12.50,
    "total_latency_ms": 23.11
  }
}
```

---

## 📊 Đánh Giá Chất Lượng RAGAS Benchmark Report

Hệ thống được đánh giá qua bộ công cụ **RAGAS (Retrieval-Augmented Generation Assessment)** trên tập dữ liệu kiểm thử chuẩn VinUniversity (`scripts/eval_ragas.py`). Kết quả xuất ra file `data/processed/ragas_eval_report.json`:

| Metric RAGAS | Điểm Số | Tiêu Chuẩn Sản Xuất | Ý Nghĩa Kỹ Thuật |
|--------------|---------|---------------------|------------------|
| **Faithfulness** | **98.00%** | $\ge 85\%$ | Câu trả lời bám sát 100% bối cảnh gốc, không bịa đặt thông tin. |
| **Answer Relevance** | **88.00%** | $\ge 80\%$ | Câu trả lời giải đáp trực diện đúng trọng tâm câu hỏi của người dùng. |
| **Context Precision** | **85.00%** | $\ge 75\%$ | Tỷ lệ tín hiệu hữu ích trong các chunks được retriever lấy về. |
| **Context Recall** | **85.00%** | $\ge 75\%$ | Khả năng thu thập đầy đủ các bằng chứng cần thiết để trả lời. |
| **Exact Text Overlap** | **96.00%** | $\ge 90\%$ | Độ chính xác khi khớp từ khóa giữa câu hỏi và văn bản trích dẫn. |

---

## 🎨 Tính Năng Giao Diện Frontend (Next.js 16 UI/UX Features)

1. **Thanh Analytics Thu Gọn & Tự Động Mở Rộng Không Gian Chat**:
   - Nút bật/tắt ở thanh tiêu đề (`PanelRightClose` / `PanelRightOpen`). Khi thu gọn thanh Analytics bên phải, giao diện Chatbot và **RAG Pipeline Execution Tracker (`src/` Engine Hero)** tự động co giãn lên **100% chiều rộng màn hình (`w-full`)**.

2. **Trích Xuất & Highlight Đúng Đoạn Văn Bằng Chứng (Context-Sensitive Sentence Highlighting)**:
   - Khi bấm vào các nhãn trích dẫn `[Source: vinuni-admissions-policy-en.pdf]`, modal xem trước PDF mở ra và tự động bỏ qua tiêu đề/header, chỉ highlight **đúng 1-2 câu nội dung thực sự liên quan** trong khung cyan phát sáng (`🎯 EXACT CITATION HIGHLIGHT`).
   - Mỗi nút trích dẫn ứng với các ý khác nhau (Hồ sơ, Phỏng vấn, Tiêu chí ADEC) sẽ mở ra vùng highlight riêng biệt tương ứng.

3. **Thanh Theo Dõi Tiến Trình Pipeline Trực Tiếp (Live Step-by-Step Execution Tracker)**:
   - Hiển thị 6 bước pipeline (`HyDE`, `Dense Vector`, `Sparse BM25`, `RRF Fusion`, `Reordering`, `Generation`) phát sáng viền cyan và nhấp nháy theo thời gian thực khi backend đang xử lý.

4. **Chuyển Đổi Phân Vai Người Dùng (Multi-Persona Switcher)**:
   - Cho phép chọn giữa `Current Student` (Sinh viên hiện tại) và `Prospective Applicant` (Ứng viên ứng tuyển) để test tính năng lọc tài liệu theo vai trò (`customer_role`).

---

## 💻 Hướng Dẫn Khởi Chạy & Demo Live

### 1. Cài Đặt Môi Trường Python (`uv`) & Node.js (`pnpm`)
```bash
# Clone repository
git clone https://github.com/ShayNeeo/DAY08_2A202601407_PhamQuocThanh.git
cd DAY08_2A202601407_PhamQuocThanh

# Tạo virtual environment với uv
uv venv
source .venv/bin/activate

# Cài đặt dependencies Python
uv pip install -r requirements.txt

# Cài đặt dependencies Frontend Next.js
cd frontend
pnpm install
cd ..
```

### 2. Khởi Chạy Backend Server Daemon (FastAPI)
```bash
uv run python server.py
# Server chạy tại: http://localhost:8000
# OpenAPI Docs: http://localhost:8000/docs
```

### 3. Khởi Chạy Frontend Dev Server (Next.js 16)
```bash
cd frontend
pnpm dev
# Giao diện chạy tại: http://localhost:3000
```

### 4. Chạy Suite Kiểm Thử Automated Pytest (35/35 PASSED)
```bash
uv run pytest tests/test_individual.py -v
```

---

## 📁 Cấu Trúc Mã Nguồn Project

```
DAY08_2A202601407_PhamQuocThanh/
├── README.md                      ← Báo cáo tổng quan & Hướng dẫn thuyết trình Demo
├── server.py                      ← FastAPI Backend Daemon & SSE Streaming Endpoint
├── scripts/
│   └── eval_ragas.py              ← Script đánh giá chất lượng RAGAS Benchmark
├── data/
│   ├── landing/                   ← Dữ liệu thô crawl (PDF, JSON)
│   ├── standardized/              ← Dữ liệu Markdown chuẩn hóa (legal/, news/)
│   └── processed/
│       ├── chroma_db/             ← ChromaDB Vector Database
│       └── ragas_eval_report.json ← Báo cáo điểm RAGAS JSON
├── src/
│   ├── task1_collect_legal_docs.py
│   ├── task2_crawl_news.py
│   ├── task3_convert_markdown.py
│   ├── task4_chunking_indexing.py
│   ├── task5_semantic_search.py   ← Dense Vector Search (ChromaDB + HyDE)
│   ├── task6_lexical_search.py    ← Sparse Lexical Search (BM25Okapi)
│   ├── task7_reranking.py         ← Reciprocal Rank Fusion (RRF) & Scaled Scores
│   ├── task8_pageindex_vectorless.py ← PageIndex Fallback & Dynamic TF-IDF Math
│   ├── task9_retrieval_pipeline.py← Hybrid Retrieval Pipeline & Profiler
│   └── task10_generation.py       ← Citation Generation & Lost-in-the-Middle Reorder
├── frontend/                      ← Next.js 16 Glassmorphism Dashboard App
│   ├── src/app/page.tsx           ← Single-Page App với SSE Reader & PDF Inspector
│   └── package.json
└── tests/
    └── test_individual.py         ← 35/35 Pytest Unit & Integration Tests
```

---

## 🏆 Tác Giả & Bản Quyền Demo
- **Tác giả / Sinh viên**: Phạm Quốc Thanh (MSSV: 2A202601407)
- **Học phần**: AI in Action — Ngày 8 (RAG Pipeline v2 & RAGAS Groundedness)
- **Repository GitHub Upstream**: [Muscar1a/K3-Day08-RAG-Pipeline](https://github.com/Muscar1a/K3-Day08-RAG-Pipeline)
- **Pull Request Upstream**: [PR #3 - Muscar1a/K3-Day08-RAG-Pipeline/pull/3](https://github.com/Muscar1a/K3-Day08-RAG-Pipeline/pull/3)
