from omero_search_engine import search_omero_app
from datetime import datetime
from omero_search_engine.validation.psql_templates import (
    tail_space_query,
    head_space_query,
    duplicated_keyvalue_pairs_query,
)
import os
import pandas as pd

conn = search_omero_app.config["database_connector"]


def prepare_the_sql_statment(sql_template, screen_name, project_name, add_where=""):
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


def check_for_tail_space(screen_name, project_name):
    search_omero_app.logger.info("Cheking for tail space ...")
    sql_statment = prepare_the_sql_statment(
        tail_space_query, screen_name, project_name, " and"
    )
    tail_space_results = conn.execute_query(sql_statment)
    if len(tail_space_results) == 0:
        search_omero_app.logger.info("No results is aviable fro tail space")
        return
    search_omero_app.logger.info("Generate for tail space ...")
    genrate_reports(tail_space_results, "tail_space", screen_name, project_name)


def check_for_head_space(screen_name, project_name):
    search_omero_app.logger.info("Cheking for head space ...")
    sql_statment = prepare_the_sql_statment(
        head_space_query, screen_name, project_name, " and"
    )
    head_space_results = conn.execute_query(sql_statment)
    if len(head_space_results) == 0:
        search_omero_app.logger.info("No results is aviablefor head space")
        return
    search_omero_app.logger.info("Generate for head space ...")
    genrate_reports(head_space_results, "head_space", screen_name, project_name)


def check_duplicated_keyvalue_pairs(screen_name, project_name):
    search_omero_app.logger.info("Cheking for dupblicated keyvalue pairs ...")
    sql_statment = prepare_the_sql_statment(
        duplicated_keyvalue_pairs_query, screen_name, project_name, "where"
    )
    duplicated_keyvalue_pairs_results = conn.execute_query(sql_statment)
    if len(duplicated_keyvalue_pairs_results) == 0:
        search_omero_app.logger.info(
            "No results is aviable for dupblicated keyvalue pairs "
        )
        return
    search_omero_app.logger.info("Generate reports for dupblicated keyvalue pairs ...")
    genrate_reports(
        duplicated_keyvalue_pairs_results,
        "dupblicated_keyvalue_pairs",
        screen_name,
        project_name,
    )


def genrate_reports(results, check_type, screen_name, project_name):
    start = datetime.now()
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
            .rename(columns={0: "no of images"})
        )
        with open(screens_file, "w") as text_file:
            text_file.write(df2.to_csv())
        search_omero_app.logger.info(df2.sum())

    if (not screen_name and not project_name) or project_name:
        df3 = (
            df.groupby(["project_name", "name", "value"])
            .size()
            .reset_index()
            .rename(columns={0: "no of images"})
        )

        with open(projects_file, "w") as text_file:
            text_file.write(df3.to_csv())
        search_omero_app.logger.info(df3.sum())
    end = datetime.now()
    search_omero_app.logger.info("Start time: %s" % str(start))
    search_omero_app.logger.info("End time: %s" % str(end))
