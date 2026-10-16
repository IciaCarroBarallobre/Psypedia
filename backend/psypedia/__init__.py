"""PsyPedia application factory."""

from flask import Flask

from .routes import api


def create_app(test_config=None):
    app = Flask(__name__)
    if test_config is not None:
        app.config.update(test_config)
    app.register_blueprint(api)
    return app
