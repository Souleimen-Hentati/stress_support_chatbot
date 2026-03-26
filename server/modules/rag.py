from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Any
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from loggger import logger
from modules.llm import SAFETY_SYSTEM_PROMPT, invoke_with_model_fallback

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
VECTORSTORE_DIR = BASE_DIR / "vectorstore" / "faiss_index"

RAG_PROMPT_TEMPLATE = """
Use the CONTEXT below to provide practical, supportive stress-management guidance.
If context is weak or missing specific facts, say so briefly and continue with safe, general support.
Do not invent document facts.
Keep the answer concise and actionable.

CONTEXT:
{context}
""".strip()

RAG_AGENT_DECIDER_PROMPT = """
You are a retrieval planning assistant.
Given the user question and retrieved context, decide whether a second retrieval pass is needed.

Return ONLY valid JSON with this schema:
{"need_more_context": true|false, "followup_query": "optional short query"}

Rules:
- Set need_more_context=true only when context is clearly insufficient.
- If true, provide a concise followup_query focused on missing details.
- Do not add any extra text outside JSON.
""".strip()

RAG_AGENT_PROMPT_TEMPLATE = """
Use the CONTEXT below to provide practical, supportive stress-management guidance.
If context is weak or missing specific facts, say so briefly and continue with safe, general support.
Do not invent document facts.
Keep the answer concise and actionable.

CONTEXT:
{context}
""".strip()

def _safe_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning(f"Invalid integer env value for {name}: {raw}. Using {default}.")
        return default

def _safe_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning(f"Invalid float env value for {name}: {raw}. Using {default}.")
        return default

def _get_doc_dirs() -> list[Path]:
    configured = os.getenv("RAG_DOC_DIRS", "uploaded_docs,server/uploaded_docs")
    dirs: list[Path] = []
    for raw_path in configured.split(","):
        candidate = raw_path.strip()
        if not candidate:
            continue
        path = Path(candidate)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        dirs.append(path)
    return dirs

def _collect_source_files() -> list[Path]:
    files: list[Path] = []
    for doc_dir in _get_doc_dirs():
        if not doc_dir.exists() or not doc_dir.is_dir():
            continue
        for ext in ("*.pdf", "*.txt", "*.md"):
            files.extend(sorted(doc_dir.glob(ext)))
    return files

def _load_documents() -> list[Any]:
    """Load documents from supported source files."""
    documents: list[Any] = []
    for file_path in _collect_source_files():
        suffix = file_path.suffix.lower()
        try:
            if suffix == ".pdf":
                loader = PyPDFLoader(str(file_path))
                documents.extend(loader.load())
            elif suffix in {".txt", ".md"}:
                loader = TextLoader(str(file_path), encoding="utf-8")
                documents.extend(loader.load())
        except Exception as exc:
            logger.warning(f"Skipping file for RAG indexing: {file_path} ({exc})")
    return documents


def _get_embeddings_client() -> OpenAIEmbeddings:
    api_key = os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("EMBEDDING_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    if not api_key:
        raise RuntimeError(
            "Embeddings API key missing. Set EMBEDDING_API_KEY (or OPENAI_API_KEY for backward compatibility)."
        )

    return OpenAIEmbeddings(
        api_key=api_key,
        base_url=base_url,
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
    )

def build_rag_index() -> bool:
    documents = _load_documents()
    if not documents:
        logger.warning("RAG index build skipped: no documents found")
        return False

    chunk_size = _safe_int_env("RAG_CHUNK_SIZE", 900)
    chunk_overlap = _safe_int_env("RAG_CHUNK_OVERLAP", 150)
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(documents)

    if not chunks:
        logger.warning("RAG index build skipped: no chunks produced")
        return False

    VECTORSTORE_DIR.parent.mkdir(parents=True, exist_ok=True)
    db = FAISS.from_documents(chunks, _get_embeddings_client())
    db.save_local(str(VECTORSTORE_DIR))
    logger.info(f"RAG index built with {len(chunks)} chunks at: {VECTORSTORE_DIR}")
    return True

def _load_vectorstore() -> FAISS | None:
    if not VECTORSTORE_DIR.exists():
        return None
    try:
        return FAISS.load_local(
            str(VECTORSTORE_DIR),
            _get_embeddings_client(),
            allow_dangerous_deserialization=True,
        )
    except Exception as exc:
        logger.warning(f"Failed to load FAISS index: {exc}")
        return None


def _sanitize_source(source: str) -> str:
    if not source:
        return "unknown"
    normalized = source.replace("\\", "/").strip()
    if "/" in normalized:
        return normalized.split("/")[-1]
    return normalized

def _format_sources(docs: list[Any]) -> list[dict[str, Any]]:
    formatted: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None]] = set()

    for doc in docs:
        meta = getattr(doc, "metadata", {}) or {}
        source = _sanitize_source(str(meta.get("source", "unknown")))
        page = meta.get("page")
        key = (source, page)
        if key in seen:
            continue
        seen.add(key)
        formatted.append({"source": source, "page": page})

    return formatted

