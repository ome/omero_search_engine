from flask import Flask
import os
import logging
from celery import Celery
from elasticsearch import Elasticsearch

from celery.schedules import crontab
from search_engine.database.database_connector import DatabaseConnector
from configurations.configuration import configLooader,load_configuration_variables_from_file,set_database_connection_variables
from logging.handlers import RotatingFileHandler

from configurations.configuration import  app_config as config_

search_omero_app = Flask(__name__)

app_config =load_configuration_variables_from_file(config_)

#create celery app
def make_celery(app, config=config_):
    global celery
    celery = Celery(
        app.import_name,
        backend=config.CELERY_RESULT_BACKEND,
        broker=config.CELERY_BROKER_URL
    )
    app.config['CELERYBEAT_SCHEDULE'] = {
        # Executes every minute
        'periodic_task-every-minute': {
            'task': 'check_search_results',
            'schedule': crontab(minute="*")
        }
    }
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def create_app(config_name="development"):
    app_config=configLooader.get(config_name)
    load_configuration_variables_from_file(app_config)
    set_database_connection_variables(app_config)
    database_connector = DatabaseConnector(app_config.DATABAS_NAME, app_config.DATABASE_URI)
    #print (app_config.DATABAS_NAME, app_config.DATABASE_URI)
    search_omero_app.config.from_object(app_config)
    search_omero_app.app_context()
    search_omero_app.app_context().push()

    #celery.conf.update(search_omero_app.config)
    search_omero_app.app_context()
    search_omero_app.app_context().push()
    es_connector = Elasticsearch(app_config.ELASTICSEARCH_URL,
                                 timeout=130, max_retries=20, retry_on_timeout=True)

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

from search_engine.api.v2.resources import resources as resources_routers_blueprint_v2
search_omero_app.register_blueprint(resources_routers_blueprint_v2, url_prefix='/api/v2/resources')

from search_engine.searchresults import searchresults as search_results_routers_blueprint
search_omero_app.register_blueprint(search_results_routers_blueprint, url_prefix='/searchresults')

