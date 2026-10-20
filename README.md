# Atlas RAG

## Author

Built by ALU ONARI PRINCE  
Backend & AI Integration Engineer

Atlas RAG is a document-centric retrieval and question-answering system built with Python, FastAPI, PostgreSQL, and pgvector. It allows users to upload files such as PDF, DOCX, TXT, and Markdown, split them into searchable chunks, embed those chunks, and retrieve relevant passages for grounded answers with a Groq-backed LLM.

This repository contains the backend API and a Streamlit frontend for local use and demos.

## Features

- Upload and process documents in supported formats
- Extract text from uploaded files
- Split text into chunked passages
- Generate embeddings and store them in PostgreSQL with pgvector
- Search by similarity using semantic query embeddings
- Ask questions against uploaded documents with source-backed answers
- Expose a REST API with interactive docs at /docs
- Provide a simple Streamlit UI for testing the system locally

## Tech stack

- Python 3.12+
- FastAPI
- SQLAlchemy
- PostgreSQL + pgvector
- Sentence transformers for embeddings
- Groq for answer generation
- Streamlit for local frontend
- Docker Compose for the database

## Project structure

```text
atlas-rag/
├── app/
│   ├── api/
│   │   ├── chat.py
│   │   ├── documents.py
│   │   └── search.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── init_db.py
│   │   ├── models.py
│   │   ├── repositories.py
│   │   └── session.py
│   ├── embeddings/
│   ├── ingestion/
│   ├── retrieval/
│   │   └── search.py
│   ├── services/
│   │   └── llm.py
│   ├── main.py
│   └── scripts/
├── frontend/
│   └── streamlit_app.py
├── tests/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── README.md
└── .gitignore
```

## How it works

1. A document is uploaded through the API or the Streamlit UI.
2. The app validates the file type and size.
3. The document is parsed into text pages.
4. Content is split into chunks.
5. Each chunk is embedded and stored in the PostgreSQL pgvector table.
6. A user question is embedded and compared against stored chunks.
7. The best matching chunks are used as context.
8. The Groq model generates a grounded answer with source references.

## Architecture

The application is structured as a lightweight retrieval-augmented generation service with a REST API backend and an optional UI layer.

```mermaid
flowchart LR
    U[User] --> S[Streamlit Frontend
    frontend/streamlit_app.py]
    U --> C[Client / API Consumer]

    S -->|HTTP requests| A[FastAPI Backend
    app.main:app]
    C -->|HTTP requests| A

    A --> D[Documents API
    /documents/]
    A --> R[Search API
    /search/]
    A --> CH[Chat API
    /chat/]

    D --> I[Ingestion Pipeline
    loaders + chunker]
    I --> E[Embedding Generation]
    E --> PG[(PostgreSQL + pgvector)]

    R --> SR[Retrieval Search]
    SR --> PG

    CH --> SR
    CH --> LLM[Groq LLM Service]
    LLM --> A

    A --> RESP[Grounded answer + source metadata]
    RESP --> S
```

### Main components

- FastAPI application: acts as the API gateway and exposes the `/health`, `/documents`, `/search`, and `/chat` endpoints.
- Document ingestion pipeline: validates files, parses them, and chunks the extracted text before embedding.
- Embedding layer: converts text chunks into vector representations for similarity search.
- PostgreSQL + pgvector: stores document metadata and vector embeddings.
- Retrieval layer: embeds user questions and finds the nearest matching document chunks.
- Chat / answer layer: builds a prompt from relevant chunks and sends it to Groq.
- Streamlit frontend: provides a local browser-based interface for uploading documents and asking questions.

## Current limitations

The repository is a solid local prototype, but it has some practical limitations that are worth knowing before production deployment:

- No authentication or user-level authorization is implemented.
- There is no background job queue or async document processing; uploads are handled synchronously.
- File support is intentionally narrow and limited to PDF, DOCX, TXT, and Markdown files.
- The application is configured for a single Groq provider and currently rejects other LLM providers.
- There is no built-in document deletion, re-indexing, or bulk management flow.
- Database and app configuration are simple local defaults rather than hardened production settings.
- The app does not add observability, rate limiting, caching, retry policies, or monitoring by default.
- The max upload size is fixed at 10 MB per file in the document endpoint.

## Prerequisites

- Python 3.12+
- Docker Desktop or Docker Engine
- A Groq API key
- Git

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/aluprince/atlas-rag.git
cd atlas-rag
```

### 2. Create and activate a virtual environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you are using the project metadata instead of requirements, this project also exposes dependencies through `pyproject.toml`.

### 4. Start PostgreSQL with pgvector

The project includes a Docker Compose setup for the database:

```bash
docker compose up -d
```

This starts a PostgreSQL container on port `5433` with:

- database: `atlas_rag`
- user: `atlas`
- password: `atlas_dev_password`

The default application database URL is:

```env
DATABASE_URL=postgresql+psycopg://atlas:atlas_dev_password@localhost:5433/atlas_rag
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg://atlas:atlas_dev_password@localhost:5433/atlas_rag
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

The app loads `.env` automatically via `pydantic-settings`.

> Do not commit real secrets to Git. Keep your API key in a local `.env` file only.

### 6. Initialize the database schema

```bash
python -m app.db.init_db
```

### 7. Run the backend

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 8. Run the Streamlit frontend (optional)

In a second terminal:

```bash
streamlit run frontend/streamlit_app.py
```

By default the frontend connects to the FastAPI backend at `http://127.0.0.1:8000`.

If needed, override it:

```bash
ATLAS_API_URL=http://127.0.0.1:8000 streamlit run frontend/streamlit_app.py
```

## API endpoints

### Health

```http
GET /health
```

Returns the service health status.

### Upload document

```http
POST /documents/
```

Form-data body:

- `file`: uploaded document

Supported file types:

- `.pdf`
- `.docx`
- `.txt`
- `.md`

### Search documents

```http
POST /search/
```

Example JSON body:

```json
{
  "question": "What does the document say about security?",
  "limit": 5,
  "document_id": 1
}
```

Returns matching chunks with similarity scores.

### Chat with documents

```http
POST /chat/
```

Example JSON body:

```json
{
  "question": "Summarize the key points from this document.",
  "limit": 5,
  "document_id": 1
}
```

Returns a grounded answer based on the retrieved context and includes source metadata.

## Local deployment notes

This project is designed for a straightforward local deployment with a PostgreSQL database and a Python web server. For production-like deployments, you would typically:

- run the API behind a reverse proxy or container orchestration layer
- configure a managed PostgreSQL instance with pgvector enabled
- store secrets in a real secret manager or environment injection system
- add TLS, rate limiting, and health monitoring
- add a production-grade LLM provider setup and failure handling

## Notes on current implementation

- The backend registers three routers: documents, search, and chat.
- The document ingestion pipeline creates embeddings and stores them in a `document_chunks` table.
- Similarity matching uses cosine distance over pgvector.
- The chat endpoint requires a valid `GROQ_API_KEY` and uses `llama-3.3-70b-versatile` by default.
- The app is intentionally small and suitable for a proof-of-concept or internal knowledge assistant.

## Example deployment commands

```bash
# Start database
docker compose up -d

# Initialize schema
python -m app.db.init_db

# Run API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run frontend
streamlit run frontend/streamlit_app.py
```

## License

This project currently does not specify a custom license in the repository metadata. Please check the repository and package configuration before using it in a production environment or public release.
