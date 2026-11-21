# 06 - Testing with mocks

Exercise: slide 93 + https://courses.dallard.tech/ci_cd/testing_python_intro/#mocking

| File | Content |
|---|---|
| [`groq_chat.py`](groq_chat.py) | `ask_groq()`, the function of the course that calls the Groq API |
| [`test_groq_chat.py`](test_groq_chat.py) | unit tests of `ask_groq()` with `mocker` (pytest-mock) |
| [`app.py`](app.py) | the FastAPI app of slide 93, corrected (list of fixes at the top of the file) |
| [`test_app.py`](test_app.py) | tests of the API with FastAPI's `TestClient` and a fake Groq client |

```bash
python -m pytest     # from the repository root: no API key and no network needed
```

## Why mock?

`ask_groq()` and `/chat` depend on an external service. Testing with the real API would be slow,
cost tokens, need a key, and fail whenever the network or Groq has a problem, even if *my* code is
correct. A mock is a fake object that replaces the API: I decide what it answers (or which error
it raises), and afterwards I can check how my code called it.

The course rule: **mock what you don't own, test what you own.** I don't test Groq; I test:

- the input validation (an empty question never reaches the API);
- the request I build (model, messages, `max_tokens`) with `assert_called_once_with`;
- what I do with the answer (extract the text, strip the spaces);
- the error handling: each Groq error becomes the right HTTP code.

| Groq error | HTTP answer of `/chat` |
|---|---|
| `APIConnectionError` (network, timeout) | 500 "API Connection Error" |
| `RateLimitError` | 429 "Rate Limit Exceeded" |
| other `APIStatusError` (e.g. 503) | same status code, "API Status Error" |
| no `GROQ_API_KEY` on the server | 503 with a clear message |
| invalid or empty body | 422 (Pydantic validation, Groq is not called) |

## Two techniques to replace the API

1. **Dependency injection**: the client is a parameter (`ask_groq(question, client=...)`) or a
   FastAPI dependency (`Depends(get_groq_client)`). The test simply gives a mock
   (`app.dependency_overrides[get_groq_client] = lambda: mock`). This is why the client is no longer
   created at import time in `app.py`.
2. **Patching**: `mocker.patch.object(groq_chat, "Groq")` replaces the class *where it is used*
   (`groq_chat.Groq`), not where it is defined (`groq.Groq`): `groq_chat` already imported its own
   reference to the class.

## Security

The API key is read from the `GROQ_API_KEY` environment variable and is **never** written in the
code. `.env` files are in `.gitignore`. To try the app for real (Git Bash):

```bash
export GROQ_API_KEY="your-key"     # only for the current terminal
python app.py                      # then open http://127.0.0.1:5000/docs
```
