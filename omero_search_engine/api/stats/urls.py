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
from flask import Response, send_file, request
from omero_search_engine import search_omero_app, auth
import os
from omero_search_engine.validation.results_validator import (
    get_omero_stats,
)


@stats.route("/", methods=["GET"])
def index():
    return "OMERO search engine (stats API)"


@stats.route("/searchterms", methods=["GET"])
@auth.login_required
def search_terms():
    """
    Search the logs file to extract the search terms
    and return them to an excel file containing the
    search terms and number of hits, unique hits
    each resource has a sheet inside the excel book
    """
    logs_folder = search_omero_app.config.get("SEARCHENGINE_LOGS_FOLDER")
    if not logs_folder or not os.path.isdir(logs_folder):
        logs_folder = "/etc/searchengine/logs"
        if not os.path.isdir(logs_folder):
            logs_folder = os.path.expanduser("~/logs")
    if not os.path.isdir(logs_folder):
        return "No logs files are found"

    max_top_values = request.args.get("return_values")
    if not max_top_values:
        max_top_values = 5
    elif max_top_values.isdigit():
        max_top_values = int(max_top_values)
    else:
        if max_top_values.lower() != "all":
            max_top_values = 5
        else:
            max_top_values = "all"
    content = get_search_terms(logs_folder, max_top_values, return_file_content=True)
    headers = {
        "Content-Disposition": "attachment; filename=searchterms.xlsx",
        "Content-type": "application/vnd.ms-excel",
    }
    return Response(content.getvalue(), headers=headers)


@stats.route("/metadata", methods=["GET"])
@auth.login_required
def get_metadata():
    """
    Search the database to extract a metadata about each resource
    for the common terms
    It returns an Excel book which contains the attribute and
    its number of buckets in addition to a link to the buckets
    """
    base_folder = "/etc/searchengine/"
    if not os.path.isdir(base_folder):
        base_folder = os.path.expanduser("~")
    metadata = os.path.join(base_folder, "metadata.xlsx")
    base_url = request.base_url.replace("stats/metadata", "v1/resources/")
    if not os.path.isfile(metadata):
        if "/searchengine/searchengine" in base_url:
            base_url = base_url.replace("/searchengine/searchengine", "/searchengine")
        get_omero_stats(base_url=base_url)

    return send_file(metadata, as_attachment=True)
