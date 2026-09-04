# Document Analyzer — Agentic RAG System

> An intelligent **Retrieval-Augmented Generation (RAG)** application that allows users to upload documents and ask questions using semantic retrieval, document citations, and a **LangGraph-based agentic workflow**.


---

## ✨ Overview

**Document Analyzer** is a full-stack AI application designed to answer questions from user-uploaded documents.

The system follows an advanced RAG pipeline:

```text
Documents
    ↓
Load & Clean
    ↓
Chunking
    ↓
Embeddings
    ↓
ChromaDB
    ↓
Semantic Retrieval
    ↓
Relevance Evaluation
    ↓
Query Rewriting (if required)
    ↓
LLM Answer Generation
    ↓
Citations & Verification
```

The project goes beyond a simple:

```text
Question → Retriever → LLM → Answer
```

by using a **LangGraph workflow** to control retrieval, relevance checking, query rewriting, answer generation, and verification.

---

## 🎯 Project Objectives

* Upload and process **PDF, TXT, and DOCX** documents.
* Clean and split documents into meaningful chunks.
* Generate semantic embeddings for document retrieval.
* Store embeddings persistently using **ChromaDB**.
* Retrieve relevant document context using semantic search.
* Improve retrieval using query variations and reranking capabilities.
* Use **LangGraph** for conditional agentic RAG workflow.
* Generate answers using an external LLM through OpenRouter.
* Provide document/page-based citations.
* Maintain chat sessions and conversation history.
* Provide a REST API through FastAPI.
* Provide a React-based web interface.

---

## 🏗️ System Architecture

```text
┌───────────────────────┐
│     React Frontend    │
│   Document + Chat UI  │
└───────────┬───────────┘
            │ HTTP
            ▼
┌───────────────────────┐
│      FastAPI API      │
├───────────────────────┤
│ Document Endpoints    │
│ Chat Endpoints        │
│ Health Endpoint       │
└───────────┬───────────┘
            │
            ▼
┌────────────────────────────────┐
│       LangGraph RAG Agent      │
│                                │
│ Query Analyzer                 │
│       ↓                        │
│ Retriever                      │
│       ↓                        │
│ Relevance Grader               │
│    ↙       ↘                   │
│ Rewrite      Answer             │
│    ↓           ↓                │
│ Retriever   Citation/Check      │
│                ↓               │
│             Final Answer        │
└───────────┬────────────────────┘
            │
      ┌─────┴─────────┐
      ▼               ▼
┌─────────────┐  ┌──────────────┐
│  ChromaDB   │  │ PostgreSQL   │
│ Vector Data │  │ Chat Data    │
└─────────────┘  └──────────────┘
            │
            ▼
       ┌─────────┐
       │  Redis  │
       └─────────┘
```

---

## 🔄 RAG & LangGraph Workflow

The agentic workflow is designed around conditional retrieval and answer generation.

```text
START
  │
  ▼
Query Analyzer
  │
  ▼
Retriever
  │
  ▼
Relevance Grader
  │
  ├── Relevant ───────► Answer Generator
  │                           │
  │                           ▼
  │                    Citation / Check
  │                           │
  │                           ▼
  │                          END
  │
  └── Not Relevant ──► Query Rewriter
                            │
                            ▼
                         Retriever
```

This enables the system to retry retrieval when the initial query does not produce sufficiently relevant context.

---

## 📄 Document Ingestion

The ingestion pipeline supports:

* PDF
* TXT
* DOCX

### Processing Steps

1. Detect document type.
2. Load document using LangChain document loaders.
3. Clean extracted text.
4. Remove unnecessary whitespace and formatting artifacts.
5. Split documents into configurable chunks.
6. Generate embeddings.
7. Store vectors and metadata in ChromaDB.

### Default Chunk Configuration

```text
Chunk Size:     512
Chunk Overlap:   50
```

Metadata such as filename, document ID, page number, and chunk index is retained to support citations.

---

## 🔎 Advanced Retrieval

The project implements several retrieval capabilities:

### Semantic Search

Documents are converted into embeddings using:

```text
sentence-transformers/all-MiniLM-L6-v2
```

ChromaDB is then used to retrieve semantically similar chunks.

### Multi-Query Retrieval

The system can generate query variations such as:

```text
Original Query
     ↓
Lowercase Variation
     ↓
Alternative Query
     ↓
Semantic Retrieval
     ↓
Deduplication
```

### Reranking

A BGE reranker is implemented using:

```text
BAAI/bge-reranker-base
```

This provides a second-stage relevance scoring mechanism after initial retrieval.

> **Note:** Advanced MMR and reranking functionality is implemented in the retrieval module, while the current LangGraph execution path uses basic semantic retrieval configuration.

