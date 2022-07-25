from flask import Blueprint
resources = Blueprint("resources2", __name__)
import omero_search_engine.api.v1.resources.urls
