"""Per-tenant FAISS vector store — one embedding model, isolated persist path per tenant."""

from __future__ import annotations

import glob
import json
import logging
import os
import shutil
import threading
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from backend.storage import data_dir
from backend.utils.pdf_parser import extract_text_from_pdf

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PERSIST = data_dir() / "vector_store"
DEFAULT_EMBED_MODEL = os.getenv("LUMINA_EMBED_MODEL", "text-embedding-3-small")

_store_lock = threading.Lock()
_store_instances: dict[str, PersistentEmbedStore] = {}


def get_embed_store(tenant_id: str | None = None) -> PersistentEmbedStore:
    """Per-tenant FAISS store so corpora do not bleed across X-Tenant-Id values."""
    from backend.tenant import get_current_tenant, sanitize_tenant_id

    tid = sanitize_tenant_id(tenant_id or get_current_tenant())
    with _store_lock:
        store = _store_instances.get(tid)
        if store is None:
            path = DEFAULT_PERSIST / "tenants" / tid
            if tid == "default":
                _migrate_legacy_store(path)
            store = PersistentEmbedStore(persist_path=str(path))
            _store_instances[tid] = store
        return store


LEGACY_INDEX_FILES = ("index.faiss", "index.pkl")


def _migrate_legacy_store(target: Path) -> None:
    """Copy a pre-tenant corpus (saved directly under DEFAULT_PERSIST) into the default tenant.

    Runs once: skipped when the default tenant already has an index. The legacy
    files are copied, not moved, so the old layout stays as a fallback.
    """
    if (target / "index.faiss").exists():
        return
    legacy = [DEFAULT_PERSIST / name for name in LEGACY_INDEX_FILES]
    if not all(f.exists() for f in legacy):
        return
    target.mkdir(parents=True, exist_ok=True)
    for f in legacy:
        shutil.copy2(f, target / f.name)
    logger.info("Migrated legacy corpus from %s into %s", DEFAULT_PERSIST, target)


class PersistentEmbedStore:
    def __init__(self, persist_path: str | None = None):
        self.persist_path = Path(persist_path or DEFAULT_PERSIST)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self.embedding_model = OpenAIEmbeddings(model=DEFAULT_EMBED_MODEL)
        self.vectorstore: FAISS | None = None
        self._load()

    def _load(self) -> None:
        index_file = self.persist_path / "index.faiss"
        if not index_file.exists():
            logger.info("No existing FAISS store at %s", self.persist_path)
            return
        try:
            self.vectorstore = FAISS.load_local(
                str(self.persist_path),
                self.embedding_model,
                allow_dangerous_deserialization=True,
            )
            logger.info("Loaded FAISS store (%s chunks)", self.chunk_count())
        except Exception as exc:
            logger.error("Failed to load vector store: %s", exc)
            self.vectorstore = None

    def chunk_count(self) -> int:
        if not self.vectorstore:
            return 0
        try:
            return len(self.vectorstore.index_to_docstore_id)
        except Exception:
            return 0

    def is_ready(self) -> bool:
        return self.vectorstore is not None and self.chunk_count() > 0

    def add_document(self, text: str, source: str) -> int:
        if not text.strip():
            raise ValueError("Empty document text")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
        )
        docs = splitter.create_documents([text], metadatas=[{"source": source}])
        if not docs:
            raise ValueError("No chunks produced from document")

        with _store_lock:
            if self.vectorstore:
                self.vectorstore.add_documents(docs)
            else:
                self.vectorstore = FAISS.from_documents(docs, self.embedding_model)

            self.vectorstore.save_local(str(self.persist_path))
        logger.info(
            "Embedded %s → %s chunks (store total %s)",
            source,
            len(docs),
            self.chunk_count(),
        )
        return len(docs)

    def query(self, question: str, k: int = 6, max_distance: float = 1.2) -> list[dict]:
        """Return chunks under a FAISS L2 distance threshold (lower = closer)."""
        if not self.vectorstore:
            return []

        with _store_lock:
            pairs = self.vectorstore.similarity_search_with_score(question, k=k)

        filtered = []
        for doc, score in pairs:
            if score > max_distance:
                continue
            filtered.append(
                {
                    "text": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "score": float(score),
                }
            )
        return filtered

    def index_pdfs_from_folder(self, folder_path: str | None = None) -> int:
        folder = Path(folder_path or (BACKEND_DIR / "data" / "testing_pdfs"))
        pdf_paths = sorted(glob.glob(str(folder / "*.pdf")))
        indexed = 0
        for path in pdf_paths:
            try:
                text = extract_text_from_pdf(path)
                if text.startswith("Error:") or text.startswith("No extractable"):
                    continue
                self.add_document(text, source=os.path.basename(path))
                indexed += 1
            except Exception as exc:
                logger.error("Failed to index %s: %s", path, exc)
        return indexed

    def list_documents(self) -> list[dict]:
        if not self.vectorstore:
            return []
        counts: dict[str, int] = {}
        with _store_lock:
            for doc_id in self.vectorstore.index_to_docstore_id.values():
                doc = self.vectorstore.docstore.search(doc_id)
                if not hasattr(doc, "metadata"):
                    continue
                src = doc.metadata.get("source", "unknown")
                counts[src] = counts.get(src, 0) + 1
        return [
            {"source": source, "chunks": chunks}
            for source, chunks in sorted(counts.items())
        ]

    def sample_context(self, max_chars: int = 5000) -> str:
        if not self.vectorstore:
            return ""
        parts: list[str] = []
        total = 0
        with _store_lock:
            for doc_id in list(self.vectorstore.index_to_docstore_id.values())[:40]:
                doc = self.vectorstore.docstore.search(doc_id)
                if not hasattr(doc, "page_content"):
                    continue
                text = doc.page_content.strip()
                if not text:
                    continue
                src = getattr(doc, "metadata", {}).get("source", "unknown")
                chunk = f"[{src}]\n{text}"
                if total + len(chunk) > max_chars:
                    break
                parts.append(chunk)
                total += len(chunk)
        return "\n\n".join(parts)

    def clear(self) -> None:
        with _store_lock:
            self.vectorstore = None
            if self.persist_path.exists():
                for path in self.persist_path.glob("*"):
                    if path.is_file():
                        path.unlink()
        logger.info("Vector store cleared")

    def debug_dump(self) -> str:
        return json.dumps(
            {
                "persist_path": str(self.persist_path),
                "ready": self.is_ready(),
                "chunks": self.chunk_count(),
                "embed_model": DEFAULT_EMBED_MODEL,
            }
        )
