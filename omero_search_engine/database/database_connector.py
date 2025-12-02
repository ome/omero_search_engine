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

import psycopg2
from sqlalchemy.orm import sessionmaker
from psycopg2.extras import RealDictCursor
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine


class DatabaseConnector(object):
    """
    An abstract base class which is inherited to provide different
    database operations,
    child classes need to implement all its methods:
    """

    DATABASE_BIND = ""
    DATABASE_NAME = ("",)
    session = ""
    engine = ""

    def _conn(self):
        return psycopg2.connect(self.DATABASE_BIND)

    def __init__(self, name, db_uri, echo_db=False):
        self.DATABASE_NAME = name
        self.DATABASE_URI = db_uri
        engine = create_engine(
            self.DATABASE_URI,
            # convert_unicode=True,
            echo=echo_db,
            pool=QueuePool(self._conn, pool_size=20, max_overflow=3, timeout=30),
        )
        self.engine = engine
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.session._model_changes = {}

    def execute_query(self, query, return_results=True):
        results = {}
        conn = psycopg2.connect(
            self.DATABASE_URI
        )  # options='-c statement_timeout=300000') #default units ms
        try:
            with conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("SET statement_timeout = '5000 s'")
                    cursor.execute(query)
                    if return_results:
                        results = cursor.fetchall()
                    else:
                        conn.commit()
        except Exception as e:
            from omero_search_engine import search_omero_app

            search_omero_app.logger.info(
                "Error while performing query %s, error message: %s" % (query, e)
            )
            # return None
            pass
        finally:
            conn.close()
        return results
