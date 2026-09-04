from flask import Flask
from flask_session import Session
from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get('SECRET_KEY'):
        raise RuntimeError('SECRET_KEY must be set in the environment (via .env).')
    
    Session(app)
    
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.servers import servers_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(servers_bp)
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
