"""Uvicorn entry point.

Run from the ``server/`` directory so ``core`` and ``services`` are importable:

    uvicorn main:app --reload

``app`` is defined in ``core.gateway``; importing it here exposes it as
``main:app`` for uvicorn.
"""

from core.gateway import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
