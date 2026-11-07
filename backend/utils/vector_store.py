import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from dotenv import load_dotenv

# Load env vars
load_dotenv()

class LangchainVectorStore:
    def __init__(self, persist_dir="data/vector_store"):
        self.persist_dir = persist_dir
        self.index_file = os.path.join(self.persist_dir, "index.faiss")
        self.store_file = os.path.join(self.persist_dir, "index.pkl")

        os.makedirs(self.persist_dir, exist_ok=True)

        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        if os.path.exists(self.index_file) and os.path.exists(self.store_file):
            self.vectorstore = FAISS.load_local(self.persist_dir, self.embeddings, allow_dangerous_deserialization=True)
            print("✅ Loaded existing FAISS vector store")
        else:
            self.vectorstore = None
            print("🆕 Initialized empty vector store")

    def add_document(self, text: str, source: str):
        if not text.strip():
            raise ValueError("Cannot add empty document to vector store.")
        
        doc = Document(page_content=text, metadata={"source": source})
        if self.vectorstore:
            self.vectorstore.add_documents([doc])
        else:
            self.vectorstore = FAISS.from_documents([doc], self.embeddings)
        
        self.vectorstore.save_local(self.persist_dir)
        print(f"✅ Document from '{source}' embedded and stored.")

    def query(self, query_text: str, top_k: int = 3):
        if not self.vectorstore:
            raise ValueError("Vector store is empty.")

        results = self.vectorstore.similarity_search(query_text, k=top_k)
        return [
            {
                "text": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
            }
            for doc in results
        ]
