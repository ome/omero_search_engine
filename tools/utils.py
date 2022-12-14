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

def copy_tools_subfolder():

    '''
    Copy the test_scripts folder to the searchengine folder
    '''
    subfolder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "test_scripts"
    )
    base_folder = "/etc/searchengine/"
    if not os.path.isdir(base_folder):
        destination_folder = os.path.expanduser("~")
    destination_folder=os.path.join(destination_folder, "test_scripts")

    if not os.path.isdir(destination_folder):
        shutil.copytree(subfolder, destination_folder)
