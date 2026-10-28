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

contains_not_contains_queries = {
    "image": [["cell line", "hel"], ["gene symbol", "cep"]]
}

query_in = {
    "image": [
        ["Gene Symbol", ["pcnt", "cenpj", "cep120", "cdk5rap2"]],
        ["temperature", ["23 c", "37 c"]],
    ]
}

image_owner = {"image": [["cell line", "Hela", 103]]}

image_group = {"image": [["cell line", "Hela", 5]]}

image_owner_group = {"image": [["gene symbol", "cep120", 702, 5]]}

images_keys = ["cell line", "gene symbol"]

images_value_parts = ["hel", "prost"]

csv_test_data = [
    {"key": "organism", "value": "homo sapiens", "no_results": 15756},
    {"key": "gene symbol", "value": "pcnt", "no_results": 1484},
]

expired_token_wrong_sign = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvbWVuYW1lIjoidXNlci00OSIsImV4cCI6MTc4ODM2MzYyMCwiaXNfYWRtaW4iOmZhbHNlLCJzZXNzaW9uX2lkIjoiMjMxZTJjZGEtNzNhMC00YWNjLWExZmUtZGIxZDNjM2JlNzg5Iiwic2Vzc2lvbklkIjoxNzY4NTQsInVzZXJfaWQiOjgwOSwiZ3JvdXBzIjp7IjYiOnsibmFtZSI6IkxhYjMifSwiMyI6eyJuYW1lIjoiTGFiNCJ9LCI1Ijp7Im5hbWUiOiJMYWIxIn0sIjQiOnsibmFtZSI6IkxhYjIifX0sImRhdGFfc291cmNlIjoiaWRyIn0.pNmjqVXfga4hWUK7Qh5pHhkQmxCoqgUSBZcpAcdEmwI"  # noqa

expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvbWVuYW1lIjoidXNlci00OSIsImV4cCI6MTc5MTIzMTA0MSwiaXNfYWRtaW4iOmZhbHNlLCJzZXNzaW9uX2lkIjoiN2E3NTMzOGQtMTAwYi00NWUxLTllNjYtYzhjNGVmMmU3Y2JhIiwic2Vzc2lvbklkIjoxNzY4NTgsInVzZXJfaWQiOjgwOSwiZ3JvdXBzIjp7IjYiOnsibmFtZSI6IkxhYjMifSwiMyI6eyJuYW1lIjoiTGFiNCJ9LCI1Ijp7Im5hbWUiOiJMYWIxIn0sIjQiOnsibmFtZSI6IkxhYjIifX0sImRhdGFfc291cmNlIjoib21lcm9fdHJhaW4ifQ.QQXJCV7XsYJvbO18UIOSOVG5cI6jOO3WLPiGiZu0C6A"  # noqa

omename = "user-49"
public_user = "user-10"
data_source = "omero_train"
user_data = {
    "is_admin": False,
    "session_id": "7a75338d-100b-45e1-9e66-c8c4ef2e7cba",
    "sessionId": 176858,
    "user_id": 809,
    "groups": {
        6: {"name": "Lab3"},
        3: {"name": "Lab4"},
        5: {"name": "Lab1"},
        4: {"name": "Lab2"},
    },
    "data_source": data_source,
}

public_user_data = {
    "is_admin": False,
    "session_id": "538d0482-3d6f-4691-873b-af654a740fe9",
    "sessionId": 177794,
    "user_id": 13,
    "groups": {6: {"name": "Lab3"}, 5: {"name": "Lab1"}, 4: {"name": "Lab2"}},
    "data_source": data_source,
}

user_2_data = {
    "is_admin": False,
    # "is_expired": False,
    # "is_valid": True,
    "user_groups": {"153": {"name": "group1"}},
    "user_id": 252,
    "data_source": data_source,
}
