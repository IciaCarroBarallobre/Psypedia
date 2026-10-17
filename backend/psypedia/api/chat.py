"""Chat HTTP contract and input validation. Message content is not logged."""

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import BadRequest

from .errors import error_response
from psypedia.providers import ProviderUnavailable, ProviderTimeout, ProviderInvalidResponse

chat_api = Blueprint("chat", __name__)


@chat_api.post("/chat")
def chat():
    if not request.is_json:
        return error_response(
            "unsupported_media_type", "Use Content-Type: application/json.", 415
        )

    try:
        payload = request.get_json()
    except BadRequest:
        return error_response(
            "invalid_json", "Request body must contain valid JSON.", 400
        )

    message = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(message, str) or not message.strip():
        return error_response(
            "invalid_message", "message must be a non-empty string.", 400
        )

    service = current_app.extensions["chat_service"]
    try:
        answer = service.answer(message.strip())
    except ProviderUnavailable:
        return error_response(
            "provider_unavailable", "Ollama or the configured model is unavailable. Check the service and model installation.", 503
        )
    except ProviderTimeout:
        return error_response("provider_timeout", "The model took too long to answer. Please try again.", 504)
    except ProviderInvalidResponse:
        return error_response("invalid_provider_response", "The model returned an invalid answer. Please try again.", 502)
    return jsonify(answer=answer)
