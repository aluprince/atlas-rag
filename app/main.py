from fastapi import FastAPI
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.chat import router as chat_router

app = FastAPI(title="Atlas-RAG")

app.include_router(documents_router)
app.include_router(search_router)
app.include_router(chat_router)

@app.get("/health")
def health():
    return {"status": "ok"}