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

from . import stats
from tools.utils.logs_analyser import get_search_terms
from flask import Response, send_file
from omero_search_engine import search_omero_app
import os
from omero_search_engine.validation.results_validator import (
    get_omero_stats,
)


@stats.route("/", methods=["GET"])
def index():
    return "OMERO search engine (stats API)"


@stats.route("/<resource>/search_terms", methods=["GET"])
def search_terms(resource):
    logs_folder = search_omero_app.config.get("SEARCHENGINE_LOGS_FOLDER")
    content = get_search_terms(logs_folder, resource=resource, return_file_content=True)
    return Response(
        content,
        mimetype="text/csv",
        headers={
            "Content-disposition": "attachment; filename=%s_stats.csv" % (resource)
        },
    )


@stats.route("/metadata", methods=["GET"])
def get_metadata():
    base_folder = "/etc/searchengine/"
    if not os.path.isdir(base_folder):
        base_folder = os.path.expanduser("~")
    metadata = os.path.join(base_folder, "metadata.csv")

    if os.path.isfile(metadata):
        return send_file(metadata, as_attachment=True)
    else:
        report = get_omero_stats(return_contents=True)
        return Response(
            report,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=metadata.csv"},
        )
