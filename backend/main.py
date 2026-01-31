# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
import logging
from pydantic import BaseModel
import asyncio

app = FastAPI(title="Market Without Money API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)  # No prefix, so /ws is available at root

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Market Without Money API"}

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    pass

@app.get("/health")
async def health_check():
    """Detailed Health check endpoint"""
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)