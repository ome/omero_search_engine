import pandas as pd
import numpy as np
import requests
import json
import copy
import os
import csv


# dataset should be added
def read_csv_file(file_name):
    df = pd.read_csv(file_name).replace({np.nan: None})
    return df


def get_values(data):
    for index, row in data.iterrows():
        for col in data.columns:
            if row[col]:
                print(col, ":", row[col])


dump_for_ome = "../data/SSBD_dump-for-ome.csv"
df = df = read_csv_file(dump_for_ome)

images_key_values = [
    "Organism",
    "Organism ontology",
    "Strain",
    "Strain ontology",
    "Cell line",
    "Cell line ontology",
    "Gene symbols",
    "Protein names",
    "Protein tags",
    "Reporter",
    "GO Biological Process",
    "GO Biological Process ontology",
    "GO Cellular Component",
    "GO Cellular Component ontology",
    "GO Molecular Function",
    "GO Molecular Function ontology",
]

project_keyvalues = [
    "Biological Imaging Method",
    "Title",
    "Biological Imaging Method ontology",
    "ssbd_dataset_id",
]


trouble_links = []
trouble_datasets = []
datasets_projects = {}
added_projects = []


def download_datasets_images():
    from datetime import datetime

    cou = 0
    for index, row in df.iterrows():
        if row.get("SSBD:OMERO Dataset ID") and row.get("SSBD:OMERO Project ID"):
            cou = cou + 1
            print("processing %s" % cou)
            datasets_projects[int(row.get("SSBD:OMERO Dataset ID"))] = int(
                row.get("SSBD:OMERO Project ID")
            )

            st = datetime.now()
            print(int(row.get("SSBD:OMERO Dataset ID")))
            dataset_id = int(row.get("SSBD:OMERO Dataset ID"))
            if os.path.isfile(
                "../data/ssbd_images/datasets_images_dataset_%s.json" % dataset_id
            ):
                print(
                    "Escap downloading, file ../data/ssbd_images/datasets_images_dataset_%s.json is exist"
                    % dataset_id
                )
                continue
            try:
                url = (
                    "https://ssbd.riken.jp/omero/webgateway/dataset/%s/children/"
                    % dataset_id
                )
                raise Exception
                res = requests.get(url)
                data = json.loads((res.text))
                with open(
                    "../data/ssbd_images/datasets_images_dataset_%s.json" % dataset_id,
                    "w",
                ) as outfile:
                    outfile.write(json.dumps(data, indent=4))

            except Exception as ex:
                print("error for url %s,  error message is: %s" % (url, ex))
                trouble_links.append(url)
                trouble_datasets.append(row.get("Dataset ID"))
                trouble_datasets.append(row.get("SSBD:OMERO Dataset ID"))
                if len(trouble_links) == 3:
                    print(trouble_datasets)
                    print(trouble_links)
            end = datetime.now()
            print(st, end)


images_data = []
projects_data = []
no_image_found_jsom = []


