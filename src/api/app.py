"""FastAPI application for Storyplex Analytics."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import analytics, fandoms, jobs, works
from src.db.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler."""
    # Startup
    init_db()
    yield
    # Shutdown


app = FastAPI(
    title="Storyplex Analytics",
    description="Multi-platform fanfiction and web novel analytics API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(works.router, prefix="/api/works", tags=["Works"])
app.include_router(fandoms.router, prefix="/api/fandoms", tags=["Fandoms"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
