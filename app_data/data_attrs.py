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

tables = ["projects", "images", "datasets", "plates"]
annotation_resource_link = {
    "image": "imageannotationlink",
    "project": "projectannotationlink",
    "plate": "plateannotationlink",
    "screen": "screenannotationlink",
    "well": "wellannotationlink",
}
# screen ==> study
distinct_study_name = """
Study Title
 Study Type
"""
distinct_gene_name = """
 Gene In Validation Screen
 Gene Description
 Gene Annotation
 Gene In Secondary Screen
 Gene Name
 Gene Annotation Comments
 Gene Expression Stromal Region
 Genetic Background Identifier
 Genetic Background
 Gene Identifier
 Gene Model Status
 Gene Identifier URL
 Gene Annotation Build
 Gene Symbol Synonyms
 Gene Hit for YAP Localization Inconsistent With Cell Shape
 Gene Symbol
 Gene Expression CIS Region
 Genetic Modification
 Gene Allele Name
"""
