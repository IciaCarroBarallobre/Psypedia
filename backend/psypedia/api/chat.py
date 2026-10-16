"""Chat HTTP contract and input validation. Message content is not logged."""

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import BadRequest

from .errors import error_response

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
    return jsonify(answer=service.answer(message.strip()))
