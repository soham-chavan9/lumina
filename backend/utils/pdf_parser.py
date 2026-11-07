# backend/utils/pdf_parser.py

import fitz  # PyMuPDF
from io import BytesIO
from typing import List, Dict, Union


def extract_text_from_pdf(file_bytes: Union[bytes, str]) -> str:
    """
    Extract clean, deduplicated text content from PDF.
    Accepts either bytes (from upload) or file path (string).
    Returns concatenated plain text.
    """
    try:
        text_chunks = []

        if isinstance(file_bytes, bytes):
            doc = fitz.open(stream=BytesIO(file_bytes), filetype="pdf")
        elif isinstance(file_bytes, str):
            doc = fitz.open(file_bytes)
        else:
            raise ValueError("Invalid input: expected bytes or file path.")

        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                text_chunks.append(page_text.strip())

        doc.close()
        full_text = "\n".join(text_chunks).strip()

        return full_text if full_text else "No extractable text found in the PDF."

    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
        return "Error: Unable to extract text from PDF."


def extract_text_with_metadata(file_bytes: Union[bytes, str]) -> List[Dict[str, str]]:
    """
    Extracts text with per-page metadata for better RAG traceability.
    Returns: [{ "page": int, "text": str }]
    """
    try:
        results = []

        if isinstance(file_bytes, bytes):
            doc = fitz.open(stream=BytesIO(file_bytes), filetype="pdf")
        elif isinstance(file_bytes, str):
            doc = fitz.open(file_bytes)
        else:
            raise ValueError("Invalid input: expected bytes or file path.")

        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            if page_text:
                results.append({
                    "page": page_num,
                    "text": page_text.strip()
                })

        doc.close()
        return results

    except Exception as e:
        print(f"❌ PDF extraction with metadata failed: {e}")
        return []
