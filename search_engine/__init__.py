from flask import Flask, request
import os
import logging
from elasticsearch import Elasticsearch
from flasgger import Swagger, LazyString, LazyJSONEncoder

from search_engine.database.database_connector import DatabaseConnector
from configurations.configuration import configLooader,load_configuration_variables_from_file,set_database_connection_variables
from logging.handlers import RotatingFileHandler

from configurations.configuration import  app_config as config_
from urllib.parse import urlparse
from flask import request, url_for as _url_for


template={"swaggerUiPrefix": LazyString(lambda: request.environ.get("SCRIPT_NAME", ""))}


main_folder=os.path.dirname(os.path.realpath(__file__))



search_omero_app = Flask(__name__)

search_omero_app.json_encoder = LazyJSONEncoder


search_omero_app.config['SWAGGER'] = {
    'title': 'OMERO Search Engine API',
    #'uiversion': 3
}


swagger = Swagger(search_omero_app, template=template)

app_config =load_configuration_variables_from_file(config_)

def create_app(config_name="development"):
    app_config=configLooader.get(config_name)
    load_configuration_variables_from_file(app_config)
    set_database_connection_variables(app_config)
    database_connector = DatabaseConnector(
        app_config.DATABASE_NAME,
        app_config.DATABASE_URI)
    search_omero_app.config.from_object(app_config)
    search_omero_app.app_context()
    search_omero_app.app_context().push()
    search_omero_app.app_context()
    search_omero_app.app_context().push()
    es_connector = Elasticsearch(app_config.ELASTICSEARCH_URL,
                                 timeout=130, max_retries=20, retry_on_timeout=True, connections_per_node=10)

    search_omero_app.config["database_connector"]=database_connector
    search_omero_app.config["es_connector"] = es_connector
    log_folder = os.path.join(os.path.expanduser('~'), 'logs')
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    file_handler = RotatingFileHandler(os.path.join(log_folder, 'omero_search_engine.log'), maxBytes=100240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    search_omero_app.logger.addHandler(file_handler)

    search_omero_app.logger.setLevel(logging.INFO)
    search_omero_app.logger.info('app assistant startup')
    return search_omero_app

create_app()


from search_engine.api.v1.resources import resources as resources_routers_blueprint_v1
search_omero_app.register_blueprint(resources_routers_blueprint_v1, url_prefix='/api/v1/resources')

from search_engine.searchresults import searchresults as search_results_routers_blueprint
search_omero_app.register_blueprint(search_results_routers_blueprint, url_prefix='/searchresults')

'''
#commented as it is ebaled at the NGINX confiuration level
#add it to account for CORS
@search_omero_app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header["Access-Control-Allow-Headers"]= "*"
    return response
'''
