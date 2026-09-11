"""Create a repeatable demonstration project in an isolated local API."""
import argparse
from urllib.parse import urlparse

import httpx

parser = argparse.ArgumentParser()
parser.add_argument('--api', default='http://127.0.0.1:8107')
args = parser.parse_args()
if urlparse(args.api).hostname not in {'localhost', '127.0.0.1'}:
    parser.error('デモ用のローカルAPIを指定してください')
with httpx.Client(base_url=args.api, timeout=60) as client:
    auth = client.post('/api/v1/auth/sign-in', json={'email': 'admin@example.com', 'password': 'Admin123!'})
    auth.raise_for_status()
    client.headers['Authorization'] = 'Bearer ' + auth.json()['accessToken']
    existing = client.get('/api/v1/ventures')
    existing.raise_for_status()
    name = 'デモ：問い合わせ支援AI'
    project = next((row for row in existing.json()['items'] if row['name'] == name and row['status'] != 'アーカイブ'), None)
    if project is None:
        result = client.post('/api/v1/ventures', json={
            'name': name, 'summary': '社内FAQを使い、問い合わせへの回答作成を支援するPoC。最終回答は担当者が確認します。',
            'scale': 'S', 'industry': '社内業務支援'})
        result.raise_for_status()
        project = result.json()
    print('/ventures/' + project['id'])
