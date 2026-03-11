User Guide
==========

Table of Contents
-----------------

- `Introduction <#introduction>`_
- `Overview of IDR Searcher <#Overview-of-IDR-Searcher>`_
    - `API-based search <#API-based-search>`_
    - `Exporting results <Exporting-results>`_
    - `Supported data formats <Supported-data-formats>`_
- `Querying Data <#Querying-Data>`_
    - `Query request structure <#Query-request-structure>`_
    - `Search Response Structure <#Search-Response-Structure>`_
    - `Filtering Results <#Filtering-Results>`_
- `Asynchronous Search <#Asynchronous-Search>`_
- `Exporting Containers data files <Exporting-Containers-data-files>`_
- `Submitting Queries for Metadata <#Submitting-Queries-for-Metadata>`_
- `Common Workflows <#Common-Workflows>`_

Introduction
------------
This Guide will explain queries structure, use filters, and interpret API responses.
The IDR searcher is deployed on https://idr.openmicroscopy.org/searchengine/api/v1/resources/ , as the public user has API access, and the IDR indexed data is available for search.

Overview of IDR Searcher
------------------------

IDR Searcher is an API-only backend service. All interactions with the system are performed over HTTP using standard REST methods. Requests and responses are exchanged in JSON format.

The API supports the following request methods:

GET — Used for simple queries where parameters are passed through the URL.
POST — Used for more complex queries that require a structured JSON request body.

API-based search
~~~~~~~~~~~~~~~~

**Querying indexed data**

The user can query the indexed data or the metadata.

The user can send a request to query the data using filters, including single or multiple conditions. For example, they can request items where:
- attribute1 = value1
- attribute1 = value1 AND attribute2 = value2
- attribute1 = value1 OR attribute2 = value2
It’s also possible to combine multiple AND and OR conditions in the same query

For metadata, they can retrieve information such as the number of values for a specific key, the count of each value, and the total number of keys available for a given resource.
They can also view how many projects have been indexed, how many items each project contains, and the metadata available for each project.

Exporting results
~~~~~~~~~~~~~~~~~

The returned results are provided as a JSON object, which includes several sections such as the query details, the results themselves, and the total number of results.
For large result sets, the user can use pagination to retrieve the data in smaller chunks, or they can run an asynchronous query to fetch all results in a single operation.

Supported data formats
~~~~~~~~~~~~~~~~~~~~~~

The default output is a JSON string, but users can also choose to retrieve the data in CSV or Parquet format. These alternative formats are available when using an asynchronous query.

Querying Data
-------------
This section explains how users search the indexed data.

**The search parameters include**

 - ``value`` is the required attribute value
 - ``data_source`` is used to filter the data for a specific data resource/s.
 - ``operator``, the supported values are  equals, not_equals, contains, not_contains, in, not_in
 - ``Key`` or ``name`` is the attribute name, i.e. Organism, Cell line, Gene symbol, etc.
 - ``resource``, the available values are image, project, screen, well, plate
 - ``case_sensitive``, false or true, default is false
 - ``bookmark`` is used to the call the next page if number of results is bigger than 1000, it returns with each result page.

If data source is specified in the request, it will be used. Otherwise, the default data source will be used. If no default data source is configured, results from all available data sources will be returned.

Query request structure
~~~~~~~~~~~~~~~~~~~~~~~
**Basic search query**

GET request which is used for simple search (no ``and`` or ``or`` filters, i.e. single filter), the search parameters are included in the url
Example, the user wants to search for the images which has the ``organism part`` is ``brain`` within the ``idr`` data resource,
for this particular search the attributes will be
 - key = organism part
 - value = brain
 - operator= equals
 - data_source=idr
 - organism part = image

This should be included in the url for the GET ``search`` request

https://idr.openmicroscopy.org/searchengine/api/v1/resources/image/search/?key=organism%20part&value=brain&operator=equals&data_source=idr

This can be achieved also, using POST request, and the query should be a JSON.

The query JSON  contains two parts:
* ``query_details`` which has two parts:
  - ``and_filters``, a list of filters (i.e. dicts), the filter takes this form:
    ``{"name": {keyword}, "value": {value}, "operator": {operator}, "resource": {resource}}``

     ``keyword``: the name of the attribute to search for

     ``value``: the value for which the attribute should be searched; the search is dependant on the operator

     ``operator``: operator criteria which is used to search the keyword value, it can be either:
        ``equals, not_equals, contains (like), not_contains (not like), lt (<), gt (>), lte (<=), and gte (>=)``

    ``resource``: such as image, project, screen, or container in case the user is not sure if the study is project or screen

  - ``or_filters``, a list of filters (i.e. dicts), the filter takes the same form illustrated above

* ``main_attributes`` this is an optional part which allows the user to search using one or more of:
   ``project _id, dataset_id, owner_id, group_id, owner_id,`` etc.

