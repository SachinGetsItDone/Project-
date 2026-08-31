"""Seed the pgvector domain_knowledge table with starter interview facts.

Run from the ``server/`` directory (after Postgres is up):

    python -m db.seed_domain_knowledge

Idempotent: if the table already has rows, it does nothing.
"""

from db.pg import get_pool, init_schema
from services.rag_service import RAGService

# (role_category, topic, content)
SEED_FACTS = [
    ("backend", "database-indexing",
     "A database index speeds up reads by maintaining a sorted structure (usually a B-tree) over one or more columns, at the cost of slower writes and extra storage."),
    ("backend", "acid",
     "ACID transactions guarantee Atomicity, Consistency, Isolation, and Durability; they are the basis for correctness in relational databases under concurrency and failure."),
    ("backend", "sql-vs-nosql",
     "SQL databases enforce a fixed schema and strong relational integrity; NoSQL stores trade that for flexible documents and horizontal scale. Choose based on access patterns and consistency needs."),
    ("backend", "caching",
     "Caching stores hot data closer to the reader to cut latency and load. Key decisions are what to cache, the eviction policy (LRU/LFU), and how to invalidate stale entries."),
    ("backend", "message-queue",
     "A message queue decouples producers from consumers and smooths spiky load. At-least-once delivery is the practical default, which requires idempotent consumers to avoid double-processing."),
    ("backend", "load-balancing",
     "A load balancer spreads traffic across servers using strategies like round-robin or least-connections, and uses health checks to route away from unhealthy instances."),
    ("distributed-systems", "cap-theorem",
     "The CAP theorem says a distributed system facing a network partition must choose between consistency and availability; you cannot have both during a partition."),
    ("distributed-systems", "consistent-hashing",
     "Consistent hashing maps keys and nodes onto a ring so that adding or removing a node only remaps a small fraction of keys, which is essential for scalable sharding and caching."),
    ("distributed-systems", "race-conditions",
     "A race condition occurs when the result depends on unsynchronized concurrent access to shared state. Fixes include locks, atomic operations, and single-writer designs."),
    ("distributed-systems", "idempotency",
     "An idempotent operation produces the same result whether applied once or many times; idempotency keys let clients safely retry requests without duplicating side effects."),
    ("system-design", "horizontal-vs-vertical-scaling",
     "Vertical scaling adds power to one machine and hits a ceiling; horizontal scaling adds more machines and needs statelessness or partitioning but scales much further."),
    ("system-design", "rate-limiting",
     "Rate limiting protects a service from overload and abuse. Token bucket allows bursts up to a cap; leaky bucket enforces a steady rate."),
    ("system-design", "cdn",
     "A CDN caches static assets at edge locations near users to reduce latency and origin load, and is the first lever for global content delivery."),
    ("system-design", "websockets",
     "WebSockets provide a persistent, bidirectional connection ideal for real-time features like live audio or chat, unlike request/response HTTP polling."),
    ("behavioral", "star-method",
     "The STAR method structures behavioral answers as Situation, Task, Action, Result, keeping stories concrete and outcome-focused."),
    ("behavioral", "system-design-approach",
     "A strong system-design answer clarifies requirements, estimates scale with numbers, sketches components, then justifies each trade-off as what it solves, worsens, and when to change it."),
]


def main():
    init_schema()
    with get_pool().connection() as conn:
        count = conn.execute("SELECT count(*) FROM domain_knowledge").fetchone()[0]
    if count > 0:
        print(f"domain_knowledge already has {count} rows; skipping seed.")
        return

    rag = RAGService()
    texts = [content for _, _, content in SEED_FACTS]
    metas = [{"role_category": rc, "topic": tp} for rc, tp, _ in SEED_FACTS]
    rag.add_documents(texts, metas)
    print(f"Seeded {len(texts)} domain facts into pgvector.")


if __name__ == "__main__":
    main()
