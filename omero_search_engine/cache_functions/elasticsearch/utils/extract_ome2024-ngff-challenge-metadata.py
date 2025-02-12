import json
import os
import sys

import pandas as pd
import random
import copy
import math

tax_id_org = {}

def escape_string(string_to_check):
    return string_to_check
    if type(string_to_check) is not str:
        return string_to_check

    sb = ''
    for i in range(len(string_to_check)):
        c = string_to_check[i]
        # These characters are part of the data and should be removed
        reserved_chars_ = ["'", '"', "*", "\\", "\n", "\r"]
        if c in reserved_chars_:
            if not sb:
                sb = ' '
            else:
                sb = sb + ' '
        else:
            if not sb:
                sb = c
            else:
                sb = sb + c
    return sb


def read_ro_crate_metadata(crate_path):

    metadata_path = crate_path  # os.path.join(crate_path, "ro-crate-metadata.json")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"No RO-Crate metadata found at {metadata_path}")

    # Read and parse the JSON-LD metadata
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return metadata


def extract_data_from_metadata(metadata):
    extracted_data = {
        "crate_name": metadata.get("@graph", [{}])[0].get("name", "Unnamed Crate"),
        "crate_description": metadata.get("@graph", [{}])[0].get("description", "No description"),
        "files": [],
        "datasets": [],
    }

    # Extract files and datasets from the "@graph"
    for item in metadata.get("@graph", []):
        if item.get("@type") == "File":
            extracted_data["files"].append({
                "id": item.get("@id"),
                "name": item.get("name", item.get("@id")),
                "description": item.get("description", "No description"),
            })
        elif item.get("@type") == "Dataset":
            extracted_data["datasets"].append({
                "id": item.get("@id"),
                "name": item.get("name", item.get("@id")),
                "description": item.get("description", "No description"),
            })

    return extracted_data

def main(crate_path):
    try:
        # Read the RO-Crate metadata
        metadata = read_ro_crate_metadata(crate_path)
        # Extract data from metadata
        extracted_data = extract_data_from_metadata(metadata)
        # Display the extracted data
        print("\nExtracted Data:")
        print(f"Crate Name: {extracted_data['crate_name']}")
        print(f"Description: {extracted_data['crate_description']}")
        print("\nFiles:")
        for file in extracted_data["files"]:
            print(f"  - {file['name']} ({file['id']})")
        print("\nDatasets:")
        for dataset in extracted_data["datasets"]:
            print(f"  - {dataset['name']} ({dataset['id']})")
    except Exception as e:
        print(f"Error: {e}")


def read_metadata_file(crate_path):
    propreties = {}

    from rocrate.rocrate import ROCrate

    # Create an ROCrate object
    crate = ROCrate(crate_path)

    # Load the metadata from the JSON file
    # crate.load(crate_path)

    # Access the metadata
    metadata = crate.metadata
    # print(metadata.__dict__)
    # Access all entities in the RO-Crate, including the metadata
    for entity in crate.get_entities():

        if entity.type == "Dataset":
            propreties["datePublished"] = entity.properties().get("datePublished")
            propreties["name"] = entity.properties().get("name")
            propreties["description"] = entity.properties().get("description")
            propreties["license"] = entity.properties().get("license")

        else:
            if entity.type == "image_acquisition":
                propreties["image_acquisition"] = entity.properties().get("image_acquisition")
        # print (type(entity.properties()))
        if "organism_classification" in entity.properties():
            # print ("FOUND",entity.properties().get("organism_classification").get("@id"))
            propreties["organism"] = entity.properties().get("organism_classification").get("@id")

    return propreties


