from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # デバッグ: Google Maps APIキーの確認
    print("Google Maps API Key:", app.config.get("GOOGLE_MAPS_API_KEY", "Not set"))

    db.init_app(app)
    migrate.init_app(app, db)

    from app import routes, models

    app.register_blueprint(routes.bp)

    # Google Maps API キーをテンプレートで利用できるようにコンテキストプロセッサで渡す
    @app.context_processor
    def inject_config():
        api_key = app.config.get("GOOGLE_MAPS_API_KEY")
        if not api_key:
            print("Warning: GOOGLE_MAPS_API_KEY is not set in the configuration")
        return dict(GOOGLE_MAPS_API_KEY=api_key)

    return app