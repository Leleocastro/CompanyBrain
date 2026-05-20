from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
import os
from indexer.embeddings import EmbeddingProvider, cosine

app = FastAPI(title="CompanyBrain Search (MVP)")

INDEX_PATH = os.getenv('INDEX_PATH', 'CompanyBrain/sample_docs/index.json')
EMB_PROVIDER = os.getenv('EMBEDDING_PROVIDER', 'mock')

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

class Doc(BaseModel):
    id: str
    title: str
    text: str

# lazy load index
_index_cache = None

def load_index():
    global _index_cache
    if _index_cache is not None:
        return _index_cache
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError(f"Index not found: {INDEX_PATH}")
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        _index_cache = json.load(f)
    return _index_cache

@app.on_event("startup")
def startup_event():
    # initialize provider
    app.state.emb = EmbeddingProvider(provider=EMB_PROVIDER)

@app.post('/search')
def search(req: SearchRequest):
    try:
        idx = load_index()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    texts = [d['text'] for d in idx]
    emb_query = app.state.emb.embed_texts([req.query])[0]
    doc_embs = app.state.emb.embed_texts(texts)
    scores = [(d['id'], d['title'], cosine(emb_query, de)) for d,de in zip(idx, doc_embs)]
    scores.sort(key=lambda x: x[2], reverse=True)
    top = []
    for _id, title, score in scores[:req.top_k]:
        top.append({'id': _id, 'title': title, 'score': score})
    return {'query': req.query, 'top_k': req.top_k, 'results': top}
