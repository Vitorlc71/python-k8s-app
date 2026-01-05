from flask import Flask, redirect, request, jsonify, render_template, session, url_for
from kubernetes import client, config
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'my_super_mega_blaster_secret_key'

try:
    config.load_incluster_config()
except:
    config.load_kube_config()

apps_v1 = client.AppsV1Api()
core_v1 = client.CoreV1Api()

@app.route('/')
def index():
    print(request.headers)
    return render_template('index.html')

@app.before_request
def check_token_expiration():
    if request.path not in ['/login', '/static', '/logout']:
        auth_header = request.headers.get('Authorization')
        print(f'AUTH HEADER: {auth_header}')
        if not auth_header:
            return redirect(url_for('logout'))

@app.route('/logout')
def logout():
    print(request.headers)
    session.clear()
    auth_header = request.headers.get('Authorization')
    id_token = auth_header.split(' ')[1]
    return redirect(f"http://10.152.183.137:8080/realms/k8sapp/protocol/openid-connect/logout?id_token_hint={id_token}&post_logout_redirect_uri=http://proxy-server.local")

@app.route('/namespaces', methods=['GET'])
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

@app.route('/deployments/<namespace>', methods=['GET'])
def list_deployments(namespace):
    try:
        deployments = apps_v1.list_namespaced_deployment(namespace)
        lista = [{"name": d.metadata.name, "replicas": d.spec.replicas} for d in deployments.items]
        return jsonify(lista)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/scale', methods=['POST'])
def scale_deployment():
    data = request.json
    name = data['deployment_name']
    namespace = data['namespace']
    replicas = int(data['replicas'])
    
    body = {'spec': {'replicas': replicas}}
    apps_v1.patch_namespaced_deployment_scale(name, namespace, body)
    return jsonify({"status": f"Escalado para {replicas} replicas"})

@app.route('/restart', methods=['POST'])
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)