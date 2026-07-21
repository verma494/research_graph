from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from .routes import chat, explore

app = FastAPI(
    title="Hybrid GraphRAG Assistant API",
    description="Backend API for the Phase 6 production web application.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev, restrict in prod
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(explore.router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
