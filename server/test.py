from fastapi import FastAPI

app = FastAPI()

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
