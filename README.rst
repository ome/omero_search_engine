.. image:: https://github.com/ome/omero_search_engine/workflows/Build/badge.svg
   :target: https://github.com/ome/omero_search_engine/actions

.. image:: https://readthedocs.org/projects/omero-search-engine/badge/?version=latest
    :target: https://omero-search-engine.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

IDR Searcher
============

Table of Contents
-----------------

- `Introduction <#introduction>`_
- `Key Features <#Key-Features>`_
- `Multiple Data Sources Supports <#Multiple-Data-Sources-Support>`_
- `Quick Start <#Quick-Start>`_
- `Documentation <#Documentation>`_
- `Disclaimer <#Disclaimer>`_
- `License <#License>`_

Introduction
------------
IDR Searcher is an Elasticsearch-based search engine developed for `IDR <idr.openmicroscopy.org>`_  (Image Data Resource) to index and analyse metadata stored as key–value pairs. It supports both simple lookups and complex queries across large datasets, with synchronous and asynchronous search capabilities.

The system connects directly to OMERO databases, which run on **PostgreSQL** and also supports CSV data sources. All functionality is exposed through REST APIs (GET/POST) using JSON, enabling easy integration with web applications and backend services.

Although built for IDR, IDR Searcher can be used as a backend search service for any application where data resides in an OMERO database or `supported CSV format <https://github.com/ome/omero_search_engine/tree/main/omero_search_engine/cache_functions/elasticsearch/csv_templates>`_  and is intended for public access.

Key Features
------------

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
* High-Performance Parallel Indexing

  - It uses parallel processing to efficiently index large volumes of data and optimize indexing speed and scalability.
* Resource Filtering:

  - Restrict search results to one or more selected data resources.
* Data Export:

  - Export indexed data or search results to JSON, CSV, or Parquet format
  - CSV and Parquet files are compatible with `BFF <https://bff.allencell.org/>`_ (BioFile Finder Format). BFF is a tool for filtering, sorting and grouping tabular data) for advanced filtering and data exploration
* Asynchronous Search:

  - Fetch all matching results from large queries in one operation.
  - Ideal for handling large query results without multiple requests.
* Dynamic Configuration Reload

  – The IDR Searcher API server monitors its configuration file and automatically reloads changes without requiring a restart.

Multiple Data Sources Support
-----------------------------

SearcherEngine can index and query data from multiple resources, even if:

* They are in different formats
* Some require preprocessing (e.g., converting to CSV)

  - CSV files must follow the supported structure to be indexed successfully.
  - CSV templates are provided to guide users in preparing files that match the required format.

**Case Study: Indexing Multiple Data Sources in a Single Deployment**

In one implemented deployment, the following data sources were indexed within the same IDR Searcher instance and made searchable together:

* IDR Data resource  ->  Database with sources metadata
* `SSBD <https://ssbd.riken.jp/database/>`_ Data resource -> use of CSV files exported from public resource and converted to the supported CSV format before indexing.
* `BIA <https://www.ebi.ac.uk/bioimage-archive/>`_ Data resource -> Data requiring conversion to CSV before indexing
* `OME 2024 NGFF Challenge <https://ome.github.io/ome2024-ngff-challenge/>`_  Data resource -> Data requiring conversion to CSV before indexing

All of these sources were indexed into the same search environment, enabling users to:

* Run queries across all resources simultaneously
* Filter results by one or multiple data resources
* Export combined search results seamlessly
* Use asynchronous search to fetch all results in one operation, or standard pagination for incremental retrieval.
* Export & Analyse:
  - Search results can be exported to CSV and Parquet formats.
   - The exported files are compatible with BFF for downstream filtering and data exploration.

Quick Start
------------
For Users / Integrators
~~~~~~~~~~~~~~~~~~~~~~~

IDR Searcher is an API-only backend service. All interactions with the system are performed through HTTP using standard REST methods. Data is exchanged in JSON format.

The API supports the following request methods:

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

For more advanced examples, see the `examples/ <https://github.com/ome/omero_search_engine/tree/main/examples>`_ directory or `API documentation <https://idr-testing.openmicroscopy.org/searchengine/apidocs/>`_.

For Administrators
~~~~~~~~~~~~~~~~~~
Deployment and configuration are handled via dedicated Ansible role, i.e. `ansible-role-omero-searchengine <https://github.com/ome/ansible-role-omero-searchengine>`_  , which includes `a sample deployment playbook <https://github.com/khaledk2/ansible-role-omero-searchengine?tab=readme-ov-file#example-playbook>`_ .
Deploy Using Ansible. The sample playbook should be reviewed and the variables need to be adjusted for host environment.

Documentation
-------------

IDR Searcher includes detailed documentation for different audiences:

* `User Guide <https://omero-search-engine.readthedocs.io/en/latest/user_guide/user_guide.html>`_

  - How to construct queries, use filters, and interpret API responses.
*  `Configuration Guide <https://omero-search-engine.readthedocs.io/en/latest/configuration/configuration_installation.html>`_

   - Guides you through configuring data sources, Elasticsearch, deployment options, indexing, and environment settings.
* `Developer Guide <https://omero-search-engine.readthedocs.io/en/latest/developer/developer.html>`_

  - Technical details for extending, maintaining, or contributing to the service.

Disclaimer
----------

* The IDR Searcher currently is intended to be used with public data.

  - All indexed data is publicly accessible for search
* There is no authenticating or access permission in place yet.

  - We are working on the authentication and access permission problem solution for the private data.

License
-------

IDR Searcher is released under the GPL v2.

Copyright
---------

2022-2026, The Open Microscopy Environment, Glencoe Software, Inc.
