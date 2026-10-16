"""Shared JSON error responses for API endpoints."""

from flask import jsonify


def error_response(code: str, message: str, status: int):
    return jsonify(error={"code": code, "message": message}), status
