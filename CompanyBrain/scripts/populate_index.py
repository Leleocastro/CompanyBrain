from pathlib import Path
import json
from api.embeddings_adapter import EmbeddingsAdapter

p = Path(__file__).resolve().parents[1] / 'index.json'
print('Index path:', p)
with p.open('r', encoding='utf-8') as f:
    data = json.load(f)

adapter = EmbeddingsAdapter()
for doc in data.get('documents', []):
    if not doc.get('embedding'):
        doc['embedding'] = adapter.embed_text(doc.get('text',''))

with p.open('w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Populated embeddings for', len(data.get('documents', [])))
