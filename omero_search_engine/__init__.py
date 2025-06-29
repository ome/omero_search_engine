#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2022 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from flask import Flask, make_response, request
import os
import logging
from elasticsearch import Elasticsearch
from flasgger import Swagger, LazyJSONEncoder
from flask_babel import LazyString

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time

from omero_search_engine.__version__ import __version__

from configurations.configuration import (
    configLooader,
    load_configuration_variables_from_file,
    set_database_connection_variables,
    get_configuration_file,
)
from logging.handlers import RotatingFileHandler

from configurations.configuration import app_config as config_


template = {
    "swaggerUiPrefix": LazyString(
        lambda: request.environ.get("SCRIPT_NAME", "")
    )  # noqa
}

environment_config_name = "development"

main_folder = os.path.dirname(os.path.realpath(__file__))


search_omero_app = Flask(__name__)

search_omero_app.json_encoder = LazyJSONEncoder

search_omero_app.config["SWAGGER"] = {
    "title": "OMERO Search Engine API",
    "version": str(__version__),
    "description": LazyString(
        lambda: "OMERO search engine app is used to search metadata"
        " (key-value pairs).\n"
        "For additional details, please refer to the following link:\n"
        "https://github.com/ome/omero_search_engine/blob/main/README.rst"
    ),
    "termsOfService": "https://github.com/ome/omero_search_engine/blob/main/LICENSE.txt",  # noqa
}


swagger = Swagger(search_omero_app, template=template)

app_config = load_configuration_variables_from_file(config_)


class ConfigHandler(FileSystemEventHandler):
    def on_modified(self, event):
        self.reload_configuration_from_file(event)

    def on_created(self, event):
        self.reload_configuration_from_file(event)

    def reload_configuration_from_file(self, event):
        try:
            if event.src_path.endswith(".app_config.yml"):
                if search_omero_app.config.get("AUTOMATIC_REFRESH"):
                    print("Configuration reloaded!")
                    create_app()
        except Exception as e:
            print("ERROR:   ===>>> %s" % e)


def create_app(config_name=None):
    global environment_config_name
    if not config_name:
        config_name = environment_config_name
    else:
        print("re-assign...")
        environment_config_name = config_name
    app_config = configLooader.get(config_name)
    load_configuration_variables_from_file(app_config)
    set_database_connection_variables(app_config)
    search_omero_app.config.from_object(app_config)
    search_omero_app.app_context()
    search_omero_app.app_context().push()
    search_omero_app.app_context()
    search_omero_app.app_context().push()
    ELASTIC_PASSWORD = app_config.ELASTIC_PASSWORD
    es_connector = Elasticsearch(
        app_config.ELASTICSEARCH_URL.split(","),
        verify_certs=app_config.verify_certs,
        timeout=130,
        max_retries=20,
        retry_on_timeout=True,
        connections_per_node=10,
        scheme="https",
        http_auth=("elastic", ELASTIC_PASSWORD),
    )
    search_omero_app.config.database_connectors = app_config.database_connectors
    print(search_omero_app.config.database_connectors)
    search_omero_app.config["es_connector"] = es_connector
    log_folder = os.path.join(os.path.expanduser("~"), "logs")
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    file_handler = RotatingFileHandler(
        os.path.join(log_folder, "omero_search_engine.log"),
        maxBytes=100240,
        backupCount=10,
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s:\
             %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    search_omero_app.logger.addHandler(file_handler)

    search_omero_app.logger.setLevel(logging.INFO)
    search_omero_app.logger.info("app assistant startup")

    return search_omero_app


def start_watcher():
    observer = Observer()
    observer.schedule(
        ConfigHandler(), path=os.path.dirname(get_configuration_file()), recursive=False
    )
    observer.start()
    try:
        while True:
            time.sleep(1)  # Prevents thread from exiting
    except Exception as ex:
        print("Error ,, %s" % ex)
        observer.stop()
    finally:
        observer.join()


watcher_thread = threading.Thread(target=start_watcher, daemon=True)
watcher_thread.start()

from omero_search_engine.api.v1.resources import (  # noqa
    resources as resources_routers_blueprint_v1,
)

search_omero_app.register_blueprint(
    resources_routers_blueprint_v1, url_prefix="/api/v1/resources"
)


# add it to account for CORS
@search_omero_app.after_request
def after_request(response):
    header = response.headers
    # header['Access-Control-Allow-Origin'] = '*'
    header["Access-Control-Allow-Headers"] = "*"
    return response


# added to let the user know the proper extension they should use
@search_omero_app.errorhandler(404)
def page_not_found(error):
    search_omero_app.logger.info("Error: %s" % error)
    resp_message = (
        "%s, You may use '/searchengine/api/v1/resources/' to test\
        the deployment and '/searchengine/apidocs/' for the Swagger documents."
        % error
    )
    response = make_response(resp_message, 404)
    response.mimetype = "text/plain"
    return response


if __name__ == "__main__":
    print("hi")
    create_app()