def get_entity(pubmed_id):
    import requests
    tax_id = None

    # Define the base URL for the E-utilities API
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    # Define the parameters for the query
    params = {
        "db": "pubmed",
        "id": pubmed_id,
        "retmode": "json"
    }

    # Make the request
    response = requests.get(base_url + "efetch.fcgi", params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the response in JSON format
        data = response.json()
        # print(data)
        tax_id = data
    else:
        print(f"Error: {response.status_code}")

    return tax_id


def test():
    import requests
    import xml.etree.ElementTree as ET

    # Define the PubMed ID you want to fetch
    pubmed_id = "NCBI:txid9606"

    # Define the base URL for the E-utilities API
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    # Define the parameters for the query
    params = {
        "db": "pubmed",
        "id": pubmed_id,
        "retmode": "xml"
    }

    # Make the request
    response = requests.get(base_url + "efetch.fcgi", params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the XML response
        root = ET.fromstring(response.content)

        # Find the PubmedArticle element
        pubmed_article = root.find("PubmedArticle")
        '''
        MedlineCitation

        PMID
        DateCompleted
        DateRevised
        Article
        MedlineJournalInfo
        CitationSubset
        MeshHeadingList

        PubmedData~:
        History
        PublicationStatus
        ArticleIdList
        '''

        # Find and explore the MedlineCitation element
        medline_citation = pubmed_article.find("MedlineCitation/PMID")
        if medline_citation is not None:
            for child in medline_citation:
                print(child.tag)
        else:
            print("MedlineCitation element not found.")
    else:
        print(f"Error: {response.status_code}")


def test_2():
    import requests
    import xml.etree.ElementTree as ET

    # Define the PubMed ID you want to fetch
    pubmed_id = "NCBI:txid9606"

    # Define the base URL for the E-utilities API
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    # Define the parameters for the query
    params = {
        "db": "pubmed",
        "id": pubmed_id,
        "retmode": "xml"
    }

    # Make the request
    response = requests.get(base_url + "efetch.fcgi", params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the XML response
        root = ET.fromstring(response.content)

        # Find the PubmedArticle element
        pubmed_article = root.find("PubmedArticle")

        # Find and explore the MedlineCitation element
        medline_citation = pubmed_article.find("MedlineCitation")
        if medline_citation is not None:
            # Look for MeshHeadingList element which contains organism information
            mesh_heading_list = medline_citation.find("MeshHeadingList")
            if mesh_heading_list is not None:
                for mesh_heading in mesh_heading_list.findall("MeshHeading"):
                    descriptor_name = mesh_heading.find("DescriptorName")
                    if descriptor_name is not None and 'Organism' in descriptor_name.attrib.get('MajorTopicYN', ''):
                        print(f"Organism Classification: {descriptor_name.text}")
                    elif descriptor_name is not None:
                        print(f"Descriptor: {descriptor_name.text}")
            else:
                print("MeshHeadingList not found.")
        else:
            print("MedlineCitation element not found.")
    else:
        print(f"Error: {response.status_code}")


def test_3():
    import requests
    import xml.etree.ElementTree as ET
    # Define the PubMed ID you want to fetch
    pubmed_id = "NCBI:txid9606"
    # Define the base URL for the E-utilities API
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    # Define the parameters for the query
    params = {
        "db": "pubmed",
        "id": pubmed_id,
        "retmode": "xml"
    }

    # Make the request
    response = requests.get(base_url + "efetch.fcgi", params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the XML response
        root = ET.fromstring(response.content)

        # Find the PubmedArticle element
        pubmed_article = root.find("PubmedArticle")

        # Find and explore the MedlineCitation element
        medline_citation = pubmed_article.find("MedlineCitation")
        if medline_citation is not None:
            # Print all child elements and their text
            for elem in medline_citation.iter():
                print(elem.tag, elem.text)
        else:
            print("MedlineCitation element not found.")
    else:
        print(f"Error: {response.status_code}")


def get_organism(tax_id):
    import requests

    # Define the taxonomic ID you want to fetch
    # tax_id = "9606"  # Example ID for Apis mellifera (honey bee)

    # Define the base URL for the E-utilities API
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    # Define the parameters for the query
    params = {
        "db": "taxonomy",
        "id": tax_id,
        "retmode": "json"
    }

    # Make the request
    response = requests.get(base_url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the response in JSON format
        data = response.json()
        # print(data)
        return data
    else:
        print(f"Error: {response.status_code}")


def get_image_acquisition():
    '''
    import requests

    # Define the term ID
    term_id = "FBbi_00000251"

    # Define the base URL for the BioStudies API
    base_url = "https://www.ebi.ac.uk/biostudies/api/term/"
    base_url = "http://purl.obolibrary.org/obo/"

    # Make the request
    response = requests.get(f"{base_url}{term_id}")

    # Check if the request was successful
    if response.status_code == 200:
        # Print the response in JSON format
        data = response.json()
        print(data)
    else:
        print(f"Error: {response.status_code}")
     '''
    import requests

    # Define the term ID
    term_id = "obo:FBbi_00000251"

    # Define the base URL for the VFB API
    base_url = "https://virtualflybrain.org/api/terms/"

    # Make the request
    response = requests.get(f"{base_url}{term_id}")

    # Check if the request was successful
    if response.status_code == 200:
        # Print the response in JSON format
        data = response.json()
        print(data)
    else:
        print(f"Error: {response.status_code}")


count = 0


def list_files_pathlib(p, files_list):
    global count
    count += 1
    ignore_list = [".git", ".venv"]
    from pathlib import Path
    for entry in p.iterdir():
        print("processing: %s , %s " % (count, entry))
        if entry.is_file():
            if entry.name == "ro-crate-metadata.json":
                # print(entry)
                files_list["json"].append(str(entry))
            else:
                if ".csv" in entry.name:
                    files_list["csv"].append(str(entry))
        elif entry.is_dir():
            if entry.name in ignore_list:
                continue
            list_files_pathlib(Path(entry), files_list)


def read_files(ome_path):
    from pathlib import Path
    p = Path(ome_path)
    for child in p.iterdir():
        print(child)

def get_the_actual_data(part_to_remove):
    json_list = []
    csv_list = []

    with open("json.csv", "r") as text_file:
        json_list_ = text_file.readlines()

    with open("csv.csv", "r") as text_file:
        csv_list_ = text_file.readlines()

    for line_ in csv_list_:
        line__ = line_.replace(part_to_remove, "")
        lst = line__.split("/")
        csv_list.append(lst)

    for line_ in json_list_:
        line__ = line_.replace(part_to_remove, "")
        lst = line__.split("/")
        json_list.append(lst)

    print(len(csv_list), csv_list[0])
    print(len(json_list), json_list[0])
    co = 0
    for ll in csv_list:
        print("checking: ", ll[0])
        for lst in json_list:
            # print ("hi", csv_list[0])
            if ll[0] in lst:
                co += 1
                # print (lst)
    print(co)


def copy_csv_files():
    import shutil
    # shutil.copyfile('/path/to/file', '/path/to/new/file')
    target = "/mnt/d/projects/forks/ome2024-ngff-challenge-metadata/utils/csvs"
    with open("csv.csv", "r") as text_file:
        csv_list_ = text_file.readlines()
    for file_ in csv_list_:
        file_ = file_.replace("\n", "")
        lst = file_.split("/")
        print(lst[-1])
        shutil.copyfile(file_, target + "/" + lst[-1])


def get_files():
    import datetime
    print(datetime.datetime.now())
    from pathlib import Path
    files_list = {"json": [], "csv": []}
    p = Path('/mnt/d/projects/forks/ome2024-ngff-challenge-metadata')
    list_files_pathlib(p, files_list)
    print(len(files_list["json"]))
    print(len(files_list["csv"]))
    json_string = '\n'.join(files_list["json"])
    csv_string = '\n'.join(files_list["csv"])
    with open("json.csv", "w") as text_file:
        text_file.write(json_string)

    with open("csv.csv", "w") as text_file:
        text_file.write(csv_string)

    print(datetime.datetime.now())


def extract_meta_data(part_to_remove):
    meta_data = []

    with open("json.csv", "r") as text_file:
        json_list_ = text_file.readlines()

    # copy_csv_files()
    # get_the_actual_data(part_to_remove)
    # get_image_acquisition()
    imge_count = 0
    error_list = []
    for crate_path_ in json_list_:
        imge_count += 1
        crate_path = crate_path_.replace("ro-crate-metadata.json", "").strip()
        print("%s: Checking : %s" % (imge_count, crate_path))
        if not os.path.isdir(crate_path):
            print("Error: ", crate_path, ": is not found")
            error_list.append(crate_path)
            continue
        propreties = read_metadata_file(crate_path)
        if 'datePublished' in propreties: del propreties['datePublished']

        if len(propreties) > 0 and "organism" in propreties:
            org_to_be_extracted = propreties["organism"]
            if org_to_be_extracted in tax_id_org:
                print("Extracted before, use the data and save time!")
                if tax_id_org[org_to_be_extracted]:
                    propreties["organism"] = tax_id_org[org_to_be_extracted]
            else:
                tax_id = get_entity(org_to_be_extracted)
                data = get_organism(tax_id)
                if data and data.get("result") and data.get("result").get("%s" % tax_id):
                    propreties["organism"] = data.get("result").get("%s" % tax_id).get("scientificname")
                    tax_id_org[org_to_be_extracted] = data.get("result").get("%s" % tax_id).get("scientificname")
                else:
                    tax_id_org[org_to_be_extracted] = None
        # print ("=======================")
        image_key = crate_path.replace(part_to_remove, "")
        propreties["ngff_id"] = image_key
        meta_data.append(propreties)

    df_metadat = pd.DataFrame(meta_data)
    df_metadat.to_csv("metadata.csv", index=False)
    with open("create_path_errors.csv", 'w', newline='') as output_file:
        output_file.write('\n'.join(error_list))


def uuid_to_int():
    # return uuid.UUID(uuid_string).int
    return random.randint(0, 1000000)


def get_data_source_data(resources_data, zar_file):
    for data_source, items in resources_data.items():

        if zar_file in items["metadata"]:
            for ff in items["metadata"]:
                if ff.lower() == zar_file.lower():
                    return data_source, items["metadata"][zar_file]

    return None, None


def get_metadata_row(metadata_df, target_zar_file):
    row_ = None
    for index, row in metadata_df.iterrows():
        if row["ngff_id"].endswith("/"):
            zar_file = get_file_name(row["ngff_id"][:-1], None)
        else:
            zar_file = get_file_name(row["ngff_id"], None)

        if target_zar_file.lower() == zar_file.lower():
            return row
    # selected_rows = df[df['ngff_id'] == "KOMP_A33267_5.zarr"]

    return row_


def create_searchengine_scsv_files(resources_list):
    search_engine_data_ = {}
    search_engine_data = []
    search_engine_data_["idr"] = []
    search_engine_data_["jax"] = []
    search_engine_data_["NFDI4BIOIMAGE"] = []
    search_engine_data_["other"] = []
    data_sources = {"NFDI4BIOIMAGE": 1, "jax": 2, "idr": 3, "bia": 4, "Webknossos": 5, "UniversityofMuenster": 6,
                    "Crick": 7}
    prjects = [
        {"id": 1, "name": "NFDI4BIOIMAGE", "description": "ome2024-ngff-challenge from NFDI4BIOIMAGE",
         "mapvalue_name": "", "mapvalue_value": "", "index": 0},
        {"id": 2, "name": "jax", "description": "ome2024-ngff-challenge data from Jax lab",
         "mapvalue_name": "", "mapvalue_value": "", "index": 0},
        {"id": 3, "name": "idr", "description": "ome2024-ngff-challenge data from idr", "mapvalue_name": "",
         "mapvalue_value": "", "index": 0},
        {"id": 4, "name": "bia", "description": "ome2024-ngff-challenge from bia", "mapvalue_name": "",
         "mapvalue_value": "", "index": 0},
        {"id": 5, "name": "Webknossos", "description": "ome2024-ngff-challenge from Webknossos",
         "mapvalue_name": "",
         "mapvalue_value": "", "index": 0},
        {"id": 6, "name": "UniversityofMuenster", "description": "ome2024-ngff-challenge from UniversityofMuenster",
         "mapvalue_name": "",
         "mapvalue_value": "", "index": 0},
        {"id": 7, "name": "Crick", "description": "ome2024-ngff-challenge from Crick", "mapvalue_name": "",
         "mapvalue_value": "", "index": 0},
    ]

    idr = 0
    NFDI4BIOIMAGE = 0
    jax = 0
    other = 0
    cols = ["license", "organism", "image_acquisition", "ngff_id", "description", "name"]
    print("Loading the metadata .....")
    metadata_df = pd.read_csv('metadata.csv')
    ccc = 0
    NoneType = type(None)
    for data_source, metadata in resources_list.items():
        print(data_source)
        # print (metadata)
        for file_, file_data in metadata["metadata"].items():
            ccc += 1
            print(ccc, ": processing data_source, file:  %s" % file_)
            data_row = {}
            data_row["id"] = uuid_to_int()
            data_row["project_name"] = data_source
            data_row["project_id"] = data_sources[data_source]
            data_row["name"] = file_
            row = get_metadata_row(metadata_df, file_)
            # print (row, type(row))
            if not isinstance(row, NoneType):
                # if type(row) is not None:
                if row["name"] and type(row["name"]) is not str:
                    # if math.isnan(row["name"]):
                    parts = row["ngff_id"].strip().split("/")
                    data_row["name"] = escape_string(parts[len(parts) - 2])
                    print(row["ngff_id"])
                    print(data_row["name"])
                    parts = row["ngff_id"].strip().split("/")
                    # sys.exit()
                else:
                    data_row["name"] = row["name"]
                data_row["description"] = escape_string(row["description"])
                for col in cols:
                    if row[col] and type(row[col]) is not str:
                        continue
                    data_row_ = copy.deepcopy(data_row)
                    # search_engine_data[data_source].append(data_row_)
                    search_engine_data.append(data_row_)
                    if col == "name":
                        data_row_["mapvalue_name"] = "image_name"
                    else:
                        data_row_["mapvalue_name"] = col
                    data_row_["mapvalue_value"] = row[col]
                    data_row_["mapvalue_index"] = 0

            for k_name, k_value in file_data.items():
                data_row__ = copy.deepcopy(data_row)
                search_engine_data.append(data_row__)
                data_row__["mapvalue_name"] = k_name
                data_row__["mapvalue_value"] = escape_string(k_value)
                data_row__["mapvalue_index"] = 0

    print(ccc)

    df_metadat = pd.DataFrame(search_engine_data)
    df_metadat.to_csv("images_ngff_metadata.csv", index=False)
    print("IDR: ", idr)
    print("Jax: ", jax)
    print("NFDI4BIOIMAGE:", NFDI4BIOIMAGE)
    print("Other: ", other)
    print("total:", (idr + jax + NFDI4BIOIMAGE + other))
    df_project_metadat = pd.DataFrame(prjects)
    df_project_metadat.to_csv("projects_ngff__metadata.csv", index=False)


def get_file_name(url_, base_folder="/mnt/d/projects/forks/ome2024-ngff-challenge-metadata/utils/csvs"):
    if url_.endswith("/"):
        url_ = url_[:len(url_) - 1]
    head, tail = os.path.split(url_)
    if base_folder:
        f_path = os.path.join(base_folder, tail)
        return f_path
    return tail


def get_sub_files_list(main_file):
    df = pd.read_csv(main_file)
    files_list = []
    for index, row in df.iterrows():
        files_list.append(get_file_name(row["url"]))
    print(files_list)
    return files_list


def get_files_contents():
    pass


def read_csv_files():
    from pathlib import Path
    resources_list = {}
    # contains sub files
    idr = "https://raw.githubusercontent.com/will-moore/ome2024-ngff-challenge/samples_viewer/samples/idr_samples.csv"
    idr = get_file_name(idr)
    print(idr)
    resources_list["idr"] = {}
    resources_list["idr"]["metadata"] = {}
    resources_list["idr"]["files"] = get_sub_files_list(idr)
    NFDI4BIOIMAGE = "https://radosgw.public.os.wwu.de/n4bi-wp1/challenge/n4bi.csv"
    NFDI4BIOIMAGE = get_file_name(NFDI4BIOIMAGE)
    resources_list["NFDI4BIOIMAGE"] = {}
    resources_list["NFDI4BIOIMAGE"]["metadata"] = {}
    resources_list["NFDI4BIOIMAGE"]["files"] = get_sub_files_list(NFDI4BIOIMAGE)
    # read the data directley
    jax_1 = "https://raw.githubusercontent.com/TheJacksonLaboratory/jax-ngff-challenge-2024/refs/heads/main/KOMP_adult_lacZ.csv"
    jax_1 == get_file_name(jax_1)
    jax_2 = "https://raw.githubusercontent.com/TheJacksonLaboratory/jax-ngff-challenge-2024/refs/heads/main/KOMP_histopathology.csv"
    jax_2 = get_file_name(jax_2)
    resources_list["jax"] = {}
    resources_list["jax"]["metadata"] = {}
    resources_list["jax"]["files"] = [jax_1, jax_2]
    bia = "https://raw.githubusercontent.com/will-moore/ome2024-ngff-challenge/samples_viewer/samples/ebi-ngff-challenge-samples.csv"
    bia = get_file_name(bia)
    resources_list["bia"] = {}
    resources_list["bia"]["metadata"] = {}
    resources_list["bia"]["files"] = [bia]
    Webknossos = "https://raw.githubusercontent.com/will-moore/ome2024-ngff-challenge/samples_viewer/samples/webknossos_samples.csv"
    Webknossos = get_file_name(Webknossos)
    resources_list["Webknossos"] = {}
    resources_list["Webknossos"]["metadata"] = {}
    resources_list["Webknossos"]["files"] = [Webknossos]
    UniversityofMuenster = "https://raw.githubusercontent.com/JensWendt/ome2024-ngff-challenge/refs/heads/main/samples/uni_muenster_samples.csv"
    UniversityofMuenster = get_file_name(UniversityofMuenster)
    print("???", UniversityofMuenster)
    resources_list["UniversityofMuenster"] = {}
    resources_list["UniversityofMuenster"]["metadata"] = {}
    resources_list["UniversityofMuenster"]["files"] = [UniversityofMuenster]
    Crick = "https://radosgw.public.os.wwu.de/n4bi-wp1/challenge/crick.csv"
    Crick = get_file_name(Crick)
    resources_list["Crick"] = {}
    resources_list["Crick"]["metadata"] = {}
    resources_list["Crick"]["files"] = [Crick]
    files_header = ["url", "written", "written_human_readable", "origin"]
    counter = 0
    for data_source, data in resources_list.items():
        print("processing ..", data_source)
        print(data_source)
        print(len(data["files"]))
        for file_ in data["files"]:
            print(file_)
            print("## Processing file: %s" % file_)
            if file_.startswith("http"):
                file_ = get_file_name(file_)
            if Path(file_).is_file():
                df = pd.read_csv(file_)
                for index, row in df.iterrows():
                    counter += 1
                    if data_source != "Webknossos":
                        name_ = get_file_name(row["url"], None)
                    else:
                        name_ = get_file_name(row["origin"], None)

                    if not name_:
                        print("I AM NULL", name_, row["url"])
                        sys.exit()
                    data_row = {}
                    resources_list[data_source]["metadata"][name_] = data_row
                    for header in files_header:
                        if header in row:
                            data_row[header] = row[header]
                        else:
                            data_row[header] = ""
            else:
                print(data_source)
                print("Data files####", data["files"])
                print(file_, " is not found.....>>>>>")
                sys.exit()

    print("Counter:", counter)
    print(resources_list["UniversityofMuenster"])
    print(resources_list["Webknossos"])
    return resources_list


if __name__ == "__main__":
    extract_meta_data("path/to/ome2024-ngff-challenge-metadata/")
    resources_list = read_csv_files()
    create_searchengine_scsv_files(resources_list)