---

## 📌 Citations

Retrieved information is associated with metadata including:

* Document name
* Page number
* Chunk index
* Retrieval score
* Source text

Example response structure:

```text
Answer:
The document states that ...

Sources:
[1] example.pdf — Page 3
[2] example.pdf — Page 7
```

This allows users to identify where retrieved information originated.

---

## 🚀 FastAPI Backend

The backend is built with **FastAPI**.

### Base URL

```text
http://localhost:8000
```

### API Documentation

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

## 🔌 API Endpoints

### Health Check

```http
GET /health
```

Checks the availability/configuration of core services such as:

* PostgreSQL
* Redis
* ChromaDB
* LLM configuration

---

### Upload Document

```http
POST /documents/upload
```

Uploads and processes a PDF, TXT, or DOCX document.

Example:

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@example.pdf"
```

---

### List Documents

```http
GET /documents
```

Returns uploaded/indexed documents.

---

### Delete Document

```http
DELETE /documents/{document_id}
```

Removes a document and its associated vector data.

---

### Ask a Question

```http
POST /chat
```

Example request:

```json
{
  "question": "What is the main conclusion of the document?",
  "top_k": 10
}
```

Example response:

```json
{
  "answer": "The main conclusion is ...",
  "citations": [
    {
      "document": "example.pdf",
      "page": 3,
      "chunk_index": 2,
      "score": 0.87
    }
  ],
  "retrieval_score": 0.87,
  "query_rewritten": false,
  "retry_count": 0
}
```

---

### Chat History

```http
GET /chat/history/{session_id}
```

Returns messages associated with a chat session.

---

### Chat Sessions

```http
GET /chat/sessions
```

Returns available conversation sessions.

---

## 🖥️ Frontend

The frontend is implemented using:

* React 18
* Vite
* Axios
* React Markdown

The interface provides:

* 📁 Document upload
* 📚 Indexed document management
* 💬 AI chat
* 🧠 Question answering
* 📌 Citation display
* 🗂️ Conversation/session management
* 🔄 Chat history

### Example UI

```text
┌──────────────────────────────────────────────────────────┐
│  Document Analyzer                                       │
├──────────────┬───────────────────────────────────────────┤
│              │                                           │
│  Documents   │          AI Chat                          │
│              │                                           │
│  📄 report   │  User: What is this document about?       │
│  📄 paper    │                                           │
│              │  AI: The document discusses...            │
│  ──────────  │                                           │
│              │  📌 Sources                               │
│  Chat        │  report.pdf — Page 3                      │
│  History     │                                           │
│              │                                           │
└──────────────┴───────────────────────────────────────────┘
```

---

## 🗄️ Data & Persistence

### ChromaDB

Used as the persistent vector database for:

* Document chunks
* Embeddings
* Metadata
* Retrieval

### PostgreSQL

Used for persistent application data such as:

* Chat sessions
* User/assistant messages
* Conversation history

### Redis

Used as a supporting in-memory service for application operations.

---

## ⚙️ Environment Variables

Create a `.env` file inside the backend configuration according to the project's environment template.

Example:

```env
OPENROUTER_API_KEY=your_api_key_here

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/document_analyzer

REDIS_URL=redis://localhost:6379

CHROMA_PERSIST_DIRECTORY=./chroma_db

CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K=10
SIMILARITY_THRESHOLD=0.1
MAX_RETRIES=1
```

> Never commit real API keys or credentials to GitHub.

---

## 💻 Running Locally

### 1. Clone Repository

```bash
git clone https://github.com/sufiandevs/Document-Analyzer.git
cd Document-Analyzer
```

### 2. Start Backend

```bash
cd backend
pip install -r requirements.txt
```

Configure the environment variables and start FastAPI:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The React application will be available through the Vite development server.

---

## 🐳 Docker

The project includes Docker configuration for running the main services together.

Services include:

```text
PostgreSQL
Redis
Backend
Frontend
```

Start the complete stack:

```bash
docker compose up --build
```

Stop the stack:

```bash
docker compose down
```

---

## 📊 Evaluation

The project contains an evaluation dataset with **30 questions** covering different categories:

* Easy questions
* Multi-hop questions
* Citation questions
* No-answer questions
* Ambiguous questions
* Hallucination-oriented questions

The evaluation script sends questions to the local `/chat` endpoint and records retrieval and answer-related results.

Run:

```bash
cd evalution
python evaluate.py
```

The evaluation pipeline reports measurements such as:

* Retrieval score
* Source retrieval success
* Citation presence
* Answer faithfulness proxy

> The current evaluation implementation uses custom metrics rather than a full Ragas/DeepEval evaluation pipeline.

---

## 🧪 Testing

The system can be tested at multiple levels:

### Backend

```text
FastAPI → Swagger → API Endpoints
```

### RAG

```text
Document → Retrieval → Context → Answer
```

### LangGraph

```text
Query → Retrieval → Relevance → Rewrite/Answer → Verification
```

### Frontend

```text
Upload → Index → Ask Question → Receive Answer → View Citations
```

---

## 🔐 Security Considerations

* API keys should be stored in environment variables.
* `.env` files should not be committed.
* Uploaded files should be validated by extension and size.
* The backend validates chat request fields using Pydantic.
* Production deployments should restrict CORS origins.
* Sensitive credentials should be rotated if accidentally exposed.

---

## 📁 Project Structure

```text
Document-Analyzer/
│
├── backend/
│   └── app/
│       ├── agents/
│       │   └── graph.py
│       ├── api/
│       │   ├── chat.py
│       │   ├── documents.py
│       │   └── health.py
│       ├── core/
│       │   └── config.py
│       ├── models/
│       │   └── schemas.py
│       ├── rag/
│       │   ├── ingestion.py
│       │   └── retrieval.py
│       ├── services/
│       │   └── chat_service.py
│       └── main.py
│
├── frontend/
│   ├── src/
│   │   └── App.jsx
│   └── package.json
│
├── evalution/
│   ├── evaluation_dataset.json
│   └── evaluate.py
│
├── docker-compose.yml
├── render.yaml
├── .env.example
├── run.bat
└── README.md
```

---

## ⚠️ Limitations

Current limitations include:

* Some advanced retrieval capabilities are implemented but not enabled in the active LangGraph retrieval path.
* Query analysis currently uses a deterministic classification approach.
* Relevance grading currently relies on retrieval scores rather than a separate LLM grader.
* Hallucination and citation verification are currently represented by workflow checks rather than a complete independent verification model.
* The evaluation script uses custom metrics rather than Ragas/DeepEval.
* The current frontend is React + Vite rather than Next.js.

These areas provide opportunities for further improvement.

---

## 🔮 Future Improvements

Possible future enhancements include:

* True MMR retrieval in the active graph path.
* Enable BGE reranking during normal retrieval.
* LLM-based query analysis.
* LLM-based relevance grading.
* Independent citation verification.
* Stronger hallucination detection.
* Ragas/DeepEval integration.
* Streaming LLM responses.
* Authentication and authorization.
* Better observability and tracing.
* Hybrid keyword + semantic retrieval.
* Long-term conversational memory.
* Multi-agent document analysis.

---

## 📸 Screenshots

### 🖥️ Application Interface

Add a screenshot of the working React application here:

```text
docs/images/frontend.png
```

Example:

### 💬 AI Chat & Citations

Add a screenshot showing a question, AI response, and citations:

```text
docs/images/chat-response.png
```

### 📚 Document Management

Add a screenshot showing uploaded/indexed documents:

```text
docs/images/documents.png
```

### 🔧 API Documentation

Add a screenshot of FastAPI Swagger:

```text
docs/images/swagger.png
```

> Create the `docs/images/` folder and place your screenshots there. GitHub will automatically render the images using the paths above.

---

## 📌 Assignment Requirements Coverage

| Requirement                     | Implementation                        |
| ------------------------------- | ------------------------------------- |
| PDF/TXT/DOCX ingestion          | ✅                                     |
| Document cleaning               | ✅                                     |
| Configurable chunking           | ✅                                     |
| Embeddings                      | ✅                                     |
| Persistent vector database      | ✅ ChromaDB                            |
| Semantic retrieval              | ✅                                     |
| Advanced retrieval capabilities | ✅ Implemented                         |
| Reranking capability            | ✅ Implemented                         |
| Context optimization            | ✅                                     |
| Citations                       | ✅                                     |
| LangGraph workflow              | ✅                                     |
| Query rewriting                 | ✅                                     |
| Conditional routing             | ✅                                     |
| FastAPI                         | ✅                                     |
| Pydantic validation             | ✅                                     |
| React frontend                  | ✅                                     |
| PostgreSQL persistence          | ✅                                     |
| Redis                           | ✅                                     |
| Docker Compose                  | ✅                                     |
| Evaluation dataset              | ✅ 30 questions                        |
| Localhost execution             | ✅                                     |
| Cloud deployment                | Not required for localhost submission |

---

## 👨‍💻 Author

**Sufian Devs**

GitHub Repository:

https://github.com/sufiandevs/Document-Analyzer

---

## 📄 License

This project is available under the license included in the repository.
