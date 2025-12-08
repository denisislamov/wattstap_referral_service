"""
WattsTap Referral Service - Main application entry point.

FastAPI application for handling referral system in WattsTap Telegram Mini App.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import settings
from app.database import init_db, close_db
from app.routers import auth_router, social_router
from app.routers.dev import router as dev_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Initializes database on startup and closes connections on shutdown.
    """
    # Startup
    print(f"Starting {settings.app_name} v{__version__}")
    print(f"Environment: {settings.app_env}")
    print(f"Debug mode: {settings.debug}")
    
    await init_db()
    print("Database initialized")
    
    yield
    
    # Shutdown
    await close_db()
    print("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    Backend service for WattsTap Telegram Mini App referral system.
    
    ## Features
    
    - **Authentication**: Secure authentication via Telegram WebApp initData
    - **Referral System**: Invite friends and earn bonus watts
    - **Friends**: Track your friends and referral statistics
    
    ## Authentication
    
    All endpoints except `/auth/telegram` require a JWT token in the Authorization header:
    ```
    Authorization: Bearer <token>
    ```
    
    Get your token by calling `POST /auth/telegram` with your Telegram initData.
    """,
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred" if settings.is_production else str(exc)
            }
        }
    )


# Include routers
app.include_router(auth_router)
app.include_router(social_router)

# Include dev router only in non-production
if not settings.is_production:
    app.include_router(dev_router)


# Health check endpoint
@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns service health status"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns basic service information for monitoring.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.app_env
    }


@app.get(
    "/",
    tags=["Health"],
    summary="Root endpoint",
    include_in_schema=False
)
async def root():
    """Root endpoint redirect to docs."""
    return {
        "service": settings.app_name,
        "version": __version__,
        "docs": "/docs" if settings.debug else "disabled"
    }


# Entry point for running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )


