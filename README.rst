.. image:: https://github.com/ome/omero_search_engine/workflows/Build/badge.svg
   :target: https://github.com/ome/omero_search_engine/actions

.. image:: https://readthedocs.org/projects/omero-search-engine/badge/?version=latest
    :target: https://omero-search-engine.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

IDR Searcher
--------

IDR Searcher is a powerful tool for searching and analysing metadata stored as key-value pairs, allowing both simple inspections (like listing values for a key) and complex queries across multiple attributes and data sources. It is designed to handle large datasets efficiently and supports both synchronous and asynchronous search, enabling users to retrieve complete results in a single operation or paginate through results as needed. It leverages Elasticsearch, a distributed, open-source search and analytics engine optimized for large data volumes.

All interactions are via standard REST APIs (GET and POST) using JSON, making it easy to integrate with web applications, scripts, or other backend services.


Key Features *

* Fast, scalable search capable of handling large datasets efficiently
* Flexible Search Operators:

  - Supports operators such as equals, not equals, and contains.
* Complex Query Support:

  - Combine multiple conditions using AND and OR to answer advanced data queries.
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
========

SearcherEngine can index and query data from multiple resources, even if:

* They are in different formats
* Some require preprocessing (e.g., converting to CSV)

  - CSV files must follow the supported  structure to be indexed successfully.
  - CSV templates are provided to guide users in preparing files that match the required format.

**Example data resources:**

* IDR Data resource  : Database with sources metadata
* SSBD Data resource : CSV files exported from a different public resource and converted to the supported CSV format before indexing.
* BIA Data resource : Data requiring conversion to CSV before indexing
* Ome2024-ngff-challenge data resource : Data requiring conversion to CSV before indexing

IDR Searcher reads data from each resource, processes it, and stores it in Elasticsearch.

Once indexed, users can:

* Run queries across all resources simultaneously
* Filter results by one or multiple data resources
* Export combined search results seamlessly
* Supports asynchronous search to fetch all results in one operation, or standard pagination for incremental retrieval.
* Export & Analysis:
  - Search results can be exported to CSV and Parquet formats.
  - Exported files are compatible with BFF for downstream filtering and data exploration.

Quick start
---------
Searcherengine does not provide a graphical user interface (GUI). All interactions are performed via REST APIs.
It can be used via:
•	Integration into backend services for other applications
•	Automation scripts
•	Swagger (OpenAPI) UI for testing endpoints
•	API clients (Postman, curl)

For Administrators
=================
Deployment and configuration are handled via dedicated Ansible role, i.e. `ansible-role-omero-searchengine <https://https://github.com/ome/ansible-role-omero-searchengine?tab=readme-ov-file#example-playbook>`_  , which includes `a sample deployment playbook <https://https://github.com/ome/ansible-role-omero-searchengine?tab=readme-ov-file#example-playbook>`_ .
Deploy Using Ansible

1.	Review the sample playbook and adjust variables for your environment.
2.	Run the playbook::

            ansible-playbook deploy.yml

For Users / Integrators
=========
* Ensure Searchengine is running and accessible to your application.
* Submit queries via your frontend, API clients (Postman, curl), or automation scripts.
* Export results in JSON, CSV, or Parquet format if needed.

For full API reference and interactive testing, use the Swagger UI:

    https://idr.openmicroscopy.org/searchengine/apidocs

Multiple example queries are included in the examples/ directory, ready to run or integrate.

Using IDR Searcher REST API
======
IDR  Searcher is an API-only backend service. All interactions are via HTTP using standard REST methods. Data is exchanged in JSON format.
* GET — Used for simple queries via URL parameters
* POST — Used for more complex queries with JSON payloads

**GET Example (Simple Query):**

    https://idr.openmicroscopy.org/searchengine/api/v1/resources/image/search/?key=Gene%20Symbol&value=pdx1&data_source=idr

What it does:

* Finds all images where **Gene Symbol** = **pdx1** and **data resource** = **idr**
* Returns JSON results

**POST Example (Complex Query)**::

    POST https://idr.openmicroscopy.org/searchengine/searchengine//api/v1/resources/submitquery/
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
* Returns JSON results ready for your Script, web application or backend service

For more advanced examples, see the examples/ directory or Swagger UI.

Documentation
--------
IDR Searcher includes detailed documentation for different audiences:
* User Guide
    How to construct queries, use filters, and interpret API responses.
* Configuration Guide
    Guides you through configuring data sources, Elasticsearch, deployment options, indexing, and environment settings.
* Developer Guide
    Technical details for extending, maintaining, or contributing to the service.


**Not sure where to start?**

* Using the API: Read the User Guide.
* Deploying/configuring: Read the Configuration Guide.
* Extending or contributing: Read the Developer Guide.

Disclaimer
----------

* The SearchEngine currently is intended to be used with public data.
* There is no authenticating or access permission in place yet.
* All the indexed data is exposed publicly.

License
-------

IDR searcher is released under the GPL v2.

Copyright
---------

2022-2026, The Open Microscopy Environment, Glencoe Software, Inc.
