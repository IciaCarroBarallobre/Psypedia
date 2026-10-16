"""Register the public API under a single URL prefix."""

from flask import Blueprint

from .chat import chat_api
from .health import health_api

api = Blueprint("api", __name__, url_prefix="/api")
api.register_blueprint(health_api)
api.register_blueprint(chat_api)
