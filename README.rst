.. image:: https://github.com/ome/omero_search_engine/workflows/Build/badge.svg
   :target: https://github.com/ome/omero_search_engine/actions

.. image:: https://readthedocs.org/projects/omero-search-engine/badge/?version=latest
    :target: https://omero-search-engine.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

IDR searcher
============

Table of Contents
-----------------

- `Introduction <#introduction>`_
- `Quick Start <#Quick-Start>`_
- `Deployment <#Deployment>`_
- `Key Features <#Key-Features>`_
- `Multiple Data Sources Support <#Multiple-Data-Sources-Support>`_
- `Documentation <#Documentation>`_
- `Public data note <#Note-on-public-data>`_
- `License <#License>`_

Introduction
------------
IDR searcher is an `Elasticsearch-based <https://www.elastic.co/elasticsearch>`_ search engine developed for `Image Data Resource (IDR) <https://idr.openmicroscopy.org>`_ to index and analyse metadata stored as key–value pairs. It supports both simple lookups and complex queries across large datasets, with synchronous and asynchronous search capabilities.

The system connects directly to OMERO databases and also supports Comma Separated Values (CSV) as data sources, see `supported CSV format <https://github.com/ome/omero_search_engine/tree/main/omero_search_engine/cache_functions/elasticsearch/csv_templates>`_. All functionalities are exposed through REST APIs ``(GET/POST)`` using JSON.

.. code-block::

    ⚠️ IDR searcher currently ignores the OMERO permissions system. 
    It assumes that all data is to be indexed and all indexed
    data is publicly available. **Do not** run IDR Searcher on
    authenticated/private OMERO instances.

Although initially built for IDR, IDR searcher can be used as a backend search service for any application where data resides in an OMERO database or supported CSV format.

Quick Start
------------

IDR searcher is an API-only backend service. All interactions with the system are performed through HTTP using standard REST methods. Data is exchanged in JSON format.

The API supports the following request methods:

* ``GET`` — Used for simple queries via URL parameters.
* ``POST`` — Used for more complex queries with JSON payloads.

Start with the two examples below. For more advanced examples, see the `examples <https://github.com/ome/omero_search_engine/tree/main/examples>`_ directory or `API documentation <https://idr-testing.openmicroscopy.org/searchengine/apidocs/>`_.

*GET Example (Simple Query)*

- Find all images where **Gene Symbol** = **pdx1** and **data source** = **idr** and return JSON results:

  - https://idr.openmicroscopy.org/searchengine/api/v1/resources/image/search/?key=Gene%20Symbol&value=pdx1&data_source=idr



*POST Example (Complex Query)*

- Search across two resources (**image** and **container**), filter records where **Organism** = **mus musculus** and **Imaging Method** = **spim** and return JSON results ready for a script, web application or backend service::

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

Deployment
----------
Deployment and configuration are handled via a dedicated `Ansible role <https://github.com/ome/ansible-role-omero-searchengine>`_ which includes `a sample deployment playbook <https://github.com/ome/ansible-role-omero-searchengine?tab=readme-ov-file#example-playbook>`_. Review and adjust as needed the variables in the sample playbook for particular host environment.

Key Features
------------

- Fast, scalable search capable of handling large datasets efficiently.
- Support operators such as ``equals``, ``not equals``, and ``contains``.
- Combine multiple conditions using ``AND`` and ``OR`` to answer advanced data queries.
- Export indexed data or search results to JSON, CSV, or Parquet format. For IDR, full study data in CSV or Parquet format can be obtained using a link, try the `CSV example <https://idr.openmicroscopy.org/searchengine//api/v1/resources/container_bff_data/?container_name=idr0092-ostrop-organoid%2FscreenA%20&container_type=screen&file_type=csv>`_. The Parquet format is not human readable.
- CSV and Parquet files are compatible with `BioFile Finder <https://bff.allencell.org/>`_ , a tool for filtering, sorting and grouping tabular data for advanced filtering and data exploration.
- Search across multiple source types, e.g. images, projects, screens, plates, and datasets.
- Attribute-Agnostic search, which finds records by value even if the attribute name is unknown.
- Multi data source Indexing, such as indexing of data from database servers, database backups, and CSV files.
- High-Performance parallel indexing to process efficiently large volumes of data.
- Resource filtering to restrict search results to one or more selected data resources.
- Asynchronous search (for large queries) to fetch all matching results from large queries in one operation.
- Dynamic configuration ceload.

Multiple Data Sources Support
-----------------------------

IDR searcher can index and query data from multiple sources, even if their format is not unified. Preprocessing (converting to `supported CSV format <https://github.com/ome/omero_search_engine/tree/main/omero_search_engine/cache_functions/elasticsearch/csv_templates>`_ ) might be necessary, see `Case Studies <CASE_STUDIES.rst>`_ for concrete examples.

Documentation
-------------

* `User Guide <https://omero-search-engine.readthedocs.io/en/latest/user_guide/user_guide.html>`_ includes the construction of queries, the usage of filters, and the interpretation of API responses.
*  `Configuration Guide <https://omero-search-engine.readthedocs.io/en/latest/configuration/configuration_installation.html>`_ explains the configurations of data sources, Elasticsearch, the deployment options, the indexing, and the environment settings.
* `Developer Guide <https://omero-search-engine.readthedocs.io/en/latest/developer/developer.html>`_ provides technical details for extending, maintaining, or contributing to the service.

Note on public data
-------------------

* The IDR searcher currently assumes that all indexed data is publicly accessible for search.
* There is no authentication or access permissions system in place yet. IDR Searcher is bypassing OMERO authentication and permissions system by connecting directly to the Database.

License
-------

IDR searcher is released under the GPL v2.

Copyright
---------

2022-2026, The Open Microscopy Environment.