Request details::

    POST https://idr.openmicroscopy.org/searchengine/api/v1/resources/submitquery/
    Content-Type: application/json
JSON details

.. code-block:: json

    {
       "query_details":{
          "and_filters":[
             {
                "name":"organism part",
                "value":"brain",
                "operator":"equals",
                "resource":"image"
             }
          ],
          "or_filters":[],
          "case_sensitive":false
       }
    }

Users can try out the examples above directly in the API IDR Searcher Swagger documentation.
https://idr.openmicroscopy.org/searchengine/apidocs/#/Mixed%20Complex%20query/post_searchengine__api_v1_resources_submitquery_

Search Response Structure
~~~~~~~~~~~~~~~~~~~~~~~~~

The search response is a dictionary containing the results and associated metadata fields (e.g., size, total_pages).

**Result structure**

`` query_details``: The query processed by the searchenginee
`` resource``: is resource which is searched
`` results``:

  - ``bookmark``:	 Use this token to fetch the next batch of results when the total results exceed the batch size
  - ``results``:	 An array of result objects included in the current response based searchengine data schema (based on Elasticsearch template)
  - ``size``:	     The total number of result objects
  - ``total_pages``: Total number of pages needed to retrieve all results.
``server_query_time``:	The server processing time for the query

Filtering Results
~~~~~~~~~~~~~~~~~
As mentioned, the user can use more than condition in one query, for example
the user needs to search for unhealthy human female breast images, then they should use 4 filters,

1. Organism = Homo sapiens
2. Sex = Female
3. Organism Part = Breast
4. Pathology != Normal tissue, NOS

All of these filters should be added to ``and_filters`` list to search for images that satisfy all the conditions.
The ``and_filters`` list should look like this:

.. code-block:: json

     [
       {
          "name":"Organism",
          "value":"Homo sapiens",
          "operator":"equals",
          "resource":"image"
       },
       {
          "name":"Organism Part",
          "value":"Breast",
          "operator":"equals",
          "resource":"image"
       },
       {
          "name":"Sex",
          "value":"Female",
          "operator":"equals",
          "resource":"image"
       },
       {
          "name":"Pathology",
          "value":"Normal tissue, NOS",
          "operator":"not_equals",
          "resource":"image"
       }
    ]

THe query needs to have such format::

    {"query_details": {"and_filters": and_filters_list}}


The query sent to the IDR Searcher should look like this

.. code-block:: json

    {
       "query_details":{
          "and_filters":[
             {
                "name":"Organism",
                "value":"Homo sapiens",
                "operator":"equals",
                "resource":"image"
             },
             {
                "name":"Organism Part",
                "value":"Breast",
                "operator":"equals",
                "resource":"image"
             },
             {
                "name":"Sex",
                "value":"Female",
                "operator":"equals",
                "resource":"image"
             },
             {
                "name":"Pathology",
                "value":"Normal tissue, NOS",
                "operator":"not_equals",
                "resource":"image"
             }
          ]
       }
    }

The response includes the first batch of results. The default batch size is 1,000 images (configurable by an administrator up to 10,000).

It also includes the following informative sections::


 "bookmark": [
      3533681
    ],
 "size": 253387,
 "total_pages": 254


The next page of results can be retrieved by adding the returned ``bookmark`` value to your query as follows

.. code-block:: json

    {
       "query_details":{
          "and_filters":[
             {
                "name":"Organism",
                "value":"Homo sapiens",
                "operator":"equals",
                "resource":"image"
             },
             {
                "name":"Organism Part",
                "value":"Breast",
                "operator":"equals",
                "resource":"image"
             },
             {
                "name":"Sex",
                "value":"Female",
                "operator":"equals",
                "resource":"image"
             },
             {
                "name":"Pathology",
                "value":"Normal tissue, NOS",
                "operator":"not_equals",
                "resource":"image"
             }
          ]
       },
       "bookmark":[
          3533681
       ]
    }

Each subsequent result page includes a ``bookmark`` that can be used to request the next page.

Asynchronous Search
-------------------

This section describes how to run asynchronous queries and retrieve large result sets in a single request.

Asynchronous search allows users to submit a query and retrieve results without waiting for the query to complete immediately.
Instead of blocking until all results are ready, the IDR Searcher processes the query in the background, returning results once the entire query is complete.
Ideal for handling large query results without requiring multiple requests.

The query format remains the same, but users must submit their queries using the following endpoint::

    async_submitquery/

Example:

The user wants to search all the images which have

 - Sex=Female
 - Organism=Homo sapiens
 - Organism part=Kidney

This is the request::

    POST https://idr.openmicroscopy.org/searchengine//api/v1/resources/async_submitquery/
    Content-Type: application/json

