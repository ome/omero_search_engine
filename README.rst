.. image:: https://github.com/ome/omero_search_engine/workflows/Build/badge.svg
   :target: https://github.com/ome/omero_search_engine/actions

OMERO Search Engine
--------------------

* OMERO search engine app is used to search metadata (``key-value`` pairs).

* The search engine query is a dict that has three parts:

  * The **first part** is ``and_filter``, it is a list. Each item in the list is a dict that has three keys:

    * name: attribute name (name in annotation_mapvalue table)
    * value: attribute value (value in annotation_mapvalue table)
    * operator: the operator, which is used to search the data, e.g. ``equals``, ``no_equals``, ``contains``, etc.
  * The **second part** of the query is ``or_filters``; it has alternatives to search the database; it answers a question like finding the images which can satisfy one or more of conditions inside a list. It is a list of dicts and has the same format as the dict inside the ``and_filter``.
  * The **third part** is the ``main_attribute``, it allows the user to search using one or more of ``project _id, dataset_id, group_id, owner_id, group_id, owner_id``, etc. It supports two operators, ``equals`` and ``not_equals``. Hence, it is possible to search one project instead of all the projects. Also it is possible to search the results which belong to a specific user or group.

* The search engine returns the results in a JSON which has the following keys:

  * ``notice``: reports a message to the sender which may include an error message.
  * ``Error``: specific error message
  * ``query_details``: The submitted query.
  * ``resource``: The resource, e.g. image
  * ``server_query_time``: The server query time in seconds
  * ``results``: the query results, which is a dict with the following keys:
  * ``size``: Total query results.
  * ``page``: page number, a page contains a maximum of 10000 records. If the results have more records, they will be transformed using more than one page.
  * ``bookmark``: Used to call the next page if the results exceed 10,000 records.
  * ``total_pages``: Total number of pages that contains the results.
  * ``results``: a list that contains the results. Each item inside the list is a dict. The dict key contains image id, name, and all the metadata (key/pair, i.e. "key_values") values for the image. Each item has other data such as the image owner Id,group Id, project Id and name etc.
* It is possible to query the search engine to get all the available resources (e.g. image) and their keys (names) using the following URL::

    127.0.0.01:5577/api/v1/resources/all/keys

* The user can get the available values for a specific key for a resourse, e.g. what are the available values for "Organism"::

    http://127.0.0.1:5577/api/v1/resources/image/getannotationvalueskey/?key=Organism

* The following python script sends a query to the search engine and gets the results:

