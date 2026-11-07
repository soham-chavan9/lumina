# test_backend_setup.py

import pytest

def test_imports():
    """✅ Ensure all core dependencies are installed and importable"""
    import fastapi
    import uvicorn
    import openai
    import langchain
    import faiss
    import fitz  # PyMuPDF
    import pdfplumber
    import pydantic
    import numpy
    import requests
    import yaml
    import dotenv
    import langgraph
    import langsmith
    print("✅ All imports successful!")

def test_fastapi_client():
    """✅ Spin up a FastAPI app and test a simple route"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("✅ FastAPI health check passed!")

def test_openai_connection(monkeypatch):
    """✅ Validate OpenAI client instantiation"""
    import openai
    from openai import OpenAI

    # Dummy key to check initialization only (no API call)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-1234567890")
    client = OpenAI()
    assert client is not None
    print("✅ OpenAI client initialized successfully!")

