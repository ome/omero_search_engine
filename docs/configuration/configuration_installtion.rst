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
        * DATABAS_NAME
        * CASH_FOLDER
        * ELASTICSEARCH__URL
        * PAGE_SIZE

* When the app runs for the first time, it will look for the application configuration file.

    * If the file does not exist, it will copy a default file to the user home folder.
    * The file contains some default values which the user can modify.

* The user needs to install the Elasticsearch before start using the app.

    * The user can find more information about installing Elasticsearch using the following link
        * https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html#install-elasticsearch

There is a need to create the ELasticsearch indices and insert the data to them to be able to use the application.

* This process is done right now using some methods inside manage.py
    * The data is extracted from the IDR/Omero database using some SQL queries and saved to csv files ({path/to/project}/omero_search_engine/search_engine/cache_functions/elasticsearch/sql_to_csv.py)
    * The image index data is generated in a big file, so it is recommended to split it into several files to facilitate processing the data and inserting it into the index. In Linux os, users can use the split command to divide the file, for example:
        * split -l 2600000 images.csv
    * create_index: Create the Elasticsearch indices, it can be used to create a single index or all the indices; the default is creating all the indices.
    * the indices are saved in this script ({path/to/project}/omero_search_engine/search_engine/cache_functions/elasticsearch/elasticsearch_templates.py)
    * add_resourse_data_to_es_index: Insert the data to the ELasticsearch index; the data can be in a single file (CSV format) or multiple files.

* It has some utility functions inside the manage.py script to build hd5 cash files.
    * These files contain the available key and value pair inside the database.
    * The user builds them using a direct connection with the Postgres database server.
    * These cashed data is available to the user through URLs as it is described in the user manual.

Application installation using docker:
======================================
Ubuntu and Centos7 images are provided
* The user should pull the image from:

    * Ubuntu: [imageurl]
    * Centos: [imageurl]

* The user should first pull the image and then run using a command docker run and then the image name.
* The image runs on port 5569 so mapping this port is required to expose the port to the host machine
* Also, folders (i.e. /etc/searchengine) and user home folder ($HOME) should be mapped to folder inside the the host machine.
    * It will be used to save the configuration file so the user can configure his instance
    * in addition, it will be used to save the logs files and other cached data.

* Example of running the docker run command for Centos image: which maps the etc/searchengine to the user home folder to save the log files, in addition, to mapping the application configuration file
    * docker run --rm -p 5569:5569 v /home/kmohamed001/.app_config.yml:/opt/app-root/src/.app_config.yml -v $HOME/:/etc/searchengine/  searchengine
* The user can call any method inside manage.py by adding the method name by end of the run command. e.g:
    *  docker run --rm -p 5569:5569 v /home/kmohamed001/.app_config.yml:/opt/app-root/src/.app_config.yml -v $HOME/:/etc/searchengine/  searchengine  show_saved_indices

* A detailed installation instructions will be provided shortly.