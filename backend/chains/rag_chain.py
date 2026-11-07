"""Deprecated dual prompt path.

The live ask route uses `backend.llm_workflow` exclusively so Answer/Citation/Confidence
stay consistent with promptfoo evals. Kept as a thin wrapper for notebooks only.
"""

from backend.llm_workflow import generate_lumina_answer


def build_qa_chain():
    raise RuntimeError(
        "build_qa_chain() is retired. Use backend.llm_workflow.generate_lumina_answer."
    )


def run_legacy_qa(question: str, context: str) -> str:
    return generate_lumina_answer(question=question, context=context)
