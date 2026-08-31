"""RAG service backed by Postgres + pgvector.

Public method signatures (``retrieve_facts`` / ``add_documents``) are unchanged
from the previous ChromaDB implementation so call sites in the gateway need no
edits. Embeddings use the local ``all-MiniLM-L6-v2`` model (384-dim), which
needs no API key.

The embedding model and its heavy import are loaded lazily on first use, so the
API process can start (and the DB-less tests can run) even when the model files
or Postgres are not available.
"""

from typing import List, Optional

from core.config import settings
from db.pg import get_pool, to_pgvector


class RAGService:
    def __init__(self):
        self._model = None

    def _get_model(self):
        if self._model is None:
            # Imported here (not at module load) so a missing/oversized dependency
            # can't break importing the gateway.
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._model

    def _embed(self, text: str) -> List[float]:
        # Normalized embeddings so cosine distance (<=>) behaves as expected.
        vec = self._get_model().encode(text, normalize_embeddings=True)
        return vec.tolist()

    def retrieve_facts(self, query: str, top_k: int = 3) -> str:
        """Retrieve the most relevant domain facts for a query, as a bullet list.

        Returns an empty string on any failure (model or DB unavailable) so the
        caller degrades gracefully.
        """
        if not query or not query.strip():
            return ""
        try:
            emb = to_pgvector(self._embed(query))
            with get_pool().connection() as conn:
                rows = conn.execute(
                    """
                    SELECT content
                    FROM domain_knowledge
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (emb, top_k),
                ).fetchall()
            if not rows:
                return "No specific domain facts found."
            return "\n".join(f"- {row[0]}" for row in rows)
        except Exception as e:
            print(f"Error retrieving facts from RAG: {e}")
            return ""

    def add_documents(self, texts: List[str], metadatas: Optional[List[dict]] = None):
        """Embed and insert documents into the vector store."""
        if not texts:
            return
        metadatas = metadatas or [{} for _ in texts]
        with get_pool().connection() as conn:
            for text, meta in zip(texts, metadatas):
                emb = to_pgvector(self._embed(text))
                conn.execute(
                    """
                    INSERT INTO domain_knowledge (role_category, topic, content, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                    """,
                    (meta.get("role_category"), meta.get("topic"), text, emb),
                )
            conn.commit()
