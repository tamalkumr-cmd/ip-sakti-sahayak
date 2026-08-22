import sys
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routers import query_router, docs_router, voice_router, export_router, chat_router, risk_router

app = FastAPI(
    title="IP-SAKTI Sahayak API",
    description="Regulatory & IP RAG assistant API for Ministry of Ayush",
    version="1.0.0",
    default_response_class=JSONResponse
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router.router)
app.include_router(docs_router.router)
app.include_router(voice_router.router)
app.include_router(export_router.router)
app.include_router(chat_router.router)
app.include_router(risk_router.router)

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "status": "ok",
        "message": "IP-SAKTI Sahayak API is running. Visit /docs for API documentation."
    }

@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {
        "status": "ok",
        "service": "IP-SAKTI Sahayak Backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)