from . import resources
from flask import request, jsonify
import json
from omero_search_engine.api.v1.resources.utils import (
    search_resource_annotation,
    build_error_message,
)
from omero_search_engine.api.v1.resources.resource_analyser import (
    search_value_for_resource,
    get_resource_attributes,
    get_resource_attribute_values,
    get_resource_names,
    get_key_values_return_contents,
)
from omero_search_engine.api.v1.resources.utils import get_resource_annotation_table
from omero_search_engine.api.v1.resources.query_handler import (
    determine_search_results_,
    simple_search,
    query_validator,
)


@resources.route("/", methods=["GET"])
def index():
    return "OMERO search engine (API V1)"


@resources.route("/<resource_table>/searchannotation_page/", methods=["POST"])
def search_resource_page(resource_table):
    """
    used to get the next results page
    """
    if not (get_resource_annotation_table):
        return jsonify(
            build_error_message(
                "No data for table {table}".format(table=resource_table)
            )
        )
    data = request.data
    if not data:
        return jsonify(
            build_error_message(
                "Error: {error}".format(error="No query data is provided ")
            )
        )
    try:
        data = json.loads(data)
    except Exception:
        return jsonify(
            build_error_message(
                "{error}".format(error="No proper query data is provided ")
            )
        )

    if "query" in data:
        query = data["query"]
        validation_results = query_validator(query)
        if validation_results == "OK":
            page = data.get("page")
            bookmark = data.get("bookmark")
            raw_elasticsearch_query = data.get("raw_elasticsearch_query")
            return_containers = data.get("return_containers")
            if return_containers:
                return_containers = json.loads(return_containers.lower())

            resource_list = search_resource_annotation(
                resource_table,
                query,
                raw_elasticsearch_query=raw_elasticsearch_query,
                page=page,
                bookmark=bookmark,
                return_containers=return_containers,
            )
            return jsonify(resource_list)
        else:
            return jsonify(build_error_message(validation_results))

    else:
        return jsonify(
            build_error_message(
                "Error: No query field is provided. please specify an id."
            )
        )


@resources.route("/<resource_table>/searchannotation/", methods=["POST"])
def search_resource(resource_table):
    """
    file: swagger_docs/searchannotation.yml
    """
    """
    API end point to search the annotation (key/value pair) for a resource 
    (resource table, e.g. image, project, study, ..)
    the request data contains a dict (query) which contains the query details.
    this version (1) uses Elastic search
    an example of a query dict is:
       q_data={"query":{'query_details':{"and_filters":and_filters,"or_filters":or_filters}}}  # noqa
       each of and_filtersand or_filters is a list of dict
       which contains the search conditions, 
       an example of and_filters is:
       and_filters=[{"Organism" : "Homo sapiens", "operator": "equals"},{"Gene Symbol": "NCAPD2", "operator": "equals"},{ "Cell Cycle Phase" :"anaphase", "operator": "equals"}] # noqa
       and_filters means that the results have to satisfy the conditions
       not_filters means that the results do not have to satisfy the conditions
       or_filters means that the results should satisfy at least one condition inside the filters
    """

    if not (get_resource_annotation_table):
        return jsonify(
            build_error_message(
                "NO data for table {table}".format(table=resource_table)
            )
        )
    data = request.data
    if not data:
        return jsonify(
            build_error_message("{error}".format(error="No query data is provided "))
        )
    try:
        data = json.loads(data)
    except Exception:
        return jsonify(
            build_error_message(
                "{error}".format(error="No proper query data is provided.")
            )
        )

    if "query" in data:
        query = data["query"]
    elif "query_details" in data:
        query = data
    else:
        return jsonify(
            build_error_message(
                "Error: No query field is provided. please specify an id."
            )
        )

    # check if the app configuration will use ASYNCHRONOUS SEARCH or not.
    validation_results = query_validator(query)
    if validation_results == "OK":
        return_containers = request.args.get("return_containers")
        if return_containers:
            return_containers = json.loads(return_containers.lower())

        resource_list = search_resource_annotation(
            resource_table, query, return_containers=return_containers
        )
        return jsonify(resource_list)
    else:
        return jsonify(build_error_message(validation_results))


