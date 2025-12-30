"""Conductor Server - FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Conductor",
    description="Async AI development service - submit requirements, get working code",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": "Conductor",
        "description": "Async AI development service",
        "docs": "/docs",
    }