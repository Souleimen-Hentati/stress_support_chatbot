# 🤖 MediBot - Stress Support Chatbot

## 🎯 Overview

**MediBot** is a conversational assistant focused on **mental wellbeing support in the stress field**.
It provides calm, practical guidance (breathing, grounding, routines, coping steps) through chat.

---

## ✅ Core Purpose

- Help users talk through stress in a supportive tone
- Provide practical, low-risk coping suggestions
- Encourage help-seeking behavior when risk language appears
- Keep interaction simple: user message -> assistant response

---

## ⚠️ Safety Scope

MediBot is not a replacement for a licensed clinician or emergency care.

- No diagnosis
- No medication guidance
- If crisis/self-harm intent is detected, the bot returns an escalation response encouraging immediate local emergency or crisis hotline support

---

## 🧰 Tools, Frameworks, and Libraries Used

### Languages and Runtime

- Python `3.11+`
- Virtual environment support (`venv`)

### Frontend

- **Streamlit**: chat UI and app shell
- **Requests**: sends user prompts from UI to backend API

### Backend

- **FastAPI**: REST API server
- **Uvicorn**: ASGI server to run FastAPI
- **python-multipart**: handles `Form(...)` input parsing in FastAPI
- **Pydantic**: data validation support via FastAPI ecosystem
- **FAISS (faiss-cpu)**: vector index for RAG retrieval

### LLM Integration

- **langchain-openai**
- **langchain-anthropic**
- **langchain + langchain-community**
- **Provider-configurable chat API**
- **Embeddings API (OpenAI-compatible)**

---

## 📁 Project Architecture

PFA_Medical_Assistant/
├── client/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── components/
│   │   ├── chatUI.py
│   │   └── history_download.py
│   └── utils/
│       └── api.py
├── server/
│   ├── main.py
│   ├── loggger.py
│   ├── requirements.txt
│   ├── build_rag_index.py
│   ├── vectorstore/
│   ├── middlewares/
│   │   └── exception_handlers.py
│   ├── routes/
│   │   └── ask_questions.py
│   └── modules/
│       ├── llm.py
│       └── rag.py
├── pyproject.toml
└── README.md
```

## 🧱 Prerequisites

- Python `3.11` or newer
- API key for your OpenRouter-compatible provider

---
