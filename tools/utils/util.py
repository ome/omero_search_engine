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

import os
import shutil
import json
import sys
import logging


def copy_tools_subfolder():
    """
    Copy the maintenance_scripts folder to the maintenance_scripts
    inside the searchengine folder
    """
    subfolder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "../maintenance_scripts"
    )
    destination_folder = "/etc/searchengine/"
    if not os.path.isdir(destination_folder):
        destination_folder = os.path.expanduser("~")
    destination_folder = os.path.join(destination_folder, "maintenance_scripts")

    if not os.path.isdir(destination_folder):
        shutil.copytree(subfolder, destination_folder)


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

"""
this script read the log file and get the search terms
it analyses the file and produces reports
e.g. csv files contain the search terms
"""


def get_search_terms(folder_name):
    resourses = {}
    for root, dirs, files in os.walk(folder_name):
        for file_name in files:
            if file_name.endswith("engine_gunilog.log"):
                file_name = os.path.join(root, file_name)
                analyse_log_file(file_name, resourses)
    logging.info("Write the reports")
    write_reports(resourses, os.path.join(folder_name, "report.csv"))


def analyse_log_file(file_name, resourses):
    # file_name="/mnt/d/logs/engine_gunilog.log"
    logging.info("Analyse: %s" % file_name)
    f = open(file_name, "r")
    contents = f.read()
    logs = contents.split(
        "INFO in query_handler: -------------------------------------------------"
    )
    f.close()

    failes = 0
    suc = 0
    co = 0
    filters = []
    for i in range(0, len(logs), 2):
        cont = logs[i].split(("\n"))
        lo = cont[1].split("in query_handler:")
        ss = "{'and_filters':" + lo[-1].split("{'and_filters':")[-1]
        if "[20]" in ss:
            continue
        co += 1
        ss = ss.replace("'", '"').replace("False", "false").replace("None", '"None"')
        try:
            filters.append(json.loads(ss, strict=False))
            suc = suc + 1
        except:  # noqa
            failes = failes + 1

    for filter in filters:
        check_filters(filter.get("and_filters"), resourses)
        for or_f in filter.get("or_filters"):
            check_filters(or_f, resourses)


def check_filters(conds, resourses):
    for cond in conds:
        if cond.get("resource") in resourses:
            names_values = resourses[cond.get("resource")]
        else:
            names_values = {}
            resourses[cond.get("resource")] = names_values
        name = cond.get("name")
        value = cond.get("value")
        if name in names_values:
            names_values[name].append(value)
        else:
            names_values[name] = [value]


def write_reports(resourses, file_name):
    for res, itms in resourses.items():
        lines = ["key,total hits,unique hits"]
        for name, values in itms.items():
            line = [name]
            vv = []
            for val in values:
                line.append(val)
                if val not in vv:
                    vv.append(val)
            line.insert(1, str(len(values)))
            line.insert(2, str(len(vv)))
            lines.append(",".join(line))
        f = open(file_name.replace(".csv", "_%s.csv" % res), "w")
        f.write("\n".join(lines))
        f.close()
