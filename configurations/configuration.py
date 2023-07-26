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

import yaml
from shutil import copyfile
import os
import json


def load_configuration_variables_from_file(config):
    # loading application configuration variables from a file
    print("Injecting config variables from :%s" % app_config.INSTANCE_CONFIG)
    with open(app_config.INSTANCE_CONFIG) as f:
        cofg = yaml.load(f)
    for x, y in cofg.items():
        setattr(config, x, y)
    if hasattr(config, "verify_certs"):
        try:
            verify_certs = json.load(config.verify_certs)
        except Exception as ex:
            print(str(ex))
            verify_certs = False
    else:
        verify_certs = False
    config.verify_certs = verify_certs
    if not verify_certs:
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning

        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def set_database_connection_variables(config):
    """
    set the databases attributes using configuration class
    i.e. databases name, password and uri
    :param database: databse name
    :return:
    """
    if hasattr(config, "DATABASE_PORT"):
        address = config.DATABASE_SERVER_URI + ":%s" % app_config.DATABASE_PORT
    else:
        address = config.DATABASE_SERVER_URI
    app_config.database_connector = ""
    app_config.DATABASE_URI = "postgresql://%s:%s@%s/%s" % (
        config.DATABASE_USER,
        config.DATABASE_PASSWORD,
        address,
        config.DATABASE_NAME,
    )


def update_config_file(updated_configuration):
    is_changed = False
    with open(app_config.INSTANCE_CONFIG) as f:
        configuration = yaml.load(f)
    found = []
    for key, value in updated_configuration.items():
        if key in configuration:
            if configuration[key] != value:
                configuration[key] = value
                is_changed = True
                print("%s is Updated, new value is %s " % (key, value))
            else:
                found.append(key)
    if len(found) != len(updated_configuration):
        for key, value in updated_configuration.items():
            if key not in found:
                configuration[key] = value
                print("%s value is added with value %s " % (key, value))
                is_changed = True

    if is_changed:
        with open(app_config.INSTANCE_CONFIG, "w") as f:
            yaml.dump(configuration, f)


class app_config(object):
    # the configuration can be loadd from yml file later
    home_folder = os.path.expanduser("~")

    INSTANCE_CONFIG = os.path.join(home_folder, ".app_config.yml")
    DEPLOYED_CONFIG = r"/etc/searchengine/.app_config.yml"
    if not os.path.isfile(INSTANCE_CONFIG):
        # Check if the configuration file exists in the docker deployed folder
        # if not, it will assume it is either development environment or
        # deploying using other methods

        if os.path.isfile(DEPLOYED_CONFIG):
            INSTANCE_CONFIG = DEPLOYED_CONFIG
        else:
            LOCAL_CONFIG_FILE = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), "app_config.yml"
            )
            copyfile(LOCAL_CONFIG_FILE, INSTANCE_CONFIG)
            print(LOCAL_CONFIG_FILE, INSTANCE_CONFIG)


class development_app_config(app_config):
    DEBUG = False
    VERIFY = False


class production_app_config(app_config):
    pass


class test_app_config(app_config):
    pass


configLooader = {
    "development": development_app_config,
    "testing": test_app_config,
    "production": production_app_config,
}
