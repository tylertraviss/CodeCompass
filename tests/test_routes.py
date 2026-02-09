import subprocess


def test_dashboard_route(client):
    """Dashboard should render successfully with questions loaded."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_about_us_route(client):
    """About page renders and contains header text."""
    response = client.get('/about')
    assert response.status_code == 200
    assert b"About Us" in response.data


def test_question_route(client):
    """Question page should include the specific LeetCode title from JSON data."""
    response = client.get('/question/1')
    assert response.status_code == 200
    assert b"Two Sum" in response.data


def test_question_route_invalid(client):
    """Invalid question IDs should respond with 404."""
    response = client.get('/question/999')
    assert response.status_code == 404
    assert b"Question not found" in response.data


def test_run_code_success(client):
    """/run_code should execute provided code and compare outputs."""
    payload = {
        'code': 'output = 1 + 1',
        'test_input': '',
        'expected_output': '2'
    }
    response = client.post('/run_code', json=payload)
    body = response.get_json()

    assert response.status_code == 200
    assert body['correct'] is True
    assert body['actual_output'] == '2'


def test_run_code_timeout(client, monkeypatch):
    """Timeouts from subprocess should send an error message."""

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd='python3', timeout=5)

    monkeypatch.setattr('code_editor_app.app.subprocess.run', fake_run)

    response = client.post('/run_code', json={'code': '', 'test_input': '', 'expected_output': ''})
    body = response.get_json()

    assert response.status_code == 200
    assert body['error'] == 'Code execution timed out.'


def test_get_summary_route(client):
    """Summary page should render the canned summary string."""
    response = client.get('/get_summary')
    assert response.status_code == 200
    assert b"summary of your progress" in response.data


def test_ask_ai_success(client, monkeypatch):
    """/ask_ai should return recruiter feedback when OpenAI succeeds."""

    def fake_chat_completion_create(**kwargs):
        return {"choices": [{"message": {"content": "Mock recruiter feedback."}}]}

    monkeypatch.setattr('code_editor_app.app.openai.ChatCompletion.create', fake_chat_completion_create)

    payload = {
        'query': 'Any tips?',
        'code': 'print("hello")',
        'problem_context': 'Reverse a string'
    }
    response = client.post('/ask_ai', json=payload)
    body = response.get_json()

    assert response.status_code == 200
    assert body['response'] == 'Mock recruiter feedback.'


def test_request_help_success(client, monkeypatch):
    """/request_help should return guidance when OpenAI succeeds."""

    def fake_chat_completion_create(**kwargs):
        return {"choices": [{"message": {"content": "Try breaking the problem into steps."}}]}

    monkeypatch.setattr('code_editor_app.app.openai.ChatCompletion.create', fake_chat_completion_create)

    payload = {
        'query': 'Help me',
        'code': 'print("test")',
        'problem_context': 'Two Sum'
    }
    response = client.post('/request_help', json=payload)
    body = response.get_json()

    assert response.status_code == 200
    assert body['response'] == 'Try breaking the problem into steps.'
