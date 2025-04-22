System configuration
====================

The application should have the access attributes (e.g, URL, username, password, etc.) for the PostgreSQL database server and Elasticsearch.

    * The configuration is saved in a yml file (``.app_config.yml``)
    * The file is saved in the user home folder
    * The configuration file template :omero_search_engine:`app_config.yml <configurations/app_config.yml>` is distributed with the code and automatically copied to the user home folder when it runs for the first time.
    * The user should edit this file and provide the required attributes , e.g.

      * ``DATABASE_SERVER_URI``
      * ``DATABASE_USER``
      * ``DATABASE_PASSWORD``
      * ``DATABASE_NAME``
      * ``ELASTICSEARCH__URL``
      * ``PAGE_SIZE``
      * ``ELASTIC_PASSWORD``
    * Although the user can edit this file to set the values, there are some methods inside :omero_search_engine:`manage.py <manage.py>` which could help to set the configuration e.g.

      * ``set_database_configuration``
      * ``set_elasticsearch_configuration``
      * ``set_elasticsearch_password``

* When the app runs for the first time, it will look for the application configuration file.

  * If the file does not exist, it will copy a default file to the user's home folder.
  * The file contains some default values which the user can modify.

* The user needs to install Elasticsearch_ before start using the app.

* The user needs to create the Elasticsearch_ indices and insert the required data in order to use the application.

* The method ``get_index_data_from_database`` inside :omero_search_engine:`manage.py <manage.py>` allows indexing automatically from the app.

* Another method to index the data:

  * The data is extracted from the IDR/OMERO database using some SQL queries and saved to csv files using :omero_search_engine:`sql_to_csv.py <omero_search_engine/cache_functions/elasticsearch/sql_to_csv.py>`
  * The image index data is generated in a large file, so it is recommended that the user splits it into several files to facilitate the processing of the data and its insertion into the index e.g. ``split -l 2600000 images.csv``.
  * ``create_index``: Create the Elasticsearch indices, it can be used to create a single index or all the indices; the default is creating all the indices.
  * the indices are saved using the script :omero_search_engine:`sql_to_csv.py <omero_search_engine/cache_functions/elasticsearch/elasticsearch_templates.py>`
  * ``add_resource_data_to_es_index``: Insert the data to the ELasticsearch index; the data can be in a single file (CSV format) or multiple files.


Application installation using Docker
=====================================

Ubuntu and Rocky Linux 9 images are provided.

* The user may build the Docker image using the following command::

    $ docker build . -f deployment/docker/$required_docker_file_folder/Dockerfile -t searchengine

* Alternatively, the user can pull the openmicroscopy docker image by using the following command::
    
    $ docker pull openmicroscopy/omero-searchengine:latest

* The image runs on port ``5577`` so mapping this port is required to expose the port to the host machine.

* Also, folders (i.e. ``/etc/searchengine``) and local data folder (e.g. user home folder) should be mapped to a folder inside the the host machine.

  * It will be used to save the configuration file so the user can configure his instance
  * Additionally, it will be used to save the logs files and other cached data.

* An example of running the docker run command for a Rocky Linux image which maps the ``etc/searchengine`` folder to the user home folder in order to save the log files as well as mapping the application configuration file ::

    $ docker run --rm -p 5577:5577 -d  -v $HOME/:/etc/searchengine/  searchengine

* This is an example of a Docker image command to un index and re-index ::

    $ docker run -d  --name searchengine_2 -v $HOME/:/etc/searchengine/  -v $HOME/:/opt/app-root/src/logs/  --network=searchengine-net searchengine get_index_data_from_database

* The user can call any method inside :omero_search_engine:`manage.py <manage.py>` by adding the method name at the end of the run command e.g.::

    $ docker run --rm -p 5577:5577 -v $HOME/:/etc/searchengine/  searchengine show_saved_indices

Searchengine installation and configuration using Ansible
=========================================================

IDR team has developed installation playbooks that can be downloaded, customized and used to install the searchengine.

* The first playbook [deploy_elasticsearch_cluster.yml](https://github.com/IDR/deployment/blob/master/ansible/idr-elasticsearch.yml) will create the required folders and configure and run the Elasticsearch cluster
* The second one, [deploy_searchengine.yml](https://github.com/IDR/deployment/blob/master/ansible/idr-searchengine.yml) will configure and run the searchengine app
* There is a variables file [searchengine_vars.yml](https://github.com/IDR/deployment/blob/master/ansible/group_vars/searchengine-hosts.yml) that the user needs to edit before running the playbook.
  The variable names are self-explanatory and should be customized to the host machine
* To check that the apps have been installed and run, the user can use ``wget`` or ``curl`` to call:

    * for searchengine, http://127.0.0.1:5577/api/v1/resources/
    * for Elasticsearch, http://127.0.0.1:9201

* After deploying the apps, the user needs to run the [run_searchengine_index_services.yml](https://github.com/IDR/deployment/blob/master/ansible/run_searchengine_index_service.yml) playbook for indexing:

    * If the PostgreSQL database server is located on the same machine which hosts the searchengine, the user needs to:

        * Edit ``pg_hba.conf`` file (one of the postgresql configuration files) and add the client IP (i.e. 10.11.0.11)
        * Reload the configuration, so the PostgreSQL accepts the connection from indexing and caching services.

    * As the caching and indexing processes take a long time, there are another two playbooks that enable the user to check if they have finished or not:

        * [check_indexing_service.yml](https://github.com/IDR/deployment/blob/master/ansible/check_indexing_service.yml)
