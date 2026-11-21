"""Unit tests of ask_groq() with mocks.

Rule from the course: mock what you don't own (the Groq API), test what you own
(input validation, the request we build, what we do with the answer and with errors).
"""
import pytest

import groq_chat
from groq_chat import DEFAULT_MODEL, ask_groq


def fake_groq_client(mocker, answer="4"):
    """A mock shaped like a real response: response.choices[0].message.content"""
    client = mocker.Mock()
    client.chat.completions.create.return_value.choices = [mocker.Mock()]
    client.chat.completions.create.return_value.choices[0].message.content = answer
    return client


def test_returns_the_answer_of_the_api(mocker):
    assert ask_groq("What is 2+2?", client=fake_groq_client(mocker, "  4 \n")) == "4"


def test_sends_the_right_request(mocker, monkeypatch):
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    client = fake_groq_client(mocker)
    ask_groq("  What is 2+2?  ", client=client)
    client.chat.completions.create.assert_called_once_with(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": "What is 2+2?"}],
        max_tokens=1024,
    )


def test_model_can_be_changed_with_an_environment_variable(mocker, monkeypatch):
    monkeypatch.setenv("GROQ_MODEL", "another-model")
    client = fake_groq_client(mocker)
    ask_groq("Hi", client=client)
    assert client.chat.completions.create.call_args.kwargs["model"] == "another-model"


@pytest.mark.parametrize("question", ["", "   ", "\n\t"])
def test_empty_question_is_refused_before_calling_the_api(mocker, question):
    client = fake_groq_client(mocker)
    with pytest.raises(ValueError):
        ask_groq(question, client=client)
    client.chat.completions.create.assert_not_called()


def test_api_errors_are_not_hidden(mocker):
    client = mocker.Mock()
    client.chat.completions.create.side_effect = ConnectionError("Groq is down")
    with pytest.raises(ConnectionError, match="Groq is down"):
        ask_groq("Hello", client=client)


def test_a_real_client_is_created_when_none_is_given(mocker):
    # patch Groq where it is USED (groq_chat.Groq), not where it is defined (groq.Groq)
    groq_class = mocker.patch.object(groq_chat, "Groq", return_value=fake_groq_client(mocker, "hi"))
    assert ask_groq("Hello") == "hi"
    groq_class.assert_called_once_with()
