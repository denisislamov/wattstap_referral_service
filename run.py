#!/usr/bin/env python3
"""
Convenience script to run the WattsTap Referral Service.

Usage:
    python run.py
    
Or with custom host/port:
    HOST=127.0.0.1 PORT=8080 python run.py
"""

import uvicorn

from app.config import settings


if __name__ == "__main__":
    print(f"Starting {settings.app_name}...")
    print(f"Environment: {settings.app_env}")
    print(f"Debug: {settings.debug}")
    print(f"Server: http://{settings.host}:{settings.port}")
    print(f"API Docs: http://{settings.host}:{settings.port}/docs")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )


