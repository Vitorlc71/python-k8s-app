from flask import Blueprint, render_template, request, jsonify, redirect, make_response
import requests

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

# Configurações do seu Keycloak Client
KEYCLOAK_TOKEN_URL = "http://localhost:30080/realms/k8sapp/protocol/openid-connect/token"
CLIENT_ID = "k8sapp"
# Se o seu client for 'confidential', você precisará do CLIENT_SECRET:
CLIENT_SECRET = "7jt2DClytLx2dTTGKSx9IOIwpF4TPzJw" 

@auth_bp.route('/login', methods=['GET'])
def render_login():
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def do_login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Dados para solicitar o token ao Keycloak (Password Grant)
    payload = {
        'grant_type': 'password',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'username': username,
        'password': password,
        'scope': 'openid profile'
    }

    response = requests.post(KEYCLOAK_TOKEN_URL, data=payload)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')

        # Em um app web, costumamos salvar o token em um Cookie Seguro
        resp = make_response(redirect('/recurso-seguro'))
        resp.set_cookie('access_token_cookie', access_token, httponly=True)
        return resp
    else:
        return jsonify({"erro": "Login falhou no Keycloak", "detalhes": response.json()}), 401