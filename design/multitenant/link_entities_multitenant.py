#!/usr/bin/env python3
"""Multi-tenant linking script (demo):
- loads enriched_seeds_multitenant.json
- links Documents to Entities only when tenant_id matches
- creates RELATED_TO edges only between documents of the same tenant
"""
import json
import os
import math

ROOT = os.path.dirname(__file__)
ENRICHED = os.path.join(ROOT, 'enriched_seeds_multitenant.json')
OUT = os.path.join(ROOT, 'linked_seeds_multitenant.json')


def cosine(a,b):
    num = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    if na==0 or nb==0: return 0.0
    return num/(na*nb)


def link():
    with open(ENRICHED, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = {n['id']: n for n in data.get('nodes', [])}
    edges = data.get('edges', [])[:]

    # Document -> Entity by mention_text exact match, only if tenant matches
    for n in data.get('nodes', []):
        if n.get('label') == 'Document':
            for e in data.get('nodes', []):
                if e.get('label') == 'Entity':
                    # only link within same tenant
                    if n.get('tenant_id') != e.get('tenant_id'):
                        continue
                    title = n.get('title','').lower()
                    if e.get('name','').lower() in title:
                        edges.append({'from': n['id'], 'to': e['id'], 'type':'MENTIONS', 'tenant_id': n.get('tenant_id'), 'confidence':0.9})

    # Relatedness by embedding cosine > 0.8, only within tenant
    docs = [n for n in data.get('nodes', []) if n.get('label')=='Document']
    for i in range(len(docs)):
        for j in range(i+1, len(docs)):
            if docs[i].get('tenant_id') != docs[j].get('tenant_id'):
                continue
            a = docs[i].get('embedding',[])
            b = docs[j].get('embedding',[])
            score = cosine(a,b)
            if score > 0.8:
                edges.append({'from': docs[i]['id'], 'to': docs[j]['id'], 'type':'RELATED_TO', 'tenant_id': docs[i].get('tenant_id'), 'score': score})

    out = {'nodes': list(nodes.values()), 'edges': edges}
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print('Linking complete ->', OUT)

if __name__ == '__main__':
    link()
