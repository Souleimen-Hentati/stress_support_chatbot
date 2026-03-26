import requests
from config import API_URL


def ask_question(question: str):
    return requests.post(f"{API_URL}/ask_questions", data={"question": question}, timeout=30)


def ask_question_rag_compare(question: str):
    return requests.post(
        f"{API_URL}/ask_questions_rag_compare",
        data={"question": question},
        timeout=45,
    )
