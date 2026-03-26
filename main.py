"""
Root application entry point.
Resolves module path and exports the FastAPI app for deployment.
This wrapper allows running the app from the workspace root directory.
"""

import sys
from pathlib import Path

# ===========================
# SETUP: PYTHON PATH
# ===========================
# Add server directory to Python's module search path
# This allows imports like "from server.main import app"
# Without this, Python wouldn't find modules in the server/ directory
sys.path.insert(0, str(Path(__file__).parent / "server"))

# ===========================
# IMPORT FASTAPI APP
# ===========================
# Import the configured FastAPI application from server/main.py
# This app contains:
# - All route handlers (/upload_pdfs, /ask_questions)
# - CORS middleware (allows frontend communication)
# - Exception handler middleware (catches errors)
from server.main import app

# ===========================
# EXPORT APP
# ===========================
# Make the app available for external use
# This allows uvicorn to find and run the app
# Usage: python -m uvicorn main:app --reload
__all__ = ["app"]

# Note: This file can also be run directly as an entry point
# It serves as a bridge between the workspace root and the server module
