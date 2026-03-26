"""
Exception handling middleware for FastAPI application.
Catches any unhandled exceptions during request processing and returns a standardized error response.
This prevents server crashes and provides meaningful error messages to clients.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from loggger import logger

async def catch_exception_middleware(request: Request, call_next):
    """
    Middleware that wraps all incoming requests with exception handling.
    
    Parameters:
    - request: The incoming HTTP request object
    - call_next: Function to proceed to next middleware/route handler
    
    Returns:
    - Response from the route handler if successful
    - JSONResponse with error message (status 500) if exception occurs
    
    Purpose:
    1. Catches ANY unhandled exceptions in the request pipeline
    2. Logs the full exception trace for debugging
    3. Returns user-friendly JSON error response
    4. Prevents exposing sensitive stack traces to clients
    """
    try:
        # EXECUTE REQUEST
        # call_next(request) passes request to the next middleware and route handler
        # If everything succeeds, the response is returned
        return await call_next(request)
    
    except Exception as exc:
        # EXCEPTION CAUGHT
        # Any unhandled exception during request processing is caught here
        
        # LOG EXCEPTION
        # logger.exception() logs full exception trace for debugging
        # Useful for tracking down server errors in logs
        logger.exception("Unhandled exception")
        
        # RETURN ERROR RESPONSE
        # Return standardized JSON error response to client
        # status_code=500: Internal Server Error (standard error code)
        # content={"error": str(exc)}: Error message converted to string
        return JSONResponse(
            status_code=500, 
            content={"error": str(exc)}
        )
