from unittest.mock import patch

import pytest

from utils.model_loader import ModelLoader


def test_groq_provider_requires_a_key():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            ModelLoader(model_provider="groq").load_llm()


def test_openai_provider_uses_configured_model_name():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
        with patch("utils.model_loader.ChatOpenAI") as chat_openai:
            ModelLoader(model_provider="openai").load_llm()

    chat_openai.assert_called_once_with(model="o4-mini", api_key="test-key")