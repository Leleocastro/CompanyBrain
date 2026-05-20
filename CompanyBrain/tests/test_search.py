from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_search_index_default():
    r = client.get('/search', params={'query':'embeddings','top_k':2, 'index':'CompanyBrain/index.json'})
    assert r.status_code == 200
    data = r.json()
    assert data['query'] == 'embeddings'
    assert isinstance(data['results'], list)
    assert len(data['results']) <= 2
