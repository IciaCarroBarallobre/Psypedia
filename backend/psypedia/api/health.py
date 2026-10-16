"""Backend availability endpoint."""

from flask import Blueprint, jsonify

health_api = Blueprint("health", __name__)


@health_api.get("/health")
def health():
    return jsonify(status="ok")