.. code-block:: json

    {
       "query_details":{
          "and_filters":[
             {
                "name":"Sex",
                "value":"Female",
                "operator":"equals",
                "resource":"image"
             },
             {
                "name":"Organism",
                "value":"Homo sapiens",
                "operator":"equals",
                "resource":"image"
             },
             {
                "name":"Organism part",
                "value":"kidney",
                "operator":"equals",
                "resource":"image"
             }
          ],
          "or_filters":[

          ]
       }
    }

The response will be a dict which contains the query id::

    {
      "query_id": "360f8047-97ed-4e55-9604-8a0892a3a56b"
    }

To check the status of the query, the user should use the following GET request.

https://idr.openmicroscopy.org/searchengine//api/v1/resources/check_query_job/?query_id=ce4256a9-f230-4be5-bbab-485430777b29

The status can be PENDING, SUCCESS, or FAILED. When the status is SUCCESS.

When the job status is ``SUCCESS``, the response includes the status, the original query, and the total number of results

.. code-block:: json

    {
      "Result": {
        "csv": "360f8047-97ed-4e55-9604-8a0892a3a56b.csv",
        "data_source": "idr",
        "parquet": "360f8047-97ed-4e55-9604-8a0892a3a56b.parquet",
        "query": {
          "and_filters": [
            {
              "name": "Sex",
              "operator": "equals",
              "resource": "image",
              "value": "Female"
            },
            {
              "name": "Organism",
              "operator": "equals",
              "resource": "image",
              "value": "Homo sapiens"
            },
            {
              "name": "Organism part",
              "operator": "equals",
              "resource": "image",
              "value": "kidney"
            }
          ],
          "or_filters": []
        },
        "total_results": 146440
      },
      "status": "SUCCESS"
    }{
      "Result": {
        "csv": "360f8047-97ed-4e55-9604-8a0892a3a56b.csv",
        "data_source": "idr",
        "parquet": "360f8047-97ed-4e55-9604-8a0892a3a56b.parquet",
        "query": {
          "and_filters": [
            {
              "name": "Sex",
              "operator": "equals",
              "resource": "image",
              "value": "Female"
            },
            {
              "name": "Organism",
              "operator": "equals",
              "resource": "image",
              "value": "Homo sapiens"
            },
            {
              "name": "Organism part",
              "operator": "equals",
              "resource": "image",
              "value": "kidney"
            }
          ],
          "or_filters": []
        },
        "total_results": 146440
      },
      "status": "SUCCESS"
    }

The results are ready for download via the following GET request using the ``query_id`` and the ``file-type`` (``csv`` or ``parquet``) parameter. This is the link for  the previous query:

https://idr.openmicroscopy.org/searchengine//api/v1/resources/return_query_results/?query_id=360f8047-97ed-4e55-9604-8a0892a3a56b&file_type=csv

Exporting Containers data files
-------------------------------

Container data can be exported in CSV or Parquet format for further analysis or exploration (for example, using BFF).

The export endpoint is ``container_bff_data/``, and the following parameters are required:

    - the container name,
    - container type (``Project`` or ``Screen``),
    - file format (``CSV`` or ``Parquet``).

For example, to download the `CSV` file format for the PR container `idr0161-yayon-thymus/experimentA``, the user should use the following URL:

https://idr.openmicroscopy.org/searchengine//api/v1/resources/container_bff_data/?container_name=idr0161-yayon-thymus%2FexperimentA%20&container_type=project&file_type=csv

Submitting Queries for Metadata
-------------------------------

**Search for any value**

The user knows a value (or part of it) and wants to identify which keys contain this value, along with the number of items in each bucket.
Then, they can use this endpoint::

    searchvalues/

Example:

To get all image keys with the value  (or part of it) ``normal tissue``, the user submits the following query:

https://idr.openmicroscopy.org/searchengine//api/v1/resources/image/searchvalues/?value=normal%20tissue

The results are returned in the following JSON:

.. code-block:: json

    {
      "data": [
        {
          "Key": "Pathology",
          "Number of images": 1654117,
          "Value": "normal tissue, nos",
          "data_source": "idr"
        },
        {
          "Key": "Compound Description",
          "Number of images": 96,
          "Value": "radioprotective agent; selectively protects normal tissues from the damaging effects of anti-neoplastic radiation therapy",
          "data_source": "idr"
        }
      ],
      "total_number_of_all_buckets": 2,
      "total_number_of_buckets": 2,
      "total_number_of_image": 1654213
}


**Available values for a resource key**

his endpoint returns the available values for a specific key along with their numbers::

    searchvaluesusingkey/

For example, to see the values for the key ``Organism`` in images, the user can use this request:

https://idr.openmicroscopy.org/searchengine//api/v1/resources/project/searchvaluesusingkey/?key=Organism

**Containers and the number of images in each container*

This IDR Searcher endpoint returns the available containers and their image counts

https://idr.openmicroscopy.org/searchengine//api/v1/resources/container_images/

Common Workflows
-----------------
Provides practical examples.

Examples:

