from flask import Blueprint
searchresults= Blueprint('searchresults', __name__)
import omero_search_engine.searchresults.urls
