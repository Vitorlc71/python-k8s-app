import requests

def get_keycloak_public_key(keycloak_url, realm_name):
    """Busca a chave pública RSA do Keycloak para validar tokens RS256."""
    url = f"{keycloak_url}/realms/{realm_name}"
    try:
        response = requests.get(url, timeout=5).json()
        return f"-----BEGIN PUBLIC KEY-----\n{response['public_key']}\n-----END PUBLIC KEY-----"
    except Exception as e:
        print(f"Erro ao buscar chave do Keycloak: {e}")
        return None