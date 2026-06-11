import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.utils.llm_helper import call_groq_llm
from app.config import settings

@pytest.mark.asyncio
async def test_llm_disabled():
    with patch.object(settings, "use_llm_agents", False):
        res = await call_groq_llm("test prompt")
        assert res is None

@pytest.mark.asyncio
async def test_llm_no_key():
    with patch.object(settings, "use_llm_agents", True):
        with patch.object(settings, "groq_api_key", ""):
            res = await call_groq_llm("test prompt")
            assert res is None

@pytest.mark.asyncio
async def test_llm_api_call_mock():
    with patch.object(settings, "use_llm_agents", True):
        with patch.object(settings, "groq_api_key", "gsk_test_key"):
            # Mock the httpx Response using a regular MagicMock (since response.json() is synchronous)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Dynamic LLM reasoning response"
                        }
                    }
                ]
            }

            # Use AsyncMock for the async post call
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response
                res = await call_groq_llm("Analyze inventory", "You are an AI.")
                assert res == "Dynamic LLM reasoning response"
                mock_post.assert_called_once()
