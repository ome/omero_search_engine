import jwt
from flask import request
from flask import current_app
import datetime

from omero_search_engine.api.auth.OMERO_connector.utils import (
    connect_omero,
    verify_session,
)


def create_token(datasource, omename, password, session_id, encode_token=True):
    data = connect_omero(datasource, omename, password, session_id)
    print(data)
    if len(data) > 0:
        if encode_token:
            return {"token": build_token(data, omename)}
        else:
            return data
    else:
        return {
            "message": "could not verify",
            "code": 401,
            "Authentication": "login required",
        }


def build_token(data, omename):
    from omero_search_engine import search_omero_app

    # JWT expire after 2 hrs by default unless
    # it has been configured otherwise using
    # set_JWT_expire_time
    jwt_exp = search_omero_app.config.get("JWT_EXPIRE_TIME")
    if not jwt_exp:
        jwt_exp = 120
    exp = int(
        round(
            (
                datetime.datetime.utcnow() + datetime.timedelta(minutes=jwt_exp)
            ).timestamp()
        )
    )
    token = jwt.encode(
        {**{"omename": omename, "exp": exp}, **data},
        current_app.config["SECRET_KEY"],
        "HS256",
    )
    return token


def check_token(token, check_session=False, decode=True):
    if decode:
        try:
            token_data = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
        except Exception as e:
            print("Error is %s" % str(e))
            return {"is_valid": False, "error": str(e)}
    else:
        token_data = token

    if check_session:
        if token_data.get("session_id"):
            if not verify_session(
                token_data.get("data_source"), token_data.get("session_id")
            ):
                return {"is_valid": False}
        else:
            return {"is_valid": False}

    user_groups = token_data.get("groups")
    is_admin = token_data.get("is_admin")
    user_id = token_data.get("user_id")
    is_expired = False
    is_valid = True
    return {
        token_data.get("data_source"): {
            "is_valid": is_valid,
            "is_expired": is_expired,
            "user_groups": user_groups,
            "is_admin": is_admin,
            "user_id": user_id,
            "data_source": token_data.get("data_source"),
        }
    }


def get_jwt_from_request():
    auth_header = request.headers.get("Authorization")
    auth = None
    if auth_header and len(auth_header.split(" ")) == 2:
        token = auth_header.split(" ")[1]
    else:
        token = auth_header
    if token:
        # check if the token is valid
        auth = check_token(token)

    return auth


def is_datasource_public(datasource):
    from omero_search_engine import search_omero_app

    for data_source in search_omero_app.config.get("DATA_SOURCES"):
        if type(datasource) is list:
            if data_source.get("name").lower() in datasource:
                return data_source.get("public")
        else:
            if data_source.get("name").lower() == datasource.lower():
                return data_source.get("public")
    return None


def get_data_source_server_url(datasource):
    from omero_search_engine import search_omero_app

    if not search_omero_app.config.get("DATA_SOURCES"):
        from omero_search_engine import create_app

        create_app()
    for data_source in search_omero_app.config.get("DATA_SOURCES"):
        if type(datasource) is list:
            if data_source.get("name").lower() in datasource:
                host = data_source.get("SERVER_URL")
                port = data_source.get("SERVER_PORT")
                return host, port
        else:
            if data_source.get("name").lower() == datasource.lower():
                host = data_source.get("SERVER_URL")
                port = data_source.get("SERVER_PORT")
                return host, port
    return None, None


def get_public_user_details(datasource):
    from omero_search_engine import search_omero_app

    for data_source in search_omero_app.config.get("DATA_SOURCES"):
        if data_source.get("name").lower() == datasource.lower():
            public_username = data_source.get("public_username")
            public_user_password = data_source.get("public_user_password")
            session_id = data_source.get("session_id")
            if (public_username and public_user_password) or session_id:
                return session_id, public_username, public_user_password
    return None, None, None


def update_session_id(datasource, session_id):
    database_config = {"DATABASE": {}, "session_id": session_id, "name": datasource}
    from configurations.configuration import update_config_file

    update_config_file(database_config, data_source=True)


def check_for_public_user(datasource):
    session_id, public_username, public_user_password = get_public_user_details(
        datasource
    )

    if (public_username and public_user_password) or session_id:
        print(public_username, public_user_password)
        # get a token
        token = create_token(
            datasource,
            public_username,
            public_user_password,
            session_id=session_id,
            encode_token=False,
        )
        if not token.get("session_id"):
            return {"is_valid": False}
        if token.get("session_id") != session_id:
            update_session_id(datasource, token.get("session_id"))
            print("Not found or not valid, saved new one ", token.get("session_id"))
        token_data = check_token(token, check_session=False, decode=False)
        return token_data
    return None


def combine_tokens(token, public_token, data_ssource):
    """
    combine public and user logg in user in case of private data source
    """
    if token and not token.get(data_ssource) and not token.get("is_valid"):
        if public_token:
            return public_token
    elif (
        public_token
        and not public_token.get(data_ssource)
        and not public_token.get("is_valid")
    ):
        if token:
            return token
    elif not public_token and token:
        return token
    elif not token and public_token:
        return public_token

    if token and public_token:
        for data_source in token:
            new_groups = token.get(data_source).get("user_groups")
            for group in public_token[data_source].get("user_groups"):
                if str(group) not in new_groups:
                    new_groups[group] = public_token[data_source].get("user_groups")[
                        group
                    ]
            token[data_source]["user_groups"] = new_groups
        return token
    elif not public_token and token:
        return token
    elif not token and public_token:
        return public_token
    else:
        return None
