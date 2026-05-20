from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def run():
    r = client.get('/health')
    assert r.status_code == 200
    print('health ok')

    r = client.get('/search', params={'query':'embeddings','top_k':2, 'index':'CompanyBrain/index.json'})
    assert r.status_code == 200
    data = r.json()
    assert data['query'] == 'embeddings'
    assert isinstance(data['results'], list)
    print('search ok, results:', len(data['results']))

if __name__ == '__main__':
    run()
