"""
Simple test FastAPI application.
Used for basic testing and debugging of FastAPI setup.
Can be run independently to verify FastAPI is working correctly.
"""

from fastapi import FastAPI

# ===========================
# CREATE TEST APP
# ===========================
# Initialize a minimal FastAPI application instance
# This is separate from the main app in main.py for testing purposes
app = FastAPI()

# ===========================
# TEST ENDPOINT
# ===========================
# Simple GET request handler for the root path "/"
# Returns a JSON response to verify the server is running
@app.get("/")
async def root():
    """
    Simple health check endpoint.
    
    Returns:
    - JSON with a greeting message
    
    Usage:
    - Run: python -m uvicorn test:app --reload
    - Visit in browser: http://localhost:8000/
    - Expected response: {"Message": "Hello World"}
    """
    return {"Message": "Hello World"}

# To run this test app:
# 1. Navigate to server directory
# 2. Run: python -m uvicorn test:app --reload --host 127.0.0.1 --port 8000
# 3. Visit: http://localhost:8000/
# 4. Check API docs at: http://localhost:8000/docs
