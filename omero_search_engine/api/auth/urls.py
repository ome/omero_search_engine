from flask import request, jsonify

from omero_search_engine.api.auth.utils import create_token, get_jwt_from_request
from . import auth_resources


@auth_resources.route("/login", methods=["POST"])
def login():
    """
    file: swagger_docs/login.yml
    """
    from ..v1.resources.utils import build_error_message

    data = request.get_json(silent=True)
    # data = request.get_json()
    if not data:
        return jsonify(
            build_error_message(
                "Error: {error}".format(
                    error="No user data (user name and password) is provided "
                )
            )
        )
    try:
        # data = json.loads(data)
        username = data.get("username")
        password = data.get("password")
        session_id = data.get("session_id")
        datasource = data.get("data_source")
        if (not username and not password) and not session_id:
            raise Exception("Username and password are required")
    except Exception as e:
        print("Error is: %s" % str(e))
        return jsonify(
            build_error_message(
                "{error}".format(error="No proper user data is provided ")
            )
        )
    try:
        if username:
            username = username.strip()
        if password:
            password = password.strip()
        if session_id:
            session_id = session_id.strip()
        if not session_id and (not username or not password) or not datasource:
            return "session id or username and password and datasource are required"

        token = create_token(datasource, username, password, session_id)
        return jsonify(token)
    except Exception as e:
        print("Error is %s" % str(e))
        return jsonify({"Error": "%s" % e})


@auth_resources.route("/verify_token/", methods=["GET"])
def verify_token():
    """
    file: swagger_docs/verify_token.yml
    """
    token = get_jwt_from_request()
    return jsonify(token)


"""
{"username": "user-49", "password": "omero", "data_source": "idr"}
"""
