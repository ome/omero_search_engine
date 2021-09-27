from flask import Blueprint
resources= Blueprint('resources', __name__)
import search_engine.api.v1.resources.urls
