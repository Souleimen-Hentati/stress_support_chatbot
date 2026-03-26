import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from loggger import logger

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

def _get_provider() -> str:
    provider_raw = os.getenv("LLM_PROVIDER", "openai_compatible").strip().lower()
    aliases = {
        "openai": "openai_compatible",
        "openrouter": "openai_compatible",
        "anthropic": "anthropic",
        "claude": "anthropic",
    }
    return aliases.get(provider_raw, provider_raw)

def _default_model_for_provider(provider: str) -> str:
    if provider == "anthropic":
        return "claude-3-5-sonnet-latest"
    return "openai/gpt-4o-mini"

def _get_primary_model(provider: str) -> str:
    return (
        os.getenv("PRIMARY_MODEL")
        or os.getenv("MISTRAL_MODEL")
        or _default_model_for_provider(provider)
    )

def _is_model_unavailable_error(err_text: str) -> bool:
    lowered = err_text.lower()
    markers = [
        "no endpoints found",
        "404",
        "model_not_found",
        "model not found",
        "does not exist",
        "invalid model",
        "unavailable model",
    ]
    return any(marker in lowered for marker in markers)

def _get_model_candidates() -> list[str]:
    provider = _get_provider()
    primary_model = _get_primary_model(provider)
    fallbacks_raw = os.getenv("FALLBACK_MODELS", primary_model)
    fallback_models = [model.strip() for model in fallbacks_raw.split(",") if model.strip()]
    candidates: list[str] = []
    for model in [primary_model, *fallback_models]:
        if model not in candidates:
            candidates.append(model)
    return candidates

def get_compare_models() -> list[str]:
    configured = os.getenv(
        "COMPARE_MODELS",
        "openai/gpt-4o-mini,openai/gpt-4.1-mini,google/gemini-1.5-pro",
    )
    models = [m.strip() for m in configured.split(",") if m.strip()]
    unique: list[str] = []
    for model in models:
        if model not in unique:
            unique.append(model)
    return unique

SAFETY_SYSTEM_PROMPT = """
You are MediBot, a supportive mental wellbeing chatbot focused on stress management.

Your role:
- Offer empathetic, non-judgmental support.
- Help users with stress coping techniques (breathing, grounding, routines, reframing, sleep hygiene, gentle planning).
- Ask brief clarifying questions when useful.

Safety rules:
- Do NOT diagnose medical or psychiatric conditions.
- Do NOT provide medication instructions.
- If the user expresses possible self-harm, suicide intent, or immediate danger, respond with care and strongly encourage contacting local emergency services or a trusted crisis hotline now.
- Keep responses concise and practical.
""".strip()


def get_chat_llm(model_name: str) -> Any:
    provider = _get_provider()

    if provider == "anthropic":
        anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_API_KEY")
        if not anthropic_key:
            raise RuntimeError(
                "Anthropic provider selected, but no key found. Set ANTHROPIC_API_KEY or LLM_API_KEY."
            )
        return ChatAnthropic(
            api_key=anthropic_key,
            model=model_name,
            temperature=0.4,
        )

    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    openai_base = os.getenv("OPENAI_BASE_URL") or os.getenv("LLM_BASE_URL")
    if not openai_key:
        raise RuntimeError(
            "OpenAI-compatible provider selected, but no key found. Set OPENAI_API_KEY or LLM_API_KEY."
        )

    return ChatOpenAI(
        api_key=openai_key,
        base_url=openai_base,
        model=model_name,
        temperature=0.4,
    )

def invoke_specific_model(messages: list[dict[str, str]], model_name: str) -> str:
    llm = get_chat_llm(model_name)
    completion = llm.invoke(messages)
    return getattr(completion, "content", str(completion))

def invoke_with_model_fallback(messages: list[dict[str, str]]) -> str:
    provider = _get_provider()
    last_error: Exception | None = None
    for model_name in _get_model_candidates():
        try:
            llm = get_chat_llm(model_name)
            completion = llm.invoke(messages)
            return getattr(completion, "content", str(completion))
        except Exception as exc:
            last_error = exc
            err_text = str(exc)
            if _is_model_unavailable_error(err_text):
                logger.warning(f"Model unavailable on {provider}: {model_name}. Trying fallback...")
                continue
            raise

    raise RuntimeError(
        f"No available model endpoints for provider '{provider}'. "
        "Update PRIMARY_MODEL/FALLBACK_MODELS in server/.env to active model IDs."
    ) from last_error


def get_stress_support_response(question: str) -> str:
    messages = [
        {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    return invoke_with_model_fallback(messages)


