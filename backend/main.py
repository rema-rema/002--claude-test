"""
FastAPI application entry point for login functionality.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.simple_config import settings
from src.features.login.routes import auth_router
from src.features.login.mock_routes import mock_auth_router

# Create FastAPI app
app = FastAPI(
    title="002 Claude Test Backend",
    description="Backend API for login functionality with Google OAuth",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])

# Include mock auth router if enabled
if settings.MOCK_AUTH_ENABLED:
    app.include_router(mock_auth_router, prefix="/api/auth", tags=["mock-authentication"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "002 Claude Test Backend is running",
            "version": "0.1.0"
        }
    )

# Root endpoint
@app.get("/")
async def root():
    return JSONResponse(
        content={
            "message": "002 Claude Test Backend API",
            "docs": "/docs",
            "health": "/health"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("BACKEND_PORT", 8000)),
        reload=True
    )