from flask import Blueprint

auth_resources = Blueprint("auth_resources", __name__)
import omero_search_engine.api.auth.urls  # noqa


# resources = Blueprint("resources2", __name__)
# import omero_search_engine.api.v1.resources.urls  # noqa
