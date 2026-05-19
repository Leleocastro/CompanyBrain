from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import random

app = FastAPI(title="Mock Graph API")

# Restrict CORS to the frontend (do NOT use '*' with allow_credentials=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---
class Node(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, str]
    embedding: Optional[List[float]] = None

class Edge(BaseModel):
    source: str
    target: str
    type: str
    weight: float

class PaginatedNodes(BaseModel):
    items: List[Node]
    total: int
    page: int
    size: int

class PaginatedEdges(BaseModel):
    items: List[Edge]
    total: int
    page: int
    size: int

class NodeDetail(BaseModel):
    node: Node
    neighbors: List[Node]

# --- In-memory seed data ---
NODES: List[Node] = []
EDGES: List[Edge] = []


def _rand_vec(d=128):
    return [random.random() for _ in range(d)]

# Create ~20 nodes
types = ["Person", "Document", "Repository", "Conversation", "Entity", "CodeFile"]
for i in range(1, 21):
    t = types[i % len(types)]
    node = Node(
        id=f"n{i}",
        label=f"{t} {i}",
        type=t,
        properties={"title": f"{t} example {i}", "summary": f"This is an example {t} with id n{i}"},
        embedding=_rand_vec(128),
    )
    NODES.append(node)

# Create ~30 edges
for i in range(1, 31):
    s = f"n{(i % 20) + 1}"
    t = f"n{((i * 3) % 20) + 1}"
    e = Edge(source=s, target=t, type="references" if i % 3 else "mentions", weight=round(random.random(), 3))
    EDGES.append(e)

# Helper maps
NODE_MAP = {n.id: n for n in NODES}

# --- Utilities ---
def paginate_items(items: List, page: int = 1, size: int = 20):
    if page < 1:
        page = 1
    start = (page - 1) * size
    end = start + size
    return items[start:end]

# --- Endpoints ---
@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.get("/api/graph/nodes", response_model=PaginatedNodes)
async def list_nodes(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    total = len(NODES)
    items = paginate_items(NODES, page, size)
    return {"items": items, "total": total, "page": page, "size": size}

@app.get("/api/graph/edges", response_model=PaginatedEdges)
async def list_edges(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    total = len(EDGES)
    items = paginate_items(EDGES, page, size)
    return {"items": items, "total": total, "page": page, "size": size}

@app.get("/api/graph/search", response_model=PaginatedNodes)
async def search_graph(q: str = Query(..., min_length=1), page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    ql = q.lower()
    matches = [n for n in NODES if ql in n.label.lower() or ql in n.type.lower() or ql in n.properties.get("title", "").lower()]
    total = len(matches)
    items = paginate_items(matches, page, size)
    return {"items": items, "total": total, "page": page, "size": size}

@app.get("/api/graph/node/{node_id}", response_model=NodeDetail)
async def get_node(node_id: str):
    node = NODE_MAP.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    # find direct neighbors
    neighbors = []
    for e in EDGES:
        if e.source == node_id:
            neighbors.append(NODE_MAP.get(e.target))
        elif e.target == node_id:
            neighbors.append(NODE_MAP.get(e.source))
    # remove None and dedupe
    neighbors = [n for n in neighbors if n]
    unique_neighbors = {n.id: n for n in neighbors}.values()
    return {"node": node, "neighbors": list(unique_neighbors)}
