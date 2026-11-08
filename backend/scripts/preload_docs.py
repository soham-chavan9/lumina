"""
Preload and embed all test PDFs into the persistent vector store.
Run this once before using the app to 'train' Lumina on compliance documents.
"""

import os
import sys

from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Ensure correct import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.embed_store import PersistentEmbedStore
from utils.pdf_parser import extract_text_from_pdf

UPLOAD_DIR = "data/testing_pdfs"


def preload_docs():
    """Loads PDFs from UPLOAD_DIR and adds their content to the vector store."""
    print("📘 Starting document preload...\n")

    store = PersistentEmbedStore()

    if not os.path.exists(UPLOAD_DIR):
        print(f"⚠️ Directory not found: {UPLOAD_DIR}")
        return

    pdf_files: list[str] = [
        f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(".pdf")
    ]
    if not pdf_files:
        print("⚠️ No PDF files found in testing_pdfs.")
        return

    print(f"📂 Found {len(pdf_files)} document(s) to process.\n")

    for file_name in pdf_files:
        path = os.path.join(UPLOAD_DIR, file_name)
        try:
            with open(path, "rb") as f:
                content = f.read()

            text = extract_text_from_pdf(content)
            if not text.strip():
                print(f"⚠️ Skipped {file_name} — no readable text.")
                continue

            print(f"🔹 Ingesting {file_name} ({len(text)} chars)...")
            store.add_text(text)
            print(f"✅ Embedded: {file_name}\n")

        except Exception as e:
            print(f"❌ Error processing {file_name}: {e}")

    store.save()
    print("\n✅ All PDFs embedded and saved successfully!\n")


if __name__ == "__main__":
    preload_docs()
