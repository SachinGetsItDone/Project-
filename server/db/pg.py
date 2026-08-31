"""Postgres + pgvector access for the RAG store.

A single synchronous connection pool is shared across the app. Embeddings are
passed as pgvector text literals (``'[0.1,0.2,...]'``) cast to ``vector`` in
SQL, so we don't depend on a client-side vector adapter or on the ``vector``
type being registered before the extension exists.
"""

from typing import Optional

from psycopg_pool import ConnectionPool

from core.config import settings

_pool: Optional[ConnectionPool] = None


def get_pool() -> ConnectionPool:
    """Return the shared connection pool, opening it on first use."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(conninfo=settings.DATABASE_URL, min_size=1, max_size=10, open=True)
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def init_schema() -> None:
    """Create the pgvector extension, the domain_knowledge table, and its index."""
    dim = settings.EMBEDDING_DIM
    with get_pool().connection() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS domain_knowledge (
                id          serial PRIMARY KEY,
                role_category text,
                topic       text,
                content     text NOT NULL,
                embedding   vector({dim}),
                created_at  timestamptz DEFAULT now()
            )
            """
        )
        # HNSW over ivfflat: correct results regardless of table size (ivfflat
        # needs lists <= row count and errors on near-empty tables).
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS domain_knowledge_embedding_idx
            ON domain_knowledge USING hnsw (embedding vector_cosine_ops)
            """
        )
        conn.commit()


def to_pgvector(vec) -> str:
    """Format an embedding as a pgvector text literal."""
    return "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"
