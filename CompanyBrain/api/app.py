from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path
from .embeddings_adapter import EmbeddingsAdapter

app = FastAPI(title="CompanyBrain Search API")


class SearchResponseItem(BaseModel):
    id: str
    score: float
    text: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResponseItem]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/search", response_model=SearchResponse)
def search(
    query: str = Query(..., min_length=1), index: Optional[str] = None, top_k: int = 5
):
    idx_path = Path(index) if index else Path("index.json")
    if not idx_path.exists():
        raise HTTPException(status_code=404, detail=f"Index file not found: {idx_path}")

    try:
        with idx_path.open("r", encoding="utf-8") as f:
            index_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load index: {e}")

    adapter = EmbeddingsAdapter()
    q_vec = adapter.embed_text(query)

    results = []
    for doc in index_data.get("documents", []):
        doc_vec = doc.get("embedding")
        if not doc_vec:
            continue
        score = adapter.cosine_similarity(q_vec, doc_vec)
        results.append({"id": doc.get("id"), "score": score, "text": doc.get("text")})

    results.sort(key=lambda r: r["score"], reverse=True)
    top = results[:top_k]

    return SearchResponse(query=query, results=[SearchResponseItem(**r) for r in top])
