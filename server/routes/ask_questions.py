import asyncio
from typing import Any
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from modules.llm import (
    SAFETY_SYSTEM_PROMPT,
    get_compare_models,
    get_stress_support_response,
    invoke_specific_model,
)
from modules.rag import (
    get_stress_support_rag_agent_response,
    get_stress_support_rag_chain_response,
    get_stress_support_rag_messages,
    get_stress_support_rag_response,
)
from loggger import logger
import re

router = APIRouter()

SIMPLE_PATTERNS = [
    r'^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|howdy)(\s+(there|everyone))?[\s!.?]*$',
    r'^(how\s+are\s+you|what\'?s\s+up|sup)[\s!.?]*$',
    r'^(thanks?|thank\s+you|thx)[\s!.?]*$',
    r'^(bye|goodbye|see\s+you|later)[\s!.?]*$',
    r'^(yes|no|ok|okay|sure|alright)[\s!.?]*$',
]

CRISIS_PATTERNS = [
    r"\b(kill\s*myself|suicide|end\s*my\s*life|want\s*to\s*die|self[-\s]?harm|hurt\s*myself)\b",
    r"\b(can't\s*go\s*on|no\s*reason\s*to\s*live|i\s*am\s*done)\b",
]

def is_simple_query(query: str) -> bool:
    query_lower = query.lower().strip()
    for pattern in SIMPLE_PATTERNS:
        if re.match(pattern, query_lower):
            return True
    return False

