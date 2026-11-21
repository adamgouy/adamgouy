"""ask_groq(): the function used in the "Mocking" part of the course.

It calls an external API (Groq). In the tests this API is replaced by a mock: no network,
no API key, no cost, and the tests always give the same result.
"""
from __future__ import annotations

import os

from groq import Groq

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def ask_groq(question: str, client: Groq | None = None) -> str:
    """Send one question to the Groq chat API and return the text of the answer.

    `client` can be given from outside (dependency injection): the tests pass a fake client.
    """
    question = question.strip()
    if not question:
        raise ValueError("The question cannot be empty")

    client = client or Groq()                         # reads GROQ_API_KEY from the environment
    response = client.chat.completions.create(
        model=os.environ.get("GROQ_MODEL", DEFAULT_MODEL),
        messages=[{"role": "user", "content": question}],
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    print(ask_groq("In one sentence, what is a unit test?"))