@resources.route("/<resource_table>/searchvalues/", methods=["GET"])
def get_values_using_value(resource_table):
    """
    file: swagger_docs/search_for_any_value.yml
    """
    value = request.args.get("value")
    if not value:
        return jsonify(
            build_error_message("Error: {error}".format(error="No value is provided "))
        )
    # print (value, resource_table)
    return jsonify(search_value_for_resource(resource_table, value))


@resources.route("/<resource_table>/searchvaluesusingkey/", methods=["GET"])
def search_values_for_a_key(resource_table):
    """
    file: swagger_docs/searchvaluesusingkey.yml
    """
    key = request.args.get("key")
    if not key:
        return jsonify(build_error_message("No key is provided "))

    # csv is a flag true of false,
    # default is false
    # if it sets to true, a CSV file content will be sent instead of dict
    csv = request.args.get("csv")
    if csv:
        try:
            csv = json.loads(csv.lower())
        except Exception:
            csv = False

    return get_key_values_return_contents(key, resource_table, csv)


# getannotationkeys==> keys
@resources.route("/<resource_table>/keys/", methods=["GET"])
def get_resource_keys(resource_table):
    """
    file: swagger_docs/getannotationkeys.yml
    """

    """
     return the keys for a resource or all the resources
    """
    mode = request.args.get("mode")
    resource_keys = get_resource_attributes(resource_table, mode=mode)
    return jsonify(resource_keys)


@resources.route("/<resource_table>/getannotationvalueskey/", methods=["GET"])
def get_resource_key_value(resource_table):
    """
    file= swagger_docs/getannotationvalueskey.yml
    """

    """
    get the values for a key for a specific resource
    """
    key = request.args.get("key")
    if not key:
        return jsonify(build_error_message("No key is provided"))
    if key != "Name (IDR number)":
        return jsonify(get_resource_attribute_values(resource_table, key))
    else:
        return jsonify(get_resource_names("all"))


# getresourcenames==>names
@resources.route("/<resource_table>/names/", methods=["GET"])
def get_resource_names_(resource_table):
    """
    file: swagger_docs/getresourcenames.yml
    """
    """
    Query the available attributes for a specific resource
    """
    if not (get_resource_annotation_table(resource_table)):
        return "NO data for table {table}".format(table=resource_table)

    names = get_resource_names(resource_table)
    return jsonify(names)


@resources.route("/submitquery_returnstudies/", methods=["POST"])
def submit_query_return_containers():
    """
    file: swagger_docs/submitquery_returncontainers.yml
    """
    try:
        query = json.loads(request.data)
    except Exception:
        query = None
    if not query:
        return jsonify(build_error_message("No query is provided"))
    return_columns = request.args.get("return_columns")
    if return_columns:
        try:
            return_columns = json.loads(return_columns.lower())
        except Exception:
            return_columns = False
    validation_results = query_validator(query)
    if validation_results == "OK":
        return jsonify(
            determine_search_results_(query, return_columns, return_containers=True)
        )
    else:
        return jsonify(build_error_message(validation_results))


@resources.route("/submitquery/", methods=["POST"])
def submit_query():
    """
    file: swagger_docs/submitquery.yml
    """
    try:
        query = json.loads(request.data)
    except Exception:
        query = None
    if not query:
        return jsonify(build_error_message("No query is provided"))
    return_columns = request.args.get("return_columns")
    if return_columns:
        try:
            return_columns = json.loads(return_columns.lower())
        except Exception:
            return_columns = False
    validation_results = query_validator(query)
    if validation_results == "OK":
        return jsonify(determine_search_results_(query, return_columns))
    else:
        return jsonify(build_error_message(validation_results))


@resources.route("/<resource_table>/search/", methods=["GET"])
def search(resource_table):
    """
    file: swagger_docs/search.yml
    """
    key = request.args.get("key")
    value = request.args.get("value")
    study = request.args.get("study")
    case_sensitive = request.args.get("case_sensitive")
    operator = request.args.get("operator")
    bookmark = request.args.get("bookmark")
    return_containers = request.args.get("return_containers")
    if return_containers:
        return_containers = json.loads(return_containers.lower())
    results = simple_search(
        key,
        value,
        operator,
        case_sensitive,
        bookmark,
        resource_table,
        study,
        return_containers,
    )
    return jsonify(results)
