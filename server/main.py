"""
FastAPI main application file.
Sets up the API server, middleware, and routes for the Medical Assistant backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middlewares.exception_handlers import catch_exception_middleware
from routes.ask_questions import router as ask_router

app = FastAPI(
    title="Stress Support Chatbot API",
    description="API for a stress-focused mental wellbeing chatbot"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(catch_exception_middleware)

app.include_router(ask_router)
