#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 University of Dundee & Open Microscopy Environment.
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

"""
This script reads the bia json files and creates the CSV files.
These CSV files will be used to index the data and push it to the elasticsearch
"""

import json
import copy
import csv
import random


def escape_string(string_to_check):
    if type(string_to_check) is not str:
        return string_to_check

    sb = ""
    for i in range(len(string_to_check)):
        c = string_to_check[i]
        # These characters are part of the query syntax and must be escaped
        reserved_chars_ = ["|", "!", "'", '"', "*", "\\", "\n", "\r"]
        if c in reserved_chars_:
            if not sb:
                sb = " "
            else:
                sb = sb + " "
        else:
            if not sb:
                sb = c
            else:
                sb = sb + c
    return sb


# All the path and file names should be configured to the hosted platform
bia_image_sample_json_file = "../data/bia-image-export.json"
bia_study_sample_json_file = "../data/bia-study-metadata.json"
bia_dataset_sample_json_file = "../data/bia-dataset-metadata.json"

with open(bia_study_sample_json_file) as f:
    studies = json.load(f)

with open(bia_image_sample_json_file) as f:
    images = json.load(f)

with open(bia_dataset_sample_json_file) as f:
    datasets = json.load(f)

print("Number of studies: ", len(studies))
print("Number of datasets: ", len(datasets))
print("Number of images: ", len(images))


def uuid_to_int(uuid_string):
    """
    the bia data does not have id but uuid so this function generates
    Ids to be used in the search engine
    :param uuid_string:
    :return:
    """
    return random.randint(0, 1000000)


projects_keyvalues = ["accession_id", "release_date", "licence", "uuid"]
projects_main = ["description", "study"]
projects_data = []
datasets_projects = {}
images_data = []
projects_id_name = {}
dataset_names_id = {}
images_without_url = []
project_id_uuid = {}
dataset_id_uuid = {}
values = []


def extract_dataset_projects():
    for st, dataset in datasets.items():
        datasets_projects[st] = dataset.get("submitted_in_study").get("uuid")
        dataset_names_id[st] = dataset.get("title_id")
        dataset_id_uuid[st] = uuid_to_int(st)


def extract_images_data():
    global keys
    added_key_value = []
    for st, imag in images.items():
        image = {}
        images_data.append(image)
        image["id"] = uuid_to_int(imag.get("uuid"))
        image["name"] = imag.get("uuid")
        image["description"] = imag.get("description")
        image["dataset_id"] = imag.get("submission_dataset_uuid")
        image["dataset_id"] = dataset_id_uuid[image["dataset_id"]]
        image["project_id"] = project_id_uuid[
            datasets_projects[imag.get("submission_dataset_uuid")]
        ]
        image["project_name"] = escape_string(
            projects_id_name[datasets_projects[imag.get("submission_dataset_uuid")]]
        )
        image["dataset_name"] = escape_string(
            dataset_names_id[imag.get("submission_dataset_uuid")]
        )
        image_ = copy.deepcopy(image)
        iamge_uid = copy.deepcopy(image_)
        images_data.append(iamge_uid)
        iamge_uid["mapvalue_name"] = "uuid"
        iamge_uid["mapvalue_value"] = imag.get("uuid")
        iamge_uid["mapvalue_index"] = 0
        iamge_project_uid = copy.deepcopy(image_)
        images_data.append(iamge_project_uid)
        iamge_project_uid["mapvalue_name"] = "project_uuid"
        iamge_project_uid["mapvalue_value"] = datasets_projects[
            imag.get("submission_dataset_uuid")
        ]
        iamge_project_uid["mapvalue_index"] = 0
        iamge_dataset_uid = copy.deepcopy(image_)
        images_data.append(iamge_dataset_uid)
        iamge_dataset_uid["mapvalue_name"] = "dataset_uuid"
        iamge_dataset_uid["mapvalue_value"] = image["dataset_id"]
        iamge_dataset_uid["mapvalue_index"] = 0
        index = 0
        for sample in imag["subject"]["sample_of"]:
            if is_added_before(
                image["id"],
                "organism",
                escape_string(sample["organism_classification"][0]["scientific_name"]),
                added_key_value,
            ):
                continue
            image_org = copy.deepcopy(image_)
            images_data.append(image_org)
            image_org["mapvalue_name"] = "organism"
            image_org["mapvalue_value"] = escape_string(
                sample["organism_classification"][0]["scientific_name"]
            )
            image_org["mapvalue_index"] = index
            added_key_value.append(image_org)
            if not keys:
                keys = image_org.keys()
            index = index + 1
        for key, value in imag["attribute"].items():
            if is_added_before(
                image_["id"], escape_string(key), escape_string(value), added_key_value
            ):
                continue

            if type(value) is str:
                if key not in values:
                    values.append(key)
                image_attr = copy.deepcopy(image_)
                images_data.append(image_attr)
                image_attr["mapvalue_name"] = escape_string(key)
                image_attr["mapvalue_value"] = escape_string(value)
                image_attr["mapvalue_index"] = 0
                added_key_value.append(image_attr)
        index = 0
        for file_ in imag["representation"]:
            # image_file = copy.deepcopy(image_)
            # images_data.append(image_file)
            # image_file["mapvalue_name"] = "image_format"
            # image_file["mapvalue_value"] = escape_string(file_["image_format"])
            # image_file["mapvalue_index"] = index
            image_file_ = copy.deepcopy(image_)
            images_data.append(image_file_)
            use_type = escape_string(file_["use_type"])
            if use_type == "THUMBNAIL":
                image_file_["mapvalue_name"] = "thumb_url"
            elif use_type == "UPLOADED_BY_SUBMITTER":
                image_file_["mapvalue_name"] = "image_url"
            else:
                image_file_["mapvalue_name"] = "file_uri"
            image_file_["mapvalue_index"] = index
            if len(file_["file_uri"]) == 0:
                images_without_url.append(st)
                image_file_["mapvalue_value"] = "None"
            else:
                image_file_["mapvalue_value"] = file_["file_uri"][0]
            # image_size = copy.deepcopy(image_)
            # images_data.append(image_size)
            # image_size["mapvalue_name"] = "image_size"
            # image_size["mapvalue_index"] = index
            # image_size["mapvalue_value"] = file_.get("total_size_in_bytes")
            # index = index


def is_added_before(id, key_, value_, added_key_value):
    added_before = False
    for item in added_key_value:
        if int(item["id"]) == int(id) and item["mapvalue_name"].lower() == key_.lower():
            if (
                item["mapvalue_value"].lower().strip() == value_.lower()
                or (
                    item["mapvalue_value"].lower() == "homo sapiens"
                    and value_.lower() == "h. sapiens"
                )
                or (
                    item["mapvalue_value"].lower() == "mus musculus"
                    and value_.lower() == "m. musculus"
                )
            ):
                added_before = True
                break
    return added_before


def extract_projects_data():
    added_key_value = []
    for st, study in studies.items():
        project = {}
        project["id"] = uuid_to_int(study.get("uuid"))
        project_id_uuid[study.get("uuid")] = project["id"]
        project["name"] = escape_string(study.get("title"))
        projects_id_name[study.get("uuid")] = study.get("title")
        project["description"] = escape_string(study.get("description"))
        project_ = copy.deepcopy(project)
        # projects_data.append(project)
        if study.get("Title"):
            Project_title = copy.deepcopy(project_)
            projects_data.append(Project_title)
            Project_title["mapvalue_name"] = "Title"
            Project_title["mapvalue_value"] = escape_string(study.get("Title"))
            Project_title["mapvalue_index"] = 0
        for name in projects_keyvalues:
            if study.get(name):
                project__ = copy.deepcopy(project_)
                projects_data.append(project__)
                project__["mapvalue_name"] = name
                project__["mapvalue_value"] = escape_string(study.get(name))
                project__["mapvalue_index"] = 0
        index = 0
        if study.get("experimental_imaging_component"):
            for entity_ in study.get("experimental_imaging_component"):
                entities = entity_.get("biological_entity")
                if entities:
                    for entity in entities:
                        if entity.get("organism_classification"):
                            for enti in entity.get("organism_classification"):
                                if not enti:
                                    continue
                                organism = enti.get("scientific_name")
                                if is_added_before(
                                    project["id"], "organism", organism, added_key_value
                                ):
                                    continue
                                project__o = copy.deepcopy(project_)
                                projects_data.append(project__o)
                                project__o["mapvalue_name"] = "organism"
                                project__o["mapvalue_value"] = escape_string(organism)
                                project__o["mapvalue_index"] = 0
                                added_key_value.append(project__o)

        if study.get("Author"):
            for author in study.get("Author"):
                index = index + 1
                project__ = copy.deepcopy(project_)
                projects_data.append(project__)
                project__["mapvalue_name"] = "author_name"
                project__["mapvalue_value"] = escape_string(author.get("name"))
                project__["mapvalue_index"] = index
                project___ = copy.deepcopy(project_)
                projects_data.append(project___)
                project___["mapvalue_name"] = "author_email"
                project__["mapvalue_value"] = author.get("contact_email")
                project__["mapvalue_index"] = index


keys = None
projects_filename = "../data/bia_projects.csv"
images_filename = "../data/bia_images.csv"

projects_keys = [
    "id",
    "name",
    "description",
    "mapvalue_value",
    "mapvalue_name",
    "mapvalue_index",
]
extract_projects_data()
with open(projects_filename, "w", newline="") as output_file:
    dict_writer = csv.DictWriter(output_file, projects_keys)
    dict_writer.writeheader()
    dict_writer.writerows(projects_data)

extract_dataset_projects()
extract_images_data()

print("datasets_projects", len(datasets_projects))
print("images_without_url", len(images_without_url))
print("projects:", len(projects_filename))


with open(images_filename, "w", newline="") as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(images_data)

print(len(values))
print("images:", len(images_filename))
