Deployment Options
==================
Automated deployment using Ansible role
---------------------------------------
* We provide an Ansible role that you can use to install the search engine.

    * https://github.com/ome/ansible-role-omero-searchengine

* The README includes a sample playbook to install the search engine and all required components. You’ll need to customise the variables for your environment, mainly the OMERO database server URL, username, password, and database name.

    * https://github.com/ome/ansible-role-omero-searchengine?tab=readme-ov-file#example-playbook`

* The role can also be used to index data, as well as to backup and restore search-engine data.

* The role has been tested and used on RHEL 9–like systems, especially Rocky Linux 9.

Manual Installation using Docker
--------------------------------

Ubuntu and Rocky Linux 9 images are provided.

* Building the Docker image::

    $ docker build . -f deployment/docker/rockylinux/Dockerfile -t searchengine

* Alternatively, the user can pull the openmicroscopy docker image by using the following command::

    $ docker pull openmicroscopy/omero-searchengine:latest

* The image runs on port ``5577`` so mapping this port is required to expose the port to the host machine.

* Also, folders (i.e. ``/etc/searchengine``) and local data folder (e.g. user home folder) should be mapped to a folder inside the the host machine.

  * It will be used to save the configuration file so the user can configure his instance
  * Additionally, it will be used to save the logs files and other cached data.

* Below is an example of the docker run command for a Rocky Linux 9 image mapping the ``etc/searchengine`` folder to the user home folder in order to save the log files as well as mapping the application configuration file ::

    $ docker run --rm -p 5577:5577 -d  -v $HOME/:/etc/searchengine/  searchengine

* This is an example of a Docker image command to index and re-index ::

    $ docker run -d  --name searchengine_2 -v $HOME/:/etc/searchengine/  -v $HOME/:/opt/app-root/src/logs/  --network=searchengine-net searchengine get_index_data_from_database

* The user can call any method inside :omero_search_engine:`commands.py <commands.py>` by adding the method name at the end of the run command e.g.::

    $ docker run --rm -p 5577:5577 -v $HOME/:/etc/searchengine/  searchengine show_saved_indices

System configuration
====================

Configuration Overview
----------------------
* The IDR searcher needs the access attributes (e.g, URL, username, password, etc.) for the PostgreSQL database server and Elasticsearch.
* Settings include data sources, indexing behavior, and environment-specific options are also needed.
* ISR Searcher persists configuration settings in a file to ensure they are retained across restarts.
* All configuration changes made are automatically saved, making deployment and updates seamless.
* The Ansible role handle all necessary setup, including data sources, indexing behavior, and environment settings.
* Configuration is persisted automatically, so users do not need to manually edit configuration files; the changes can be made through via Ansible role.

Configuration file details (For developer)
------------------------------------------
    * The configuration is saved in a yml file (``.app_config.yml``)
    * The file is saved in the users home folder
    * The configuration file template :omero_search_engine:`app_config.yml <configurations/app_config.yml>` is distributed with the code and automatically copied to the user home folder when it runs for the first time.
    * The user should edit this file and provide the required attributes , e.g.

      * ``DATABASE_SERVER_URI``
      * ``DATABASE_USER``
      * ``DATABASE_PASSWORD``
      * ``DATABASE_NAME``
      * ``ELASTICSEARCH__URL``
      * ``PAGE_SIZE``
      * ``ELASTIC_PASSWORD``
    * This file can be edited manually to set/modify the values. Also, there are some methods inside :omero_search_engine:`commands.py <commands.py>` which could help to set the configuration e.g.

      * ``set_database_configuration``
      * ``set_elasticsearch_configuration``
      * ``set_elasticsearch_password``

* When the app runs for the first time, it looks for the application configuration file.

  * If the file does not exist, it will copy a default file to the user's home folder.
  * The file contains some default values that can be modified by the user.

Data Indexing Overview
=======================

Indexing imports data from a configured source into the search environment, preparing it for queries and analytics.

Key Points:
-----------

* Uses predefined schemas specified in the IDR Searcher templates (:omero_search_engine:`elasticsearch_templates.py <omero_search_engine/cache_functions/elasticsearch/elasticsearch_templates.py>`) which specify the structure and field mappings for indexed data.
* Ensures consistency across different data sources.
* Supports multiple types of sources: databases and CSV files.
* Uses parallel processing to optimize performance for large datasets.
* Typically executed during the first deployment or when adding a new data source.

Workflow Overview:
------------------

* Data source connection is established.
* Records are extracted in batches.
* Data is transformed to match the predefined template schema.
* Records are pushed into the Elasticsearch.
* Logs capture success, errors, and processed record counts.

Index the data from database
-----------------------------
* The Ansible role can be used to index the using tags
* Alternatively for advanced users, the method ``get_index_data_from_database`` inside :omero_search_engine:`commands.py <commands.py>` allows automatic indexing using docker commands.

Index the data using CSV files:
-------------------------------
  * Extract the data from the IDR/OMERO database using SQL queries and save them to CSV files using :omero_search_engine:`sql_to_csv.py <omero_search_engine/cache_functions/elasticsearch/sql_to_csv.py>`.
  * Alternatively, you can provide the data as CSV files that follows the supported CSV format. You can find more information in the :omero_search_engine:`README.md <omero_search_engine/cache_functions/elasticsearch/csv_templates/README.md>`.
  * If the data is generated in a large file, it is recommended that the user splits it into several files to facilitate the processing of the data and its insertion into the index e.g. ``split -l 2600000 images.csv``.
  * ``create_index``: Create the Elasticsearch indices no data have been previously added, it can be used to create a single index or all the indices; the default is to create all the indices.
  * The user must add a new data source (CSV) using the ''set_data_source_files'' command inside :omero_search_engine:`commands.py <commands.py>`
  * ``get_index_data_from_csv_files`` is used to read the data, to format it then to push the data to the resource Elasticsearch index. The user can provide a single file (CSV format) or folder. If a folder is specified, the indexer will use all the CSV files inside the folder.

Advanced users and system administrators can perform data indexing operations using dedicated maintenance scripts. The :omero_search_engine:`data_indexing.md <docs/user_guide/data_indexing.md>' document provides guidance on how to execute and manage these operations effectively.