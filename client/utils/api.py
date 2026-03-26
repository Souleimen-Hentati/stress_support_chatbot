import requests
from config import API_URL


def ask_question(question: str):
    """
    Sends a user message to the backend for stress-support response generation.
    
    Parameters:
    - question: The user's question as a string
    
    Returns:
    - HTTP response object containing chatbot response content
    """
    return requests.post(f"{API_URL}/ask_questions", data={"question": question}, timeout=30)


def ask_question_rag_compare(question: str):
    """Send a user message to compare RAG chain vs RAG agent strategies."""
    return requests.post(
        f"{API_URL}/ask_questions_rag_compare",
        data={"question": question},
        timeout=45,
    )