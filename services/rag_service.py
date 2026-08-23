import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from core.config import settings

class RAGService:
    def __init__(self):
        # Using a lightweight local embedding model for the domain KB
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Initialize chroma db (creates it if it doesn't exist)
        self.vectorstore = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            embedding_function=self.embeddings
        )

    def retrieve_facts(self, query: str, top_k: int = 3) -> str:
        """
        Retrieves relevant domain knowledge based on the user's transcript or current topic.
        """
        try:
            results = self.vectorstore.similarity_search(query, k=top_k)
            if not results:
                return "No specific domain facts found."
            
            facts = "\n".join([f"- {doc.page_content}" for doc in results])
            return facts
        except Exception as e:
            print(f"Error retrieving facts from RAG: {e}")
            return ""

    def add_documents(self, texts: list[str], metadatas: list[dict] = None):
        """
        Adds knowledge to the vector store.
        """
        self.vectorstore.add_texts(texts, metadatas=metadatas)
