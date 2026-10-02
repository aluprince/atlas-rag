from fastapi import FastAPI

app = FastAPI(
    title="Atlas RAG",
    description="Enterprise knowledge assistant powered by retrieval-augmented generation.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "atlas-rag",
    }