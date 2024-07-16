#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2024 University of Dundee & Open Microscopy Environment.
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

from omero_search_engine import search_omero_app
from omero_search_engine.validation.psql_templates import (
    trail_space_query,
    head_space_query,
    duplicated_keyvalue_pairs_query,
)
import os
import pandas as pd

conn = search_omero_app.config["database_connector"]


def prepare_the_sql_statement(sql_template, screen_name, project_name, add_where=""):
    """
    customize the sql statement
    """
    if not screen_name and project_name:
        return sql_template.substitute(
            condition=" {add_where} project.name like '%{project_name}%'".format(
                add_where=add_where, project_name=project_name
            )
        )
    elif not project_name and screen_name:
        return sql_template.substitute(
            condition=" {add_where} screen.name like '%{screen_name}%'".format(
                add_where=add_where, screen_name=screen_name
            )
        )
    elif not screen_name and not project_name:
        return sql_template.substitute(condition="")


def check_for_trailing_space(screen_name, project_name):
    search_omero_app.logger.info("Checking for trailing space ...")
    sql_statment = prepare_the_sql_statement(
        trail_space_query, screen_name, project_name, " and"
    )
    tail_space_results = conn.execute_query(sql_statment)
    if len(tail_space_results) == 0:
        search_omero_app.logger.info("No results is availlable for trailing space")
        return
    search_omero_app.logger.info("Generate for trailing space ...")
    genrate_reports(tail_space_results, "tailing_space", screen_name, project_name)


def check_for_heading_space(screen_name, project_name):
    search_omero_app.logger.info("Checking for heading space ...")
    sql_statment = prepare_the_sql_statement(
        head_space_query, screen_name, project_name, " and"
    )
    head_space_results = conn.execute_query(sql_statment)
    if len(head_space_results) == 0:
        search_omero_app.logger.info("No results available for heading space")
        return
    search_omero_app.logger.info("Generate for head space ...")
    genrate_reports(head_space_results, "heading_space", screen_name, project_name)


def check_duplicated_keyvalue_pairs(screen_name, project_name):
    search_omero_app.logger.info("Checking for duplicated key-value pairs ...")
    sql_statment = prepare_the_sql_statement(
        duplicated_keyvalue_pairs_query, screen_name, project_name, "where"
    )
    duplicated_keyvalue_pairs_results = conn.execute_query(sql_statment)
    if len(duplicated_keyvalue_pairs_results) == 0:
        search_omero_app.logger.info(
            "No results available for duplicated key-value pairs "
        )
        return
    search_omero_app.logger.info("Generate reports for duplicated key-value pairs ...")
    genrate_reports(
        duplicated_keyvalue_pairs_results,
        "duplicated_keyvalue_pairs",
        screen_name,
        project_name,
    )


def genrate_reports(results, check_type, screen_name, project_name):
    """
    Generate the output CSV files contents and save them
    """
    df = pd.DataFrame(results)
    base_folder = "/etc/searchengine/"
    if not os.path.isdir(base_folder):
        base_folder = os.path.expanduser("~")

    all_fields_file = os.path.join(base_folder, "all_%s.csv" % check_type)
    screens_file = os.path.join(base_folder, "screens_%s.csv" % check_type)
    projects_file = os.path.join(base_folder, "projects_%s.csv" % check_type)

    with open(all_fields_file, "w") as text_file:
        text_file.write(df.to_csv())

    if (not screen_name and not project_name) or screen_name:
        df2 = (
            df.groupby(["screen_name", "name", "value"])
            .size()
            .reset_index()
            .rename(columns={0: "number of images"})
        )
        with open(screens_file, "w") as text_file:
            text_file.write(df2.to_csv())
        search_omero_app.logger.info(df2.sum())

    if (not screen_name and not project_name) or project_name:
        df3 = (
            df.groupby(["project_name", "name", "value"])
            .size()
            .reset_index()
            .rename(columns={0: "number of images"})
        )

        with open(projects_file, "w") as text_file:
            text_file.write(df3.to_csv())
        search_omero_app.logger.info(df3.sum())
