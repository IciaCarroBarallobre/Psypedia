"""PsyPedia application factory."""

import os

from flask import Flask

from .api import api
from .knowledge import DemoKnowledgeBase
from .providers.ollama import OllamaChatProvider
from .providers import ChatProvider
from .providers.mock import MockChatProvider
from .services.chat import ChatService


def create_app(test_config=None, *, chat_provider: ChatProvider | None = None):
    app = Flask(__name__)
    app.config.update({key: os.environ.get(key) for key in (
        "CHAT_PROVIDER", "OLLAMA_BASE_URL", "OLLAMA_MODEL", "OLLAMA_TIMEOUT"
    )})
    if test_config is not None:
        app.config.update(test_config)
    knowledge_base = None
    if chat_provider is not None:
        provider = chat_provider
    elif app.config["CHAT_PROVIDER"] == "mock":
        provider = MockChatProvider()
    elif app.config["CHAT_PROVIDER"] == "ollama":
        knowledge_base = DemoKnowledgeBase()
        for key in ("OLLAMA_BASE_URL", "OLLAMA_MODEL", "OLLAMA_TIMEOUT"):
            if not app.config.get(key) or not str(app.config[key]).strip():
                raise ValueError(f"Set {key} in .env (copy .env.example).")
        try:
            timeout = float(app.config["OLLAMA_TIMEOUT"])
        except (TypeError, ValueError) as exc:
            raise ValueError("OLLAMA_TIMEOUT must be between 0 and 120 seconds.") from exc
        if not 0 < timeout <= 120:
            raise ValueError("OLLAMA_TIMEOUT must be between 0 and 120 seconds.")
        provider = OllamaChatProvider(
            app.config["OLLAMA_BASE_URL"], app.config["OLLAMA_MODEL"], timeout
        )
    else:
        raise ValueError("Set CHAT_PROVIDER to 'ollama' or 'mock' in .env (copy .env.example).")
    app.extensions["chat_service"] = ChatService(provider, knowledge_base)
    app.register_blueprint(api)
    return app
