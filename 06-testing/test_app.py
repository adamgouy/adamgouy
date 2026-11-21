"""Tests of the FastAPI app: real HTTP requests on the app, fake Groq client."""
import groq
import httpx
import pytest
from fastapi.testclient import TestClient

from app import DEFAULT_MODEL, app, get_groq_client

GROQ_URL = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")


@pytest.fixture
def http():
    return TestClient(app)


@pytest.fixture
def fake_groq(mocker):
    client = mocker.Mock()
    client.chat.completions.create.return_value.choices = [mocker.Mock()]
    client.chat.completions.create.return_value.choices[0].message.content = "Paris"
    app.dependency_overrides[get_groq_client] = lambda: client   # FastAPI's way to inject a mock
    yield client
    app.dependency_overrides.clear()


def test_status(http):
    response = http.get("/status")
    assert response.status_code == 200 and response.json() == {"message": "OK"}


def test_chat_returns_the_model_answer(http, fake_groq, monkeypatch):
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    response = http.post("/chat", json={"prompt": "Capital of France?"})
    assert response.status_code == 200
    assert response.json() == {"response": "Paris"}
    sent = fake_groq.chat.completions.create.call_args.kwargs
    assert sent["model"] == DEFAULT_MODEL
    assert sent["messages"][0]["role"] == "system"
    assert sent["messages"][-1] == {"role": "user", "content": "Capital of France?"}


@pytest.mark.parametrize("body", [{}, {"question": "wrong field"}, {"prompt": ""}])
def test_invalid_body_is_refused_without_calling_groq(http, fake_groq, body):
    assert http.post("/chat", json=body).status_code == 422
    fake_groq.chat.completions.create.assert_not_called()


@pytest.mark.parametrize("error, status, detail", [
    (groq.APIConnectionError(request=GROQ_URL), 500, "API Connection Error"),
    (groq.APITimeoutError(request=GROQ_URL), 500, "API Connection Error"),
    (groq.RateLimitError("too many requests", response=httpx.Response(429, request=GROQ_URL), body=None),
     429, "Rate Limit Exceeded"),
    (groq.APIStatusError("service unavailable", response=httpx.Response(503, request=GROQ_URL), body=None),
     503, "API Status Error"),
])
def test_groq_errors_become_http_errors(http, fake_groq, error, status, detail):
    fake_groq.chat.completions.create.side_effect = error
    response = http.post("/chat", json={"prompt": "Hello"})
    assert response.status_code == status
    assert response.json() == {"detail": detail}


def test_missing_api_key_gives_a_clear_503(http, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = http.post("/chat", json={"prompt": "Hello"})
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]
