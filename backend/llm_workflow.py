import os
import re
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# Single canonical prompt — no competing chain templates on the hot path
prompt_with_context = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are Lumina, an AI compliance assistant.\n\n"
        "Rules:\n"
        "- Use ONLY the document context provided below.\n"
        "- If the answer is not in the context, reply exactly with: 'Not found in document.'\n"
        "- Do NOT hallucinate regulations, article numbers, or sections that are not visible in the context.\n"
        "- Your response MUST follow this exact format:\n"
        "  Answer: <clear, concise answer in plain English>\n"
        "  Citation: <policy/regulation name and section or a short quoted snippet from the context>\n"
        "  Confidence: <High | Medium | Low>\n"
        "- If you cannot see any explicit section/article names in the context, still answer but set\n"
        "  Citation: 'Based on provided context (no explicit section visible).'\n"
        "- Keep the answer short (3–6 sentences max) and focused on compliance, privacy, security, risk, or policy.\n"
    ),
    (
        "human",
        "Context:\n{context}\n\nQuestion:\n{question}"
    ),
])


# === Initialize reusable LLM ===
def get_lumina_model(model_name: Optional[str] = None):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing for LangChain backend.")
    
    model_name = model_name or os.getenv("LUMINA_MODEL", "gpt-4o-mini")

    return ChatOpenAI(
        api_key=api_key,
        model=model_name,
        temperature=0.3,
    )


# === Core Generation Function ===
def generate_lumina_answer(
    question: str,
    context: Optional[str] = "",
    model_name: Optional[str] = None,
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
        raise RuntimeError(f"Lumina LLM error: {str(e)}") from e


# === Output Parsing ===
def parse_lumina_output(text: str) -> Dict[str, Any]:
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