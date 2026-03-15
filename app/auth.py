from flask import current_app, jsonify, request

try:
    import jwt
except ImportError:  # pragma: no cover - allows read-only app boot before deps install
    jwt = None


FIREBASE_JWKS_URL = "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com"
JWKS_CLIENT = jwt.PyJWKClient(FIREBASE_JWKS_URL) if jwt else None


def get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not auth_header.startswith(prefix):
        return None
    return auth_header[len(prefix):].strip()


def verify_firebase_token(id_token):
    if not jwt or not JWKS_CLIENT:
        raise ValueError("PyJWT is not installed on the server.")

    project_id = current_app.config["TIDE_SETTINGS"]["firebase"]["projectId"]
    if not project_id:
        raise ValueError("FIREBASE_PROJECT_ID is not configured.")

    signing_key = JWKS_CLIENT.get_signing_key_from_jwt(id_token)
    decoded = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=project_id,
        issuer=f"https://securetoken.google.com/{project_id}",
    )
    if not decoded.get("sub"):
        raise ValueError("Token is missing sub.")
    return decoded


def require_actor():
    id_token = get_bearer_token()
    if not id_token:
        return None, (jsonify({"error": "Missing bearer token."}), 401)

    try:
        decoded = verify_firebase_token(id_token)
    except Exception as exc:  # pragma: no cover - defensive auth boundary
        return None, (jsonify({"error": f"Invalid auth token: {exc}"}), 401)

    actor = {
        "email": decoded.get("email"),
        "sub": decoded.get("sub"),
        "display_name": decoded.get("name") or decoded.get("email") or decoded.get("sub"),
        "identifier": decoded.get("email") or decoded.get("sub"),
    }
    if not actor["identifier"]:
        return None, (jsonify({"error": "Token missing email and sub."}), 401)
    return actor, None