def extract_images_projects_data():
    files_counter = 0
    for index, row in df.iterrows():
        if not row.get("SSBD:OMERO Dataset ID"):
            continue
        files_counter += 1
        print("processing %s" % files_counter)
        dataset_id = int(row.get("SSBD:OMERO Dataset ID"))
        fname = "../data/ssbd_images/datasets_images_dataset_%s.json" % dataset_id
        if not os.path.isfile(fname):
            print("No images' file found for dataset: %s" % dataset_id)
            no_image_found_jsom.append(dataset_id)
            continue

        with open(fname) as f:
            images_json_data = json.load(f)
        print("Found")
        if row.get("SSBD:OMERO Project ID") not in added_projects:
            added_projects.append(row.get("SSBD:OMERO Project ID"))
            project = {}
            project["id"] = row.get("SSBD:OMERO Project ID")
            project["name"] = row.get("Project ID")
            project["description"] = row.get("Description")
            project_ = copy.deepcopy(project)
            projects_data.append(project)
            Project_title = copy.deepcopy(project_)
            projects_data.append(Project_title)
            Project_title["mapvalue_name"] = "Title"
            Project_title["mapvalue_value"] = row.get("Title")
            Project_title["mapvalue_index"] = 0
            for name in project_keyvalues:
                if row.get(name):
                    project__ = copy.deepcopy(project_)
                    projects_data.append(project__)
                    project__["mapvalue_name"] = name
                    project__["mapvalue_value"] = row.get(name)
                    project__["mapvalue_index"] = 0

        for image_ in images_json_data:
            image = {}
            images_data.append(image)
            image["id"] = int(image_.get("id"))
            image["name"] = image_.get("name")
            image["description"] = image_.get("description")
            image["dataset_id"] = dataset_id
            image["project_id"] = datasets_projects[image["dataset_id"]]
            image["project_name"] = row.get("Project ID")
            image["dataset_name"] = row.get("Dataset ID")
            iamge_name_ = copy.deepcopy(image)
            image["mapvalue_name"] = "thumb_url"
            image["mapvalue_value"] = "https://ssbd.riken.jp%s" % image_.get(
                "thumb_url"
            )
            image["mapvalue_index"] = 0
            iamge_name_url = copy.deepcopy(iamge_name_)
            images_data.append(iamge_name_url)
            iamge_name_url["mapvalue_name"] = "image_url"
            iamge_name_url["mapvalue_value"] = (
                "https://ssbd.riken.jp/omero/webclient/img_detail/%s" % image["id"]
            )
            iamge_name_url["mapvalue_index"] = 0

            dataset_url = copy.deepcopy(iamge_name_)
            images_data.append(dataset_url)
            dataset_url["mapvalue_name"] = "dataset_url"
            dataset_url["mapvalue_value"] = (
                "https://ssbd.riken.jp/omero/webclient/?show=dataset-%s" % dataset_id
            )
            dataset_url["mapvalue_index"] = 0
            for name in images_key_values:
                if row.get(name):
                    iamge_name = copy.deepcopy(iamge_name_)
                    images_data.append(iamge_name)
                    iamge_name_ = copy.deepcopy(image)
                    """   "Gene symbols",
                          "Protein names","""
                    if name == "Gene symbols":
                        iamge_name_["mapvalue_name"] = "Gene symbol"
                    elif name == "Protein names":
                        iamge_name_["mapvalue_name"] = "Protein name"
                    else:
                        iamge_name_["mapvalue_name"] = name
                    if (
                        row.get(name).lower() == "h. sapiens"
                        and name.lower() == "organism"
                    ):
                        iamge_name_["mapvalue_value"] = "Homo sapiens"
                    elif (
                        row.get(name).lower() == "hell cell"
                        and name.lower() == "cell line"
                    ):
                        iamge_name_["mapvalue_value"] = "hela"
                    elif (
                        row.get(name).lower() == "m. musculus"
                        and name.lower() == "organism"
                    ):
                        iamge_name_["mapvalue_value"] = "mus musculus"
                    else:
                        iamge_name_["mapvalue_value"] = row.get(name)


projects_filename = "../data/ssbd_images/ssbd_projects.csv"
images_filename = "../data/ssbd_images/ssbd_images.csv"
links_filename = "../data/ssbd_images/ssbd_links_error.csv"

download_datasets_images()
extract_images_projects_data()

keys = images_data[0].keys()
with open(images_filename, "w", newline="") as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(images_data)

projects_keys = [
    "id",
    "name",
    "description",
    "mapvalue_value",
    "mapvalue_name",
    "mapvalue_index",
]

with open(projects_filename, "w", newline="") as output_file:
    dict_writer = csv.DictWriter(output_file, projects_keys)
    dict_writer.writeheader()
    dict_writer.writerows(projects_data)


print(len(no_image_found_jsom))


print(len(trouble_links))

with open(links_filename, "w", newline="") as output_file:
    output_file.write("\n".join(trouble_links))
