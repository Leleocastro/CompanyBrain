from fastapi.testclient import TestClient
from api.mock_graph.main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_list_nodes_pagination():
    r = client.get("/api/graph/nodes?page=1&size=5")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 5

def test_list_edges_pagination():
    r = client.get("/api/graph/edges?page=1&size=10")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 10

def test_search():
    # we know nodes have labels like "Person 1", search for "Person"
    r = client.get("/api/graph/search?q=Person")
    assert r.status_code == 200
    data = r.json()
    assert all("Person" in n["label"] or n["type"] == "Person" for n in data)

def test_get_node_and_neighbors():
    # pick known node id n1
    r = client.get("/api/graph/node/n1")
    assert r.status_code == 200
    body = r.json()
    assert "node" in body and "neighbors" in body
    assert body["node"]["id"] == "n1"
