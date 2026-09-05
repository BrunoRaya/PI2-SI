import os
from pathlib import Path

from flask import Flask

from .db import init_app, init_db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-this-key"),
        DATABASE=str(Path(app.instance_path) / "pronto_socorro.db"),
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_app(app)

    from .routes import bp

    app.register_blueprint(bp)

    with app.app_context():
        init_db()

    return app
