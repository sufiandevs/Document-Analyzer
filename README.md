#  Document Analyzer — Agentic RAG System

> An intelligent full-stack **Retrieval-Augmented Generation (RAG)** application for uploading documents, asking questions, retrieving relevant information, and generating answers with document-based citations.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green?logo=fastapi)
![React](https://img.shields.io/badge/React-18-blue?logo=react)
![LangChain](https://img.shields.io/badge/LangChain-RAG-orange)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_RAG-purple)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-Cache-red?logo=redis)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)

---

##  Overview

**Document Analyzer** is a full-stack AI document-question-answering system built around an advanced RAG architecture.

Users can upload **PDF, TXT, and DOCX** documents and ask questions about their contents through a React web interface.

The system combines:

* LangChain for document processing and RAG components
* ChromaDB for persistent vector storage
* Sentence Transformers for embeddings
* LangGraph for agentic workflow orchestration
* FastAPI for backend APIs
* PostgreSQL for chat persistence
* Redis for supporting application services
* React + Vite for the frontend
* OpenRouter for LLM access

---

##  Key Features

| Feature                  | Implementation               |
| ------------------------ | ---------------------------- |
|  PDF/TXT/DOCX Upload   | Supported                    |
|  Document Cleaning     | Implemented                  |
|  Configurable Chunking | 512 chunk size / 50 overlap  |
|  Embeddings            | `all-MiniLM-L6-v2`           |
|  Vector Database      | ChromaDB                     |
|  Semantic Retrieval    | Implemented                  |
|  Multi-Query Retrieval | Implemented                  |
|  Reranking             | BGE reranker implemented     |
|  Context Optimization  | Implemented                  |
|  Citations             | Document/page/chunk metadata |
|  Agentic Workflow      | LangGraph                    |
|  Query Rewriting       | Implemented                  |
|  REST API              | FastAPI                      |
|  Chat Sessions         | PostgreSQL                   |
|  Web Interface        | React + Vite                 |
|  Docker                | Docker Compose               |
|  Evaluation Dataset    | 30 questions                 |

---

#  System Architecture

```mermaid
flowchart TB
    U[" User"]

    F[" React + Vite Frontend"]

    API[" FastAPI Backend"]

    G[" LangGraph Agentic RAG"]

    QA[" Query Analyzer"]
    R[" Retriever"]
    RG[" Relevance Grader"]
    RW[" Query Rewriter"]
    AG[" Answer Generator"]
    VC[" Citation / Verification"]

    C[" ChromaDB"]
    P[" PostgreSQL"]
    RED[" Redis"]

    LLM[" LLM / OpenRouter"]
    EMB[" Sentence Transformer Embeddings"]

    U --> F
    F --> API
    API --> G

    G --> QA
    QA --> R
    R --> C
    R --> RG

    RG -->|Relevant| AG
    RG -->|Not Relevant| RW
    RW --> R

    AG --> LLM
    AG --> VC
    VC --> F

    API --> P
    API --> RED

    EMB --> C
```

---

#  Document Ingestion Pipeline

Uploaded documents pass through a multi-stage ingestion pipeline before becoming searchable.

```mermaid
flowchart LR
    A[" Upload Document"]
    B[" Detect File Type"]
    C[" Load Document"]
    D[" Clean Text"]
    E[" Split into Chunks"]
    F[" Generate Embeddings"]
    G[" Store in ChromaDB"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
```

### Supported Formats

| Format | Loader         |
| ------ | -------------- |
| PDF    | PyPDFLoader    |
| TXT    | TextLoader     |
| DOCX   | Docx2txtLoader |

### Chunking Configuration

| Parameter       |                                    Value |
| --------------- | ---------------------------------------: |
| Chunk Size      |                                      512 |
| Chunk Overlap   |                                       50 |
| Vector Store    |                                 ChromaDB |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |

Document metadata such as filename, document ID, page number, and chunk index is preserved for retrieval and citation generation.

---

#  Advanced RAG Pipeline

```mermaid
flowchart LR
    Q[" User Question"]
    E[" Query Embedding"]
    S[" Semantic Search"]
    M[" Multi-Query Retrieval"]
    RR[" Reranking"]
    CO[" Context Optimization"]
    C[" Citation Creation"]
    L[" LLM"]
    A[" Final Answer"]

    Q --> E
    E --> S
    S --> M
    M --> RR
    RR --> CO
    CO --> C
    C --> L
    L --> A
```

The retrieval module provides semantic search, multi-query retrieval, reranking, duplicate removal, relevance filtering, context-length optimization, and citation generation.



---

#  LangGraph Agentic Workflow

The system uses LangGraph to organize the RAG process into conditional nodes.

```mermaid
flowchart TD
    START(["START"])

    QA[" Query Analyzer"]

    R[" Retriever"]

    G[" Relevance Grader"]

    A[" Answer Generator"]

    C[" Citation / Hallucination Check"]

    RW[" Query Rewriter"]

    FINAL[" Final Answer"]

    END(["END"])

    START --> QA
    QA --> R
    R --> G

    G -->|Relevant| A
    G -->|Not Relevant| RW

    RW --> R

    A --> C

    C -->|Verified| FINAL
    C -->|Retry| RW

    FINAL --> END
```

This workflow allows the application to retry retrieval when the initial retrieved context is not considered sufficiently relevant.

---

#  Agent State

The LangGraph workflow maintains structured state containing information such as:

| State Field           | Purpose                        |
| --------------------- | ------------------------------ |
| `question`            | Original user question         |
| `rewritten_query`     | Improved query after rewriting |
| `documents`           | Retrieved document chunks      |
| `relevance_score`     | Retrieval relevance            |
| `answer`              | Generated answer               |
| `citations`           | Source information             |
| `retry_count`         | Number of retrieval retries    |
| `max_retries`         | Maximum retry limit            |
| `query_type`          | Query classification           |
| `needs_retrieval`     | Retrieval decision             |
| `hallucination_check` | Verification state             |
| `citation_check`      | Citation verification state    |

---

#  Citations

The system retains source metadata during retrieval.

A citation can contain:

| Field    | Description              |
| -------- | ------------------------ |
| Document | Source filename          |
| Page     | Source page              |
| Chunk    | Chunk index              |
| Score    | Retrieval score          |
| Text     | Retrieved source content |

Example:

```text
Answer:
The document explains that...

Sources:
[1] research.pdf — Page 3
[2] research.pdf — Page 7
```

This allows users to trace generated answers back to retrieved document content.

---

#  FastAPI Backend

The backend exposes a REST API using FastAPI.

### Base URL

```text
http://localhost:8000
```

### API Documentation

```text
http://localhost:8000/docs
```

```text
http://localhost:8000/redoc
```

## API Endpoints

| Method   | Endpoint                     | Purpose                          |
| -------- | ---------------------------- | -------------------------------- |
| `GET`    | `/health`                    | Check application/service health |
| `POST`   | `/documents/upload`          | Upload and process a document    |
| `GET`    | `/documents`                 | List uploaded documents          |
| `DELETE` | `/documents/{document_id}`   | Delete a document                |
| `POST`   | `/chat`                      | Ask a question                   |
| `GET`    | `/chat/history/{session_id}` | Retrieve chat history            |
| `GET`    | `/chat/sessions`             | Retrieve chat sessions           |

### Upload Document

```http
POST /documents/upload
```

Example:

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@example.pdf"
```

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

#  Frontend

The frontend is built using **React 18 + Vite**.

It provides:

*  Document upload
*  Document management
*  AI chat
*  Citation display
*  Chat sessions
*  Conversation history

### Application Screenshot

![Document Analyzer UI](docs/images/frontend.png)

---

#  Document Management

Users can upload supported documents and manage indexed files from the application interface.

![Document Management](docs/images/documents.png)

---

#  AI Chat & Citations

Users can ask questions and receive answers generated from retrieved document context.

![AI Chat Response](docs/images/chat-response.png)

---

#  Data Persistence

```mermaid
flowchart LR
    APP["🚀 Application"]

    CH[" ChromaDB"]
    PG[" PostgreSQL"]
    RD[" Redis"]

    APP --> CH
    APP --> PG
    APP --> RD
```

### ChromaDB

Stores:

* Document chunks
* Embeddings
* Document metadata
* Retrieval information

### PostgreSQL

Stores:

* Chat sessions
* User messages
* Assistant messages
* Conversation history

### Redis

Provides supporting in-memory application services.

---

#  Environment Configuration

Create your environment configuration using `.env.example`.

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


---

#  Local Installation

## 1. Clone the Repository

```bash
git clone https://github.com/sufiandevs/Document-Analyzer.git
cd Document-Analyzer
```

## 2. Start the Backend

```bash
cd backend
pip install -r requirements.txt
```

Configure environment variables and run:

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

## 3. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the frontend using the URL shown by Vite.

---

# 🐳 Docker

The project includes Docker Compose configuration for the main application services.

```mermaid
flowchart TB
    D["🐳 Docker Compose"]

    F["Frontend"]
    B["Backend"]
    P["PostgreSQL"]
    R["Redis"]

    D --> F
    D --> B
    D --> P
    D --> R
```

Start the application stack:

```bash
docker compose up --build
```

Stop the stack:

```bash
docker compose down
```

---

# 📊 Evaluation

The project includes an evaluation dataset containing **30 questions**.

The dataset covers:

| Category      | Purpose                                            |
| ------------- | -------------------------------------------------- |
| Easy          | Basic document questions                           |
| Multi-hop     | Questions requiring multiple pieces of information |
| Citation      | Source/citation-focused questions                  |
| No Answer     | Questions where information is unavailable         |
| Ambiguous     | Unclear or underspecified questions                |
| Hallucination | Testing unsupported answers                        |

Run the evaluation script:

```bash
cd evalution
python evaluate.py
```

The current evaluation implementation records:

* Retrieval score
* Source retrieval success
* Citation presence
* Answer faithfulness proxy

> The current implementation uses custom evaluation logic rather than Ragas or DeepEval.

---

#  Testing Strategy

The system can be tested across the complete application pipeline:

```mermaid
flowchart LR
    U["Upload"]
    I["Index"]
    Q["Question"]
    R["Retrieve"]
    G["Grade"]
    A["Generate"]
    C["Citations"]

    U --> I
    I --> Q
    Q --> R
    R --> G
    G --> A
    A --> C
```

Testing areas include:

* Document upload
* Document processing
* Vector storage
* Semantic retrieval
* Query rewriting
* Answer generation
* Citations
* API endpoints
* Chat history
* Frontend interaction

---

#  Security

The project follows basic security practices:

* API credentials are stored through environment variables.
* `.env` files should not be committed.
* Uploaded file types are validated.
* Upload size is restricted.
* Chat requests use Pydantic validation.
* Production deployments should use restricted CORS settings.
* Exposed credentials should be rotated immediately.

---

#  Project Structure

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
├── docs/
│   └── images/
│       ├── frontend.png
│       ├── documents.png
│       └── chat-response.png
│
├── docker-compose.yml
├── render.yaml
├── .env.example
├── run.bat
├── README.md
└── LICENSE
```

---

#  Limitations

Some advanced capabilities are implemented in the codebase but are not currently enabled in the main LangGraph execution path.

Current limitations include:

* MMR/reranking are implemented but disabled in the active retrieval call.
* Query analysis currently uses deterministic classification.
* Relevance grading currently uses retrieval-score logic.
* Hallucination/citation verification is represented in the workflow but does not currently perform independent LLM verification.
* Evaluation uses custom metrics rather than Ragas/DeepEval.
* Frontend uses React + Vite rather than Next.js.

---

#  Future Improvements

* Enable true MMR retrieval in the active workflow.
* Enable BGE reranking in normal graph execution.
* Implement LLM-based query analysis.
* Implement independent relevance grading.
* Add stronger hallucination detection.
* Add Ragas/DeepEval evaluation.
* Add streaming responses.
* Add authentication and authorization.
* Add hybrid keyword + semantic search.
* Add long-term conversational memory.
* Add observability and tracing.
* Extend the system toward multi-agent document analysis.

---

#  API Documentation

FastAPI automatically provides interactive API documentation through Swagger UI.

![FastAPI Swagger](docs/images/swagger.png)

---


#  Author

**Sufian Devs**

GitHub Repository:

https://github.com/sufiandevs/Document-Analyzer

---

# 📄 License

This project is available under the license included in the repository.
