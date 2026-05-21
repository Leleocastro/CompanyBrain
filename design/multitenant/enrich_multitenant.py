#!/usr/bin/env python3
"""Multi-tenant enrichment pipeline (demo):
- loads seed_data_multitenant.json
- populates fake embeddings and keywords while preserving tenant_id
- writes enriched_seeds_multitenant.json
"""
import json
import random
import os

ROOT = os.path.dirname(__file__)
SEED = os.path.join(ROOT, 'seed_data_multitenant.json')
OUT = os.path.join(ROOT, 'enriched_seeds_multitenant.json')

random.seed(42)

def fake_embedding(dim=8):
    return [random.random() for _ in range(dim)]


def enrich():
    with open(SEED, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for node in data.get('nodes', []):
        # keep tenant_id intact; if missing, assign to 'tenant:unknown'
        node.setdefault('tenant_id', 'tenant:unknown')
        if 'embedding' not in node:
            node['embedding'] = fake_embedding()
        # mock NER: mark documents with a keywords field
        if node.get('label') == 'Document':
            node.setdefault('keywords', [])
            node['keywords'].append('graph')
            node['keywords'].append('enrichment')

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print('Enrichment complete ->', OUT)

if __name__ == '__main__':
    enrich()
