# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
import asyncio

app = FastAPI(title="Market Without Money API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Market Without Money API"}

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)