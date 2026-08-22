import sys
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routers import (
    query_router,
    docs_router,
    voice_router,
    export_router,
    chat_router,
    risk_router
)

app = FastAPI(
    title="IP-SAKTI Sahayak API",
    description="Regulatory & IP RAG assistant API for Ministry of Ayush",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# ROOT MONITOR / HEALTH ENDPOINT
# Supports both GET and POST
# --------------------------------------------------

@app.get("/")
async def root_get():
    return {
        "status": "ok",
        "message": "IP-SAKTI Sahayak Backend is running",
        "service": "IP-SAKTI Sahayak API",
        "version": "1.0.0"
    }


@app.post("/")
async def root_post(request: Request):
    return {
        "status": "ok",
        "message": "IP-SAKTI Sahayak Backend is running",
        "service": "IP-SAKTI Sahayak API",
        "version": "1.0.0"
    }


# --------------------------------------------------
# HEALTH ENDPOINT
# --------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "IP-SAKTI Sahayak Backend",
        "version": "1.0.0"
    }


# --------------------------------------------------
# REGISTER API ROUTERS
# --------------------------------------------------

app.include_router(query_router.router)
app.include_router(docs_router.router)
app.include_router(voice_router.router)
app.include_router(export_router.router)
app.include_router(chat_router.router)
app.include_router(risk_router.router)


# --------------------------------------------------
# LOCAL DEVELOPMENT
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )