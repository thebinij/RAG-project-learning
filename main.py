#!/usr/bin/env python3
"""
Entry point for LegendaryCorp AI Assistant
Usage: python main.py
"""

import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )
