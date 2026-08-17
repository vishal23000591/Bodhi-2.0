import json

import httpx
import pytest
import respx

from app.services import openrouter_client
from app.services.openrouter_client import OpenRouterError


async def test_chat_completion_returns_content(test_settings):
    with respx.mock:
        respx.post(f"{test_settings.openrouter_base_url}/chat/completions").mock(
            return_value=httpx.Response(
                200, json={"choices": [{"message": {"content": "hello student"}}]}
            )
        )
        result = await openrouter_client.chat_completion([{"role": "user", "content": "hi"}])
    assert result == "hello student"


async def test_chat_completion_sends_configured_model(test_settings):
    with respx.mock:
        route = respx.post(f"{test_settings.openrouter_base_url}/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
        )
        await openrouter_client.chat_completion([{"role": "user", "content": "hi"}])

    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body["model"] == test_settings.openrouter_chat_model


async def test_chat_completion_raises_on_http_error(test_settings):
    with respx.mock:
        respx.post(f"{test_settings.openrouter_base_url}/chat/completions").mock(
            return_value=httpx.Response(500, text="boom")
        )
        with pytest.raises(OpenRouterError):
            await openrouter_client.chat_completion([{"role": "user", "content": "hi"}])


async def test_chat_completion_json_parses_content(test_settings):
    with respx.mock:
        respx.post(f"{test_settings.openrouter_base_url}/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": '{"topics": ["a", "b"]}'}}]},
            )
        )
        data = await openrouter_client.chat_completion_json([{"role": "user", "content": "hi"}])
    assert data == {"topics": ["a", "b"]}


async def test_chat_completion_json_raises_on_invalid_json(test_settings):
    with respx.mock:
        respx.post(f"{test_settings.openrouter_base_url}/chat/completions").mock(
            return_value=httpx.Response(
                200, json={"choices": [{"message": {"content": "not json"}}]}
            )
        )
        with pytest.raises(OpenRouterError):
            await openrouter_client.chat_completion_json([{"role": "user", "content": "hi"}])


async def test_embed_texts_returns_vectors_in_order(test_settings):
    with respx.mock:
        respx.post(f"{test_settings.openrouter_base_url}/embeddings").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"index": 1, "embedding": [0.2, 0.2]},
                        {"index": 0, "embedding": [0.1, 0.1]},
                    ]
                },
            )
        )
        result = await openrouter_client.embed_texts(["first", "second"])
    assert result == [[0.1, 0.1], [0.2, 0.2]]


async def test_embed_texts_empty_input_short_circuits(test_settings):
    result = await openrouter_client.embed_texts([])
    assert result == []
