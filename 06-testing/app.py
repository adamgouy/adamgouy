"""FastAPI + Groq app from slide 93, corrected so that it runs and can be tested.

What I changed compared to the slide:
- `import os` was missing;
- the model `mixtral-8x7b-32768` has been removed by Groq: the model is now read from the
  GROQ_MODEL environment variable, with a current model as default;
- the Groq client was created at import time: importing the file (in the tests, for example)
  failed without an API key. It is now given to the endpoint by a FastAPI dependency
  (`Depends(get_groq_client)`), which the tests replace with a mock;
- if the API key is missing, the API answers 503 with a clear message instead of crashing;
- an empty prompt is refused by Pydantic (422) before calling Groq;
- `RateLimitError` is a subclass of `APIStatusError`, so it must be caught BEFORE it.

Run it:  set GROQ_API_KEY, then `python app.py` and open http://127.0.0.1:5000/docs
"""
from __future__ import annotations

import os
from functools import lru_cache

import groq
from fastapi import Depends, FastAPI, HTTPException
from groq import Groq
from pydantic import BaseModel, Field

DEFAULT_MODEL = "llama-3.3-70b-versatile"

app = FastAPI(title="Groq chat API")


class Prompt(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)


@lru_cache(maxsize=1)
def _build_client(api_key: str) -> Groq:
    # one client reused by all requests, 20 s timeout instead of 60 s, one retry
    return Groq(api_key=api_key, timeout=20.0, max_retries=1)


def get_groq_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured")
    return _build_client(api_key)


@app.get("/status")
async def get_status():
    return {"message": "OK"}


@app.post("/chat")
async def post_chat(prompt: Prompt, client: Groq = Depends(get_groq_client)):
    try:
        completion = client.chat.completions.create(
            model=os.environ.get("GROQ_MODEL", DEFAULT_MODEL),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt.prompt},
            ],
        )
    except groq.APIConnectionError:
        raise HTTPException(status_code=500, detail="API Connection Error")
    except groq.RateLimitError:
        raise HTTPException(status_code=429, detail="Rate Limit Exceeded")
    except groq.APIStatusError as error:
        raise HTTPException(status_code=error.status_code, detail="API Status Error")
    return {"response": completion.choices[0].message.content}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)
