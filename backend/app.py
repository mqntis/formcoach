from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import config

jwt = JWTManager()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = config.FLASK_SECRET_KEY
    app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY

    CORS(app, origins=[config.FRONTEND_URL])
    jwt.init_app(app)

    from routes.health import health_bp
    from routes.auth import auth_bp
    from routes.sessions import sessions_bp
    from routes.upload import upload_bp
    from routes.joints import joints_bp
    from routes.analyze import analyze_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(sessions_bp, url_prefix="/api/sessions")
    app.register_blueprint(upload_bp, url_prefix="/api/upload")
    app.register_blueprint(joints_bp, url_prefix="/api/extract-joints")
    app.register_blueprint(analyze_bp, url_prefix="/api/analyze-form")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=config.FLASK_DEBUG)
