from flask import Blueprint, Flask, redirect, request, jsonify, render_template, session, url_for
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from kubernetes import client, config
from datetime import datetime

main_bp = Blueprint('main', __name__)

try:
    config.load_incluster_config()
except:
    config.load_kube_config()

apps_v1 = client.AppsV1Api()
core_v1 = client.CoreV1Api()

@main_bp.route('/recurso-seguro', methods=['GET'])
@jwt_required()
def get_secure_data():
    # Pega o ID do usuário (subject do JWT)
    user_id = get_jwt_identity()
    
    # Pega todos os dados (claims) contidos no token do Keycloak
    claims = get_jwt()
    
    # Exemplo: Acessando papéis (roles) do Realm configurados no Keycloak
    roles = claims.get("realm_access", {}).get("roles", [])

    return jsonify({
        "usuario": user_id,
        "roles": roles,
        "mensagem": "Token validado com sucesso pelo Keycloak!"
    }), 200

@main_bp.route('/admin-only', methods=['GET'])
@jwt_required()
def admin_only():
    claims = get_jwt()
    roles = claims.get("realm_access", {}).get("roles", [])
    
    if "admin" not in roles:
        return jsonify({"erro": "Acesso negado: Requer papel de admin"}), 403
        
    return jsonify({"status": "Acesso concedido ao painel administrativo"})

@main_bp.route('/')
@jwt_required()
def index():
    print(request.headers)
    return render_template('index.html')

#@main_bp.before_request
#def check_token_expiration():
#    if request.path not in ['/login', '/static', '/logout']:
#        auth_header = request.headers.get('Authorization')
#        print(f'AUTH HEADER: {auth_header}')
#        if not auth_header:
#            return redirect(url_for('main.logout'))

@main_bp.route('/logout')
def logout():
    print(request.headers)
    session.clear()
    auth_header = request.headers.get('Authorization')
    id_token = auth_header.split(' ')[1]
    return redirect(f"http://10.152.183.137:8080/realms/k8sapp/protocol/openid-connect/logout?id_token_hint={id_token}&post_logout_redirect_uri=http://proxy-server.local")

@main_bp.route('/namespaces', methods=['GET'])
@jwt_required()
def list_namespaces():
    try:
        namespaces = core_v1.list_namespace()

        forbidden = [
            'kube-system', 
            'ingress',
            'kube-public', 
            'kube-node-lease',
            'default'
        ]

        lista = [ns.metadata.name for ns in namespaces.items
                 if ns.metadata.name not in forbidden]
        return jsonify(lista)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/deployments/<namespace>', methods=['GET'])
@jwt_required()
def list_deployments(namespace):
    try:
        deployments = apps_v1.list_namespaced_deployment(namespace)
        lista = [{"name": d.metadata.name, "replicas": d.spec.replicas} for d in deployments.items]
        return jsonify(lista)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/scale', methods=['POST'])
@jwt_required()
def scale_deployment():
    data = request.json
    name = data['deployment_name']
    namespace = data['namespace']
    replicas = int(data['replicas'])
    
    body = {'spec': {'replicas': replicas}}
    apps_v1.patch_namespaced_deployment_scale(name, namespace, body)
    return jsonify({"status": f"Escalado para {replicas} replicas"})

@main_bp.route('/restart', methods=['POST'])
@jwt_required()
def restart_deployment():
    data = request.json
    name = data['deployment_name']
    namespace = data['namespace']
    
    now = datetime.now().isoformat()
    body = {
        'spec': {
            'template': {
                'metadata': {
                    'annotations': {
                        'kubectl.kubernetes.io/restartedAt': now
                    }
                }
            }
        }
    }
    apps_v1.patch_namespaced_deployment(name, namespace, body)
    return jsonify({"status": "Restart solicitado", "timestamp": now})
