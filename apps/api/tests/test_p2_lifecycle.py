from uuid import uuid4
from fastapi.testclient import TestClient
from main import app


def setup_project():
    client = TestClient(app)
    auth = client.post('/api/v1/auth/sign-in', json={'email': 'admin@example.com', 'password': 'Admin123!'}).json()
    headers = {'Authorization': 'Bearer ' + auth['accessToken']}
    response = client.post('/api/v1/ventures', headers=headers, json={'name': 'P2 ' + uuid4().hex, 'scale': 'S'})
    assert response.status_code == 200, response.text
    return client, headers, '/api/v1/ventures/' + response.json()['id']


def test_template_classification_is_not_user_input():
    client, headers, base = setup_project()
    def count():
        summary = client.get(base + '/summary', headers=headers).json()
        return next(row for row in summary['ledgers'] if row['key'] == 'eval_plan')
    assert count()['filled'] == 0
    row = client.get(base + '/ledgers/eval_plan', headers=headers).json()['items'][0]
    # Even a client echoing the generated EvalType must not count as input.
    result = client.post(base + '/ledgers/eval_plan/entries', headers=headers, json={'id': row['id'], 'expectedRevision': row['revision'], 'values': row['values']})
    assert result.status_code == 200, result.text
    assert count()['filled'] == 0
    row = result.json()
    result = client.post(base + '/ledgers/eval_plan/entries', headers=headers, json={'id': row['id'], 'expectedRevision': row['revision'], 'values': {'EvalType': row['values']['EvalType'], '状態': '設計中'}})
    assert result.status_code == 200, result.text
    assert count()['filled'] == 1


def test_archive_is_read_only_and_reopen_requires_a_recorded_reason():
    client, headers, base = setup_project()
    before = {path: client.get(base + path, headers=headers).json()
              for path in ['/tasks', '/gates', '/skill-gap', '/ledgers/eval_plan']}
    archived = client.patch(base, headers=headers, json={'status': 'アーカイブ'})
    assert archived.status_code == 200, archived.text
    assert archived.json()['capabilities']['canReopen'] is True
    assert archived.json()['capabilities']['canEdit'] is False
    assert archived.json()['governance']['archiveSnapshotId']
    for path, original in before.items():
        assert client.get(base + path, headers=headers).json() == original
    for payload in [{'name': 'changed'}, {'status': '進行中'}, {'status': '進行中', 'reopenReason': '  '},
                    {'status': '進行中', 'reopenReason': '追加検証', 'name': 'changed'}]:
        assert client.patch(base, headers=headers, json=payload).status_code == 400
    task = before['/tasks']['items'][0]
    assert client.patch(base + '/tasks/' + task['id'], headers=headers, json={'status': '進行中'}).status_code == 400
    row = before['/ledgers/eval_plan']['items'][0]
    assert client.post(base + '/ledgers/eval_plan/entries', headers=headers,
                       json={'id': row['id'], 'expectedRevision': row['revision'], 'values': {}}).status_code == 400
    reopened = client.patch(base, headers=headers, json={'status': '進行中', 'reopenReason': '追加検証'})
    assert reopened.status_code == 200, reopened.text
    assert reopened.json()['governance']['reopenReason'] == '追加検証'
    assert reopened.json()['governance']['riskConfirmed'] is False
    assert reopened.json()['capabilities']['canManage'] is True
