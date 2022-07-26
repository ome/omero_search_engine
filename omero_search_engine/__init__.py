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
from flasgger import Swagger, LazyString, LazyJSONEncoder

from omero_search_engine.database.database_connector import DatabaseConnector
from configurations.configuration import (
    configLooader,
    load_configuration_variables_from_file,
    set_database_connection_variables,
)
from logging.handlers import RotatingFileHandler

from configurations.configuration import app_config as config_


template = {
    "swaggerUiPrefix": LazyString(
        lambda: request.environ.get("SCRIPT_NAME", "")
    )  # noqa
}


main_folder = os.path.dirname(os.path.realpath(__file__))


search_omero_app = Flask(__name__)

search_omero_app.json_encoder = LazyJSONEncoder


search_omero_app.config["SWAGGER"] = {
    "title": "OMERO Search Engine API",
    "version": "0.2.0",
}


swagger = Swagger(search_omero_app, template=template)

app_config = load_configuration_variables_from_file(config_)


def create_app(config_name="development"):
    app_config = configLooader.get(config_name)
    load_configuration_variables_from_file(app_config)
    set_database_connection_variables(app_config)
    database_connector = DatabaseConnector(
        app_config.DATABASE_NAME, app_config.DATABASE_URI
    )
    search_omero_app.config.from_object(app_config)
    search_omero_app.app_context()
    search_omero_app.app_context().push()
    search_omero_app.app_context()
    search_omero_app.app_context().push()
    es_connector = Elasticsearch(
        app_config.ELASTICSEARCH_URL,
        timeout=130,
        max_retries=20,
        retry_on_timeout=True,
        connections_per_node=10,
    )

    search_omero_app.config["database_connector"] = database_connector
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


create_app()

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
