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

from celery import Celery

from configurations.configuration import (
    configLoader,
    load_configuration_variables_from_file,
    set_database_connection_variables,
)


def make_celery(beat=None):
    app_config = configLoader.get("development")
    load_configuration_variables_from_file(app_config)
    set_database_connection_variables(app_config)

    celery_app = Celery(
        "tasks",
        broker="redis://%s:%s/0" % (app_config.REDIS_URL, app_config.REDIS_PORT),
        backend="redis://%s:%s/0" % (app_config.REDIS_URL, app_config.REDIS_PORT),
    )
    if beat:
        from datetime import timedelta

        celery_app.conf.beat_schedule = {
            f"{beat}-every-hour": {
                "task": beat,
                # "schedule": 30.0,
                "schedule": timedelta(hours=1),
                "args": (),
            }
        }
    return celery_app, app_config