def has_crisis_language(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(re.search(pattern, query_lower) for pattern in CRISIS_PATTERNS)

def get_simple_response(query: str) -> dict:
    query_lower = query.lower().strip()
    
    if re.match(r'^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|howdy)', query_lower):
        return {
            "response": "Hello! I'm MediBot, your stress support assistant. I'm here to help you manage stress with practical, supportive steps. How are you feeling today?",
            "sources": []
        }
    
    if re.match(r'^(how\s+are\s+you|what\'?s\s+up|sup)', query_lower):
        return {
            "response": "Thank you for asking. I'm here to support you with stress and emotional wellbeing. What feels most stressful right now?",
            "sources": []
        }
    
    if re.match(r'^(thanks?|thank\s+you|thx)', query_lower):
        return {
            "response": "You're welcome! Feel free to ask if you have any more questions.",
            "sources": []
        }
    
    if re.match(r'^(bye|goodbye|see\s+you|later)', query_lower):
        return {
            "response": "Goodbye. Take care of yourself, and come back anytime you need support.",
            "sources": []
        }
    
    if re.match(r'^(yes|no|ok|okay|sure|alright)', query_lower):
        return {
            "response": "I understand. If you want, I can help you with one simple stress-reduction step right now.",
            "sources": []
        }
    
    return {
        "response": "I'm here to support you. Share what has been stressful lately, and we can work through it together.",
        "sources": []
    }

@router.post("/ask_questions")
async def ask_questions(question: str = Form(...)):
    try:
        logger.info(f"User query: {question}")

        if has_crisis_language(question):
            logger.warning("Crisis-language query detected - returning escalation response")
            return {
                "response": (
                    "I'm really glad you shared this. You deserve immediate support right now. "
                    "If you're in immediate danger or might act on these thoughts, please call your local emergency services now. "
                    "You can also contact a trusted person or a crisis hotline in your country right away. "
                    "If you want, I can stay with you while you take that first step and help you write a short message to ask for help."
                ),
                "sources": [],
            }

        if is_simple_query(question):
            logger.info("Simple query detected - using fast path")
            response = get_simple_response(question)
            logger.info("Query handled via fast path")
            return response

        rag_answer, sources, used_rag = get_stress_support_rag_response(question)

        if used_rag:
            logger.info("Query handled with RAG retrieval")
            return {"response": rag_answer, "sources": sources, "mode": "rag"}

        answer = get_stress_support_response(question)
        logger.info("Query handled with direct LLM fallback")
        return {"response": answer, "sources": [], "mode": "llm"}

    except Exception as e:
        logger.exception("Error during question processing")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/ask_questions_compare")
async def ask_questions_compare(question: str = Form(...)):
    try:
        logger.info(f"Compare query: {question}")

        if has_crisis_language(question):
            logger.warning("Crisis-language query detected during comparison")
            response = (
                "I'm really glad you shared this. You deserve immediate support right now. "
                "If you're in immediate danger or might act on these thoughts, please call your local emergency services now. "
                "You can also contact a trusted person or a crisis hotline in your country right away. "
                "If you want, I can stay with you while you take that first step and help you write a short message to ask for help."
            )
            return {
                "question": question,
                "mode": "crisis",
                "sources": [],
                "results": [{"model": "safety-escalation", "response": response}],
            }

        if is_simple_query(question):
            logger.info("Simple query detected during comparison")
            simple = get_simple_response(question)
            return {
                "question": question,
                "mode": "simple",
                "sources": simple.get("sources", []),
                "results": [{"model": "fast-path", "response": simple["response"]}],
            }

        models = get_compare_models()
        if not models:
            return JSONResponse(
                status_code=400,
                content={"error": "No compare models configured. Set COMPARE_MODELS in server/.env."},
            )

        rag_messages, sources, used_rag = get_stress_support_rag_messages(question)
        messages = (
            rag_messages
            if used_rag
            else [
                {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ]
        )

        results: list[dict[str, str]] = []
        for model in models:
            try:
                answer = invoke_specific_model(messages, model)
                results.append({"model": model, "response": answer})
            except Exception as exc:
                logger.exception(f"Model compare failure: {model}")
                results.append({"model": model, "error": str(exc)})

        return {
            "question": question,
            "mode": "rag" if used_rag else "llm",
            "sources": sources if used_rag else [],
            "results": results,
        }

    except Exception as e:
        logger.exception("Error during compare processing")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/ask_questions_rag_chain")
async def ask_questions_rag_chain(question: str = Form(...)):
    try:
        logger.info(f"RAG chain query: {question}")

        if has_crisis_language(question):
            logger.warning("Crisis-language query detected during RAG chain processing")
            return {
                "question": question,
                "mode": "crisis",
                "strategy": "rag-chain",
                "response": (
                    "I'm really glad you shared this. You deserve immediate support right now. "
                    "If you're in immediate danger or might act on these thoughts, please call your local emergency services now. "
                    "You can also contact a trusted person or a crisis hotline in your country right away. "
                    "If you want, I can stay with you while you take that first step and help you write a short message to ask for help."
                ),
                "sources": [],
            }

        if is_simple_query(question):
            logger.info("Simple query detected during RAG chain processing")
            simple = get_simple_response(question)
            return {
                "question": question,
                "mode": "simple",
                "strategy": "fast-path",
                "response": simple["response"],
                "sources": simple.get("sources", []),
            }

        answer, sources, used_rag = await asyncio.to_thread(get_stress_support_rag_chain_response, question)
        if used_rag:
            return {
                "question": question,
                "mode": "rag",
                "strategy": "rag-chain",
                "response": answer,
                "sources": sources,
            }

        fallback = await asyncio.to_thread(get_stress_support_response, question)
        return {
            "question": question,
            "mode": "llm-fallback",
            "strategy": "rag-chain",
            "response": fallback,
            "sources": [],
        }

    except Exception as e:
        logger.exception("Error during RAG chain processing")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/ask_questions_rag_compare")
async def ask_questions_rag_compare(question: str = Form(...)):
    try:
        logger.info(f"RAG strategy compare query: {question}")

        if has_crisis_language(question):
            logger.warning("Crisis-language query detected during RAG strategy comparison")
            response = (
                "I'm really glad you shared this. You deserve immediate support right now. "
                "If you're in immediate danger or might act on these thoughts, please call your local emergency services now. "
                "You can also contact a trusted person or a crisis hotline in your country right away. "
                "If you want, I can stay with you while you take that first step and help you write a short message to ask for help."
            )
            return {
                "question": question,
                "mode": "crisis",
                "results": [
                    {"strategy": "rag-chain", "response": response, "sources": []},
                    {"strategy": "rag-agent", "response": response, "sources": []},
                ],
            }

        if is_simple_query(question):
            logger.info("Simple query detected during RAG strategy comparison")
            simple = get_simple_response(question)
            return {
                "question": question,
                "mode": "simple",
                "results": [
                    {
                        "strategy": "fast-path",
                        "response": simple["response"],
                        "sources": simple.get("sources", []),
                    }
                ],
            }

        async def _run_chain() -> dict[str, Any]:
            try:
                answer, sources, used = await asyncio.to_thread(get_stress_support_rag_chain_response, question)
                if used:
                    return {
                        "strategy": "rag-chain",
                        "response": answer,
                        "sources": sources,
                        "used_rag": True,
                    }
                fallback = await asyncio.to_thread(get_stress_support_response, question)
                return {
                    "strategy": "rag-chain",
                    "response": fallback,
                    "sources": [],
                    "used_rag": False,
                    "mode": "llm-fallback",
                }
            except Exception as exc:
                logger.exception("RAG chain compare failure")
                return {"strategy": "rag-chain", "error": str(exc)}

        async def _run_agent() -> dict[str, Any]:
            try:
                answer, sources, used = await asyncio.to_thread(get_stress_support_rag_agent_response, question)
                if used:
                    return {
                        "strategy": "rag-agent",
                        "response": answer,
                        "sources": sources,
                        "used_rag": True,
                    }
                fallback = await asyncio.to_thread(get_stress_support_response, question)
                return {
                    "strategy": "rag-agent",
                    "response": fallback,
                    "sources": [],
                    "used_rag": False,
                    "mode": "llm-fallback",
                }
            except Exception as exc:
                logger.exception("RAG agent compare failure")
                return {"strategy": "rag-agent", "error": str(exc)}

        chain_result, agent_result = await asyncio.gather(_run_chain(), _run_agent())
        return {
            "question": question,
            "mode": "rag-strategy-compare",
            "results": [chain_result, agent_result],
        }

    except Exception as e:
        logger.exception("Error during RAG strategy compare processing")
        return JSONResponse(status_code=500, content={"error": str(e)})