.. code-block:: python

    import logging
    import requests
    import json
    from datetime import datetime
    # url to send the query
    image_ext = "/resources/image/searchannotation/"
    # url to get the next page for a query, bookmark is needed
    image_page_ext = "/resources/image/searchannotation_page/"
    # search engine url
    base_url = "http://127.0.0.1:5577/api/v1/"

    import sys

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)


    def query_the_search_ending(query, main_attributes):
        query_data = {"query": {'query_details': query,"main_attributes":main_attributes}}
        query_data_json = json.dumps(query_data)
        resp = requests.post(url="%s%s" % (base_url, image_ext), data=query_data_json)
        res = resp.text
        start = datetime.now()
        try:
            returned_results = json.loads(res)
        except:
            logging.info(res)
            return

        if not returned_results.get("results"):
            logging.info(returned_results)
            return

        elif len(returned_results["results"]) == 0:
            logging.info("Your query returns no results")
            return

        logging.info("Query results:")
        total_results = returned_results["results"]["size"]
        logging.info("Total no of result records %s" % total_results)
        logging.info("Server query time: %s seconds" % returned_results["server_query_time"])
        logging.info("Included results in the current page %s" % len(returned_results["results"]["results"]))

        recieved_results_data = []
        for res in returned_results["results"]["results"]:
            recieved_results_data.append(res)

        recieved_results = len(returned_results["results"]["results"])
        #set the bookmark to be used in the next the page if the number of pages is greater than 1
        bookmark = returned_results["results"]["bookmark"]
        #get the total number of pages
        total_pages = returned_results["results"]["total_pages"]
        page = 1
        logging.info("bookmark: %s, page: %s, received results: %s" % (
        bookmark, (str(page) + "/" + str(total_pages)), (str(recieved_results) + "/" + str(total_results))))
        while recieved_results < total_results:
            page += 1
            query_data = {"query": {'query_details': returned_results["query_details"]}, "bookmark": bookmark}
            query_data_json = json.dumps(query_data)
            resp = requests.post(url="%s%s" % (base_url, image_page_ext), data=query_data_json)
            res = resp.text
            try:
                returned_results = json.loads(res)
            except Exception as e:
                logging.info("%s, Error: %s"%(resp.text,e))
                return
            bookmark = returned_results["results"]["bookmark"]
            recieved_results = recieved_results + len(returned_results["results"]["results"])
            for res in returned_results["results"]["results"]:
                recieved_results_data.append(res)

            logging.info("bookmark: %s, page: %s, received results: %s" % (
            bookmark, (str(page) + "/" + str(total_pages)), (str(recieved_results) + "/" + str(total_results))))

        logging.info("Total received results: %s" % len(recieved_results_data))
        return recieved_results_data


    query_1 = {"and_filters": [{"name": "Organism", "value": "Homo sapiens", "operator": "equals"},
                               {"name": "Antibody Identifier", "value": "CAB034889", "operator": "equals"}],
               "or_filters": [[{"name": "Organism Part", "value": "Prostate", "operator": "equals"},
                              {"name": "Organism Part Identifier", "value": "T-77100", "operator": "equals"}]]}
    query_2 = {"and_filters": [{"name": "Organism", "value": "Mus musculus", 'operator': 'equals'}]}
    main_attributes=[]
    logging.info("Sending the first query:")
    results_1 = query_the_search_ending(query_1,main_attributes)
    logging.info("=========================")
    logging.info("Sending the second query:")
    results_2 = query_the_search_ending(query_2,main_attributes)
    #The above returns 130834 within 23 projects
    #[101, 301, 351, 352, 353, 405, 502, 504, 801, 851, 852, 853, 1151, 1158, 1159, 1201, 1202, 1451, 1605, 1606, 1701, 1902, 1903]
    #It is possible to get the results in one project, e.g. 101 by using the main_attributes filter
    main_attributes_2={ "and_main_attributes": [{
        "name":"project_id","value": 101, "operator":"equals"}]}
    results_3=query_the_search_ending(query_2,main_attributes_2)
    #It is possible to get the results and exculde one project, e.g. 101
    main_attributes_3={"and_main_attributes":[{"name":"project_id","value": 101, "operator":"not_equals"}]}
    results_4=query_the_search_ending(query_2,main_attributes_3)

* There is a `simple GUI <https://github.com/ome/omero_search_engine_client/tree/elastic_search>`_ to build the query and send it to the search engine

  * It is used to build the query
  * It will display the results when they are ready
* The app uses Elasticsearch

  * The method ``create_index`` inside `manage.py <manage.py>`_ creates a separate index for image, project, dataset, screen, plate, and well using two templates:

    * Image template (image_template) for image index. It is derived from some OMERO tables into a single Elasticsearch index (image, annoation_mapvalue, imageannotationlink, project, dataset, well, plate, and screen to generate a single index.
    * Non-image template (non_image_template) for other indices (project, dataset, well, plate, screen). It is derived from some OMERO tables depending on the resource; for example for the project it combines project, projectannotationlink and annotation_mapvalue.
    * Both of the templates are in `elasticsearch_templates.py <omero_search_engine/cache_functions/elasticsearch/elasticsearch_templates.py>`_
    * The data can be moved using SQL queries which generate the CSV files; the queries are in `sql_to_csv.py <omero_search_engine/cache_functions/elasticsearch/sql_to_csv.py>`_
    * The method ``add_resource_data_to_es_index`` inside `manage.py <manage.py>`_ reads the CSV files and inserts the data to the Elasticsearch index.
* The data can be transferred directly from the OMERO database to the Elasticsearch using the ``get_index_data_from_database`` method inside `manage.py <manage.py>`_:

  * It creates the elasticsearch indices for each resource
  * It queries the OMERO database after receiving the data, processes, and pushes it to the Elasticsearch indices.
  * This process takes a relatively long time depending on the hosting machine specs. The user can adjust how many rows can be processed per call to the OMERO database:
    * Set the no. of rows using the ``set_cache_rows_number`` method inside ``manage.py``, the following example will set the number to 1000::
        
        $ python manage.py set_cache_rows_number -s 10000
* The data can be also moved using SQL queries which generate the CSV files; the queries are in `sql_to_csv.py <omero_search_engine/cache_functions/elasticsearch/sql_to_csv.py>`_

For the configuration and installation instructions, please read the following document `configuration_installation <docs/configuration/configuration_installation.rst>`_

