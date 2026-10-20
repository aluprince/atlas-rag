
from fastapi import FastAPI

app = FastAPI(
    title="Atlas RAG",
    description="Startup diagnostic",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "atlas-rag",
    }
