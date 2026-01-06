from flask import Flask
from flask_jwt_extended import JWTManager
from .auth_utils import get_keycloak_public_key

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "my_super_mega_blaster_secret_key"

    # Configurações Keycloak
    KEYCLOAK_URL = "http://localhost:30080"
    REALM = "k8sapp"

    app.config["JWT_ALGORITHM"] = "RS256"
    app.config["JWT_PUBLIC_KEY"] = get_keycloak_public_key(KEYCLOAK_URL, REALM)
    
    # Opcional: define qual campo do token será o 'identity' (ex: 'sub' ou 'preferred_username')
    app.config["JWT_IDENTITY_CLAIM"] = "preferred_username" 

    jwt = JWTManager(app)

    # Registro do Blueprint
    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    app.config["JWT_COOKIE_SECURE"] = False  # Em produção, mude para True (requer HTTPS)
    app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token_cookie"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False

    # Registrar o blueprint
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app