System configuration
====================
The application should have the access attributes (e.g, URL, username, password, etc.) for the PostgreSQL database server and Elasticsearch.

    * The configuration is saved in a yml file (.app_config.yml)
    * The file is saved in the user home folder
    * The configuration file template ({path/to/project}/configurations/app_config.yml) is distributed with the code and automatically copied to the user home folder when it runs for the first time.
    * The user should edit this file and provide the required attributes , e.g.,
        * DATABASE_SERVER_URI
        * DATABASE_USER
        * DATABASE_PASSWORD
        * DATABASE_NAME
        * ELASTICSEARCH__URL
        * PAGE_SIZE
    *  Although the user can edit this file to set the values, there are some methods inside manage.py which could help to set the configuration e.g.
        * set_database_configuration
        * set_elasticsearch_configuration

* When the app runs for the first time, it will look for the application configuration file.

    * If the file does not exist, it will copy a default file to the user's home folder.
    * The file contains some default values which the user can modify.

* The user needs to install Elasticsearch before start using the app.

    * The user can find more information about installing Elasticsearch using the following link:
        * https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html#install-elasticsearch

The user needs to create the ELasticsearch indices and insert the required data in order to use the application.

* There is a method inside manage.py (get_index_data_from_database) to allow indexing automatically from the app.

* Another method to index the data:
    * The data is extracted from the IDR/Omero database using some SQL queries and saved to csv files ({path/to/project}/omero_search_engine/search_engine/cache_functions/elasticsearch/sql_to_csv.py)
    * The image index data is generated in a large file, so it is recommended that the user splits it into several files to facilitate processing the data and inserting it into the index. In Linux os, users can use the split command to divide the file, for example:
        * split -l 2600000 images.csv
    * Create_index: Create the Elasticsearch indices, it can be used to create a single index or all the indices; the default is creating all the indices.
    * the indices are saved in this script ({path/to/project}/omero_search_engine/search_engine/cache_functions/elasticsearch/elasticsearch_templates.py)
    * add_resource_data_to_es_index: Insert the data to the ELasticsearch index; the data can be in a single file (CSV format) or multiple files.


Application installation using docker:
======================================
Ubuntu and Centos7 images are provided
* The user may build the docker image using the following command:

    * docker build . -f deployment/docker/centos/Dockerfile -t searchengine

* Alternatively, the user can pull the openmicroscopy docker image by using the following command:
    * docker pull openmicroscopy/omero-searchengine:latest

* The image runs on port 5577 so mapping this port is required to expose the port to the host machine
* Also, folders (i.e. /etc/searchengine) and local data folder (e.g. user home folder) should be mapped to a folder inside the the host machine.
    * It will be used to save the configuration file so the user can configure his instance
    * Additionally, it will be used to save the logs files and other cached data.

* An example of running the docker run command for a Centos image which maps the etc/searchengine to the user home folder in order to save the log files as well as mapping the application configuration file:
    * docker run --rm -p 5577:5577 -d  -v $HOME/:/etc/searchengine/  searchengine
* This is an example of a Docker image command to un index and re-index:
    * docker run -d  --name searchengine_2 -v $HOME/:/etc/searchengine/  -v $HOME/:/opt/app-root/src/logs/  --network=searchengine-net searchengine get_index_data_from_database
* The user can call any method inside manage.py by adding the method name at the end of the run command. e.g:
    *  docker run --rm -p 5577:5577 -v $HOME/:/etc/searchengine/  searchengine show_saved_indices

Searchengine installation and configuration using Ansible:
==========================================================

There is an ansible playbook (management-searchengine.yml) that has been written to deploy the apps:

* It will config and run searchengine, Elasticsearch and searchengine client
* It will configure and create the required folders
* It will configure the three apps and run them
* There is a variables file (searchengine_vars.yml) that the user needs to edit before running the playbook.
  The variable names are self-explanatory and should be customized to the host machine
* To check that the apps have been installed and run, the user can use wget or curl to call:

    * for searchengine, http://127.0.0.1:5556/api/v1/resources/
    * for searchengine client, http://127.0.0.1:5556
    * for Elasticsearch, http://127.0.0.1:9201
* After deploying the apps, the user needs to run another playbook for indexing:

    * run_searchengine_index_services.yml
    * If the Postgresql database server is located on the same machine which hosts the searchengine, the user needs to:

        * Edit pg_hba.conf file (one of the postgresql configuration files) and add client IP (i.e. 10.11.0.11)
        * Reload the configuration, so the PostgreSQL accepts the connection from indexing and caching services.
    * As the caching and indexing processes take a long time, there are another two playbooks that enable the user to check if they have finished or not:
    
        * check_indexing_service.yml