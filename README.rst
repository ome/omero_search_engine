.. image:: https://github.com/ome/omero_search_engine/workflows/Build/badge.svg
   :target: https://github.com/ome/omero_search_engine/actions

.. image:: https://readthedocs.org/projects/omero-search-engine/badge/?version=latest
    :target: https://omero-search-engine.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

IDR Searcher
------------
IDR searcher is an Elasticsearch-based search engine developed for IDR (Image Data Resource) to index and analyse metadata stored as key–value pairs. It supports both simple lookups and complex queries across large datasets, with synchronous and asynchronous search capabilities.

The system connects directly to OMERO databases and also supports CSV data sources. All functionality is exposed through REST APIs (GET/POST) using JSON, enabling easy integration with web applications and backend services.

Although built for IDR, IDR searcher can be used as a backend search service for any application where data resides in an OMERO database or `supported CSV format <https://github.com/ome/omero_search_engine/tree/main/omero_search_engine/cache_functions/elasticsearch/csv_templates>`_  and is intended for public access.

Key Features
============

* Fast, scalable search capable of handling large datasets efficiently
* Flexible Search Operators:

  - Supports operators such as ``equals``, ``not equals``, and ``contains``.
* Complex Query Support:

  - Combine multiple conditions using ``AND`` and ``OR`` to answer advanced data queries.
* Search Across Multiple source types

  - Search images, projects, screens, plates, and datasets.
* Attribute-Agnostic Search:

  - Find records by value even if the attribute name is unknown.
* Multi data Resource Indexing:

  - Index data from database servers, database backups, and CSV files.
  - JSON support is currently under development.

* Resource Filtering:

  - Restrict search results to one or more selected data resources.
* Data Export:

  - Export indexed data or search results to JSON, CSV, or Parquet format
  - CSV and Parquet files are compatible with BFF (BioFile Finder Format). BFF is a tool for filtering, sorting and grouping tabular data) for advanced filtering and data exploration
* Asynchronous Search:

  - Fetch all matching results from large queries in one operation.
  - Ideal for handling large query results without multiple requests.

Multi-Data-Resource Support
===========================

SearcherEngine can index and query data from multiple resources, even if:

* They are in different formats
* Some require preprocessing (e.g., converting to CSV)

  - CSV files must follow the supported  structure to be indexed successfully.
  - CSV templates are provided to guide users in preparing files that match the required format.

**Example data resources:**


* IDR Data resource  ->  Database with sources metadata
* SSBD Data resource -> CSV files exported from a different public resource and converted to the supported CSV format before indexing.
* BIA Data resource -> Data requiring conversion to CSV before indexing
* Ome2024-ngff-challenge data resource -> Data requiring conversion to CSV before indexing

IDR Searcher reads data from each resource, processes it, and stores it in Elasticsearch.

Once indexed, you can:

* Run queries across all resources simultaneously
* Filter results by one or multiple data resources
* Export combined search results seamlessly
* Use asynchronous search to fetch all results in one operation, or standard pagination for incremental retrieval.
* Export & Analyse:
  - Search results can be exported to CSV and Parquet formats.
  - Exported files are compatible with BFF for downstream filtering and data exploration.

Quick start
-----------
For Users / Integrators
=======================

Wide range of example queries can be found in the `examples/ <https://github.com/khaledk2/ansible-role-omero-searchengine>`_  directory, ready to run or integrate.
Searcherengine does not provide a graphical user interface (GUI). All interactions are performed via REST APIs.
The IDR searcher is deployed at

    https://idr.openmicroscopy.org/searchengine/apidocs/

That page provides a full API reference and interactive testing, searching data from the IDR.

IDR searcher APIs can be used via:

* Integration into backend services for other applications
* Automation scripts
* Swagger (OpenAPI) UI for testing endpoints
* API clients (Postman, curl)

For Administrators
==================
Deployment and configuration are handled via dedicated Ansible role, i.e. `ansible-role-omero-searchengine <https://github.com/khaledk2/ansible-role-omero-searchengine>`_  , which includes `a sample deployment playbook <https://github.com/khaledk2/ansible-role-omero-searchengine?tab=readme-ov-file#example-playbook>`_ .
Deploy Using Ansible

1.	Review the sample playbook and adjust variables for your environment.
2.	Run the playbook (assuming the playbook name is deploy.ym)::

            ansible-playbook deploy.yml

Using IDR Searcher REST API
===========================
IDR Searcher is an API-only backend service. All interactions are via HTTP using standard REST methods. Data is exchanged in JSON format.

* GET — Used for simple queries via URL parameters
* POST — Used for more complex queries with JSON payloads

**GET Example (Simple Query):**

    https://idr.openmicroscopy.org/searchengine/api/v1/resources/image/search/?key=Gene%20Symbol&value=pdx1&data_source=idr

What it does:

* Finds all images where **Gene Symbol** = **pdx1** and **data resource** = **idr**
* Returns JSON results

**POST Example (Complex Query)**::

    POST https://idr.openmicroscopy.org/searchengine/api/v1/resources/submitquery/
    Content-Type: application/json


.. code-block:: json

    {
       "resource":"image",
       "query_details":{
          "and_filters":[
             {
                "name":"Organism",
                "value":"mus musculus",
                "operator":"equals",
                "resource":"image"
             },
             {
                "name":"Imaging Method",
                "value":"spim",
                "operator":"equals",
                "resource":"container"
             }
          ],
          "or_filters":[

          ],
          "case_sensitive":false
       }
    }

What it does:

* Searches across multiples resources (**image** and **container**)
* Filters records where **Organism** = **mus musculus** and **Imaging Method** = **spim**
* Returns JSON results ready for your script, web application or backend service

For more advanced examples, see the examples/ directory or Swagger UI.

Documentation
=============

IDR Searcher includes detailed documentation for different audiences:

* `User Guide <https://omero-search-engine.readthedocs.io/en/latest/user_guide/user_guide.html>`_

  - How to construct queries, use filters, and interpret API responses.
*  `Configuration Guide <https://omero-search-engine.readthedocs.io/en/latest/configuration/configuration_installation.html>`_

  - Guides you through configuring data sources, Elasticsearch, deployment options, indexing, and environment settings.
* `Developer Guide <https://omero-search-engine.readthedocs.io/en/latest/developer/developer.html>`_

  - Technical details for extending, maintaining, or contributing to the service.

**Not sure where to start?**

* Using the API: Read the User Guide.
* Deploying/configuring: Read the Configuration Guide.
* Extending or contributing: Read the Developer Guide.

Disclaimer
----------

* The IDR searcher currently is intended to be used with public data.

  - All indexed data is publicly accessible for search
* There is no authenticating or access permission in place yet.

  - We are working on the authentication and access permission problem solution for the private data.

License
-------

IDR searcher is released under the GPL v2.

Copyright
---------

2022-2026, The Open Microscopy Environment, Glencoe Software, Inc.
