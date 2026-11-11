import hashlib
import json
import logging
import os
import re
import threading
from typing import Any

from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

logger = logging.getLogger(__name__)

DEFAULT_LOCAL_MODEL = "llama3.1:8b"
_probe_lock = threading.Lock()
_probe_cache: tuple[str, bool] | None = None  # (key fingerprint, usable)

# Single canonical prompt — no competing chain templates on the hot path
prompt_with_context = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are Lumina, the HIPAA privacy desk for health systems and digital health.\n\n"
        "Rules:\n"
        "- Use ONLY the document context provided below.\n"
        "- If the answer is not in the context, reply exactly with: 'Not found in document.'\n"
        "- Do NOT invent HIPAA citations, section numbers, or policy clauses absent from the context.\n"
        "- Prefer language useful to Privacy Officers: breach clocks, access rights, BAAs, "
        "minimum necessary, sanctions, and workforce duties.\n"
        "- Your response MUST follow this exact format:\n"
        "  Answer: <clear, concise answer in plain English>\n"
        "  Citation: <policy/regulation name and section or a short quoted snippet from the context>\n"
        "  Confidence: <High | Medium | Low>\n"
        "- If you cannot see any explicit section/article names in the context, still answer but set\n"
        "  Citation: 'Based on provided context (no explicit section visible).'\n"
        "- Keep the answer short (3–6 sentences max).\n"
    ),
    (
        "human",
        "Context:\n{context}\n\nQuestion:\n{question}"
    ),
])


# === Model selection: OpenAI first, local Ollama model as the fallback ===
def local_fallback_enabled() -> bool:
    return os.getenv("LUMINA_LOCAL_FALLBACK", "true").strip().lower() not in {"0", "false", "no", "off"}


def local_model_name() -> str:
    return os.getenv("LUMINA_LOCAL_MODEL", DEFAULT_LOCAL_MODEL).strip() or DEFAULT_LOCAL_MODEL


def get_local_model(json_mode: bool = False):
    # JSON mode makes Ollama return a valid JSON object; local models otherwise
    # tend to answer "JSON only" prompts with Markdown.
    return ChatOllama(
        model=local_model_name(),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        temperature=0.3,
        format="json" if json_mode else None,
    )


def openai_usable() -> bool:
    """True when OPENAI_API_KEY is set and accepted by OpenAI.

    Checked once per process (per key) with a tiny embeddings call, so a missing,
    invalid or out-of-credit key switches Lumina to local fallbacks.
    """
    global _probe_cache
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return False
    fingerprint = hashlib.sha256(api_key.encode()).hexdigest()
    with _probe_lock:
        if _probe_cache is None or _probe_cache[0] != fingerprint:
            try:
                OpenAIEmbeddings(
                    model=os.getenv("LUMINA_EMBED_MODEL", "text-embedding-3-small"),
                    api_key=api_key,
                    max_retries=0,
                    request_timeout=10,
                ).embed_query("ping")
                usable = True
            except Exception as exc:
                logger.warning("OpenAI unavailable (%s); using local fallbacks", type(exc).__name__)
                usable = False
            _probe_cache = (fingerprint, usable)
        return _probe_cache[1]


def llm_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip()) or local_fallback_enabled()


def active_model_label() -> str:
    if local_fallback_enabled() and not openai_usable():
        return f"{local_model_name()} (local)"
    return os.getenv("LUMINA_MODEL", "gpt-4o-mini")


def _openai_chat(api_key: str, model_name: str | None):
    return ChatOpenAI(
        api_key=api_key,
        model=model_name or os.getenv("LUMINA_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )


def get_lumina_model(model_name: str | None = None, json_mode: bool = False):
    """Chat model for prompts. json_mode=True for prompts that expect one JSON object."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not local_fallback_enabled():
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing for LangChain backend.")
        return _openai_chat(api_key, model_name)
    if openai_usable():
        # A failing OpenAI call (quota, outage) still falls through to the local model.
        return _openai_chat(api_key, model_name).with_fallbacks([get_local_model(json_mode)])
    return get_local_model(json_mode)


# === Core Generation Function ===
def generate_lumina_answer(
    question: str,
    context: str | None = "",
    model_name: str | None = None,
) -> str:
    """
    Generate a structured compliance answer using LangChain.
    If no context is provided, model still responds safely.
    """
    try:
        llm = get_lumina_model(model_name)
        chain = prompt_with_context | llm | StrOutputParser()

        if not context or not str(context).strip():
            raise ValueError("Refusing LLM call without retrieved document context.")

        return chain.invoke({
            "question": question,
            "context": context,
        })
    except Exception as e:
        raise RuntimeError(f"Lumina LLM error: {e!s}") from e


# === Output Parsing ===
_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json(text: str):
    """Parse the first JSON object or array in a model reply.

    Handles bare JSON, a ```json fence, and JSON preceded or followed by prose,
    which local models such as llama3.1 often add.
    """
    text = (text or "").strip()
    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "[{":
            try:
                return decoder.raw_decode(text, i)[0]
            except json.JSONDecodeError:
                continue
    raise ValueError("No JSON found in model output")


def parse_lumina_output(text: str) -> dict[str, Any]:
    """
    Parse structured LLM output into JSON format.
    Input example:
        Answer: ...
        Citation: ...
        Confidence: High
    """
    try:
        answer_match = re.search(
            r"Answer:\s*(.*?)(?:\nCitation:|\Z)",
            text, re.DOTALL | re.IGNORECASE,
        )
        citation_match = re.search(
            r"Citation:\s*(.*?)(?:\nConfidence:|\Z)",
            text, re.DOTALL | re.IGNORECASE,
        )
        confidence_match = re.search(
            r"Confidence:\s*([A-Za-z]+)",
            text, re.IGNORECASE,
        )

        answer = answer_match.group(1).strip() if answer_match else text.strip()
        citation = citation_match.group(1).strip() if citation_match else ""
        confidence = (
            confidence_match.group(1).strip().capitalize()
            if confidence_match else "Unknown"
        )

        return {
            "answer": answer,
            "citation": citation,
            "confidence": confidence,
            "raw": text.strip(),
        }
    except Exception:
        return {
            "answer": text.strip(),
            "citation": "",
            "confidence": "Unknown",
            "raw": text.strip(),
        }