"""PsyPedia application factory."""

from flask import Flask

from .api import api
from .providers import ChatProvider
from .providers.mock import MockChatProvider
from .services.chat import ChatService


def create_app(test_config=None, *, chat_provider: ChatProvider | None = None):
    app = Flask(__name__)
    if test_config is not None:
        app.config.update(test_config)
    provider = MockChatProvider() if chat_provider is None else chat_provider
    app.extensions["chat_service"] = ChatService(provider)
    app.register_blueprint(api)
    return app
