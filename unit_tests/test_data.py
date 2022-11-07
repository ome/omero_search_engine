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

sql = "select current_database()"
valid_and_filters = [
    {"name": "Organism", "value": "Homo sapiens", "operator": "equals"},
    {"name": "Antibody Identifier", "value": "CAB034889", "operator": "equals"},
]

valid_or_filters = [
    [
        {"name": "Organism Part", "value": "Prostate", "operator": "equals"},
        {"name": "Organism Part Identifier", "value": "T-77100", "operator": "equals"},
    ]
]

not_valid_and_filters = [
    {"name": "Organism", "value": "Mus musculus"},
    {"name": "Organism Part", "operator": "equals", "value": "Prostate"},
]
not_valid_or_filters = []

# query = {"query_details": {"and_filters":
#                           [{"name": "Organism", "value": "Homo sapiens",
#                             "operator": "equals", 'resource': "image"},
#                            {"name": "Antibody Identifier",
#                             "value": "CAB034889",
#                             "operator": "equals", "resource": "image"}],
#                           "or_filters":
#                           [{"name": "Organism Part",
#                             "value": "Prostate",
#                             "operator": "equals",
#                             "resource": "image"},
#                            {"name": "Organism Part Identifier",
#                             "value": "T-77100",
#                             "operator": "equals", "resource": "image"}]}}

query = {"query_details": {"and_filters": []}}

query_image_and = [
    [["Phenotype Annotation Level", "protein"], ["organism", "homo sapiens"]]
]

query_image_or = [[["Gene Symbol", "CDK5RAP2"], ["Gene Symbol", "cep120"]]]

query_image_and_or = [
    {
        "query_image_and": [
            ["Organism", "homo sapiens"],
            ["Targeted Protein", "CDK5RAP2"],
            ["Phenotype Term Accession", "CMPO_0000425"],
        ],
        "query_image_or": [
            ["Phenotype", "protein localized to centrosome"],
            ["Gene Symbol", "http://www.ebi.ac.uk/cmpo/CMPO_0000425"],
        ],
    }
]

simple_queries = {
    "image": [
        ["cell line", "Hela"],
        ["PBS", "10Mm"],
        ["Gene Symbol", "CDK5RAP2"],
        ["organism", "homo sapiens"],
        ["temperature", "37"],
    ]
}

contains_not_contains_quries = {"image": [["cell line", "hel"], ["gene symbol", "cep"]]}

query_in = {
    "image": [
        ["Gene Symbol", ["pcnt", "cenpj", "cep120", "cdk5rap2"]],
        ["temperature", ["23 c", "37 c"]],
    ]
}

images_keys = ["cell line", "ene symbol"]

images_value_parts = ["he", "pr"]
