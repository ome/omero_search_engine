#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2026 University of Dundee & Open Microscopy Environment.
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

import os
import time

from omero_search_engine.api.v1.resources.asyn_quries.make_celery import make_celery


celery_app, app_config = make_celery("clean_query_files")


@celery_app.task(
    name="clean_query_files",
    bind=True,
)
def clean_query_files(self):
    """
    check quires  files and delete them after the configured time (QUIRES_TTL)

    """

    quires_ttl = app_config.QUERIES_TTL
    quires_files_path = os.path.join(
        app_config.DATA_DUMP_FOLDER, app_config.QUIRES_FOLDER
    )
    quires_ttl_in_sec = time.time() - (quires_ttl * 86400)

    for filename in os.listdir(quires_files_path):
        file_path = os.path.join(quires_files_path, filename)

        if os.path.isdir(file_path):
            continue

        file_last_modifiied = os.path.getmtime(file_path)

        if file_last_modifiied < quires_ttl_in_sec:
            print(f"Deleting: {file_path} ")
            # os.remove(file_path)