def _retrieve_docs(db: FAISS, query: str, k: int) -> list[Any]:
    search_type = os.getenv("RAG_SEARCH_TYPE", "mmr").strip().lower()

    if search_type == "similarity":
        return db.similarity_search(query, k=k)

    if search_type == "threshold":
        min_score = _safe_float_env("RAG_MIN_SCORE", 0.25)
        try:
            scored = db.similarity_search_with_relevance_scores(query, k=k)
            return [doc for doc, score in scored if score >= min_score]
        except Exception as exc:
            logger.warning(f"Threshold retrieval failed, falling back to similarity search: {exc}")
            return db.similarity_search(query, k=k)

    fetch_k = max(k * 3, k)
    try:
        return db.max_marginal_relevance_search(query, k=k, fetch_k=fetch_k)
    except Exception as exc:
        logger.warning(f"MMR retrieval failed, falling back to similarity search: {exc}")
        return db.similarity_search(query, k=k)

def _build_context(docs: list[Any]) -> str:
    max_snippet_chars = _safe_int_env("RAG_MAX_SNIPPET_CHARS", 1200)
    max_context_chars = _safe_int_env("RAG_MAX_CONTEXT_CHARS", 6000)

    blocks: list[str] = []
    used_chars = 0
    for idx, doc in enumerate(docs, start=1):
        snippet = getattr(doc, "page_content", "").strip()
        if len(snippet) > max_snippet_chars:
            snippet = snippet[: max_snippet_chars - 3].rstrip() + "..."

        meta = getattr(doc, "metadata", {}) or {}
        source = _sanitize_source(str(meta.get("source", "unknown")))
        page = meta.get("page")
        source_tag = f"{source} (page {page})" if page is not None else source
        block = f"[{idx}] {source_tag}\n{snippet}"

        if used_chars + len(block) > max_context_chars:
            break
        blocks.append(block)
        used_chars += len(block)

    return "\n\n".join(blocks)

def _extract_agent_decision(decision_text: str) -> tuple[bool, str]:
    default = (False, "")
    text = (decision_text or "").strip()
    if not text:
        return default

    payload: dict[str, Any] | None = None
    try:
        payload = json.loads(text)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                payload = json.loads(match.group(0))
            except Exception:
                payload = None

    if not isinstance(payload, dict):
        return default

    need_more = bool(payload.get("need_more_context", False))
    followup_query = str(payload.get("followup_query", "") or "").strip()
    return need_more, followup_query

def _merge_docs(first: list[Any], second: list[Any], max_docs: int) -> list[Any]:
    seen: set[tuple[str, str]] = set()
    merged: list[Any] = []

    for doc in [*first, *second]:
        meta = getattr(doc, "metadata", {}) or {}
        source = str(meta.get("source", "unknown"))
        page = str(meta.get("page", ""))
        key = (source, page)
        if key in seen:
            continue
        seen.add(key)
        merged.append(doc)
        if len(merged) >= max_docs:
            break

    return merged

def get_stress_support_rag_messages(
    question: str,
) -> tuple[list[dict[str, str]], list[dict[str, Any]], bool]:
    db = _load_vectorstore()
    if db is None:
        if build_rag_index():
            db = _load_vectorstore()

    if db is None:
        return [], [], False

    k = _safe_int_env("RAG_TOP_K", 4)
    docs = _retrieve_docs(db, question, k=k)
    if not docs:
        return [], [], False

    context = _build_context(docs)
    if not context.strip():
        return [], [], False

    rag_prompt = RAG_PROMPT_TEMPLATE.format(context=context)
    messages = [
        {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
        {"role": "system", "content": rag_prompt},
        {"role": "user", "content": question},
    ]
    return messages, _format_sources(docs), True

def get_stress_support_rag_response(question: str) -> tuple[str, list[dict[str, Any]], bool]:
    messages, sources, used_rag = get_stress_support_rag_messages(question)
    if not used_rag:
        return "", [], False
    answer = invoke_with_model_fallback(messages)
    return answer, sources, True

def get_stress_support_rag_chain_response(question: str) -> tuple[str, list[dict[str, Any]], bool]:
    return get_stress_support_rag_response(question)

def get_stress_support_rag_agent_response(question: str) -> tuple[str, list[dict[str, Any]], bool]:
    db = _load_vectorstore()
    if db is None:
        if build_rag_index():
            db = _load_vectorstore()

    if db is None:
        return "", [], False

    k = _safe_int_env("RAG_TOP_K", 4)
    first_docs = _retrieve_docs(db, question, k=k)
    if not first_docs:
        return "", [], False

    first_context = _build_context(first_docs)
    planner_messages = [
        {"role": "system", "content": RAG_AGENT_DECIDER_PROMPT},
        {
            "role": "user",
            "content": f"Question:\n{question}\n\nCurrent Context:\n{first_context}",
        },
    ]
    planner_output = invoke_with_model_fallback(planner_messages)
    need_more, followup_query = _extract_agent_decision(planner_output)

    final_docs = first_docs
    if need_more:
        query = followup_query or question
        second_docs = _retrieve_docs(db, query, k=k)
        final_docs = _merge_docs(first_docs, second_docs, max_docs=max(k * 2, k))

    final_context = _build_context(final_docs)
    if not final_context.strip():
        return "", [], False

    agent_prompt = RAG_AGENT_PROMPT_TEMPLATE.format(context=final_context)
    messages = [
        {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
        {"role": "system", "content": agent_prompt},
        {"role": "user", "content": question},
    ]
    answer = invoke_with_model_fallback(messages)
    return answer, _format_sources(final_docs), True
