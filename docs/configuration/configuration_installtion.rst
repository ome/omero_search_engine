System configuration
====================

The application should have the access attributes (e.g, URL, username, password, etc.) for the PostgreSQL database server and Elasticsearch.

    * The configuration is saved in a yml file (.app_config.yml)
    * The file is saved in the user home folder
    * The configuration file template ({path/to/project}/configurations/app_config.yml) is distributed with the code and automatically copied to the user home folder when it runs for the first time.
    * The user should edit this file and provide the required attributes.

There is a need to create the ELasticsearch inches and insert the data to them to be able to use the application.

* This process is done right now using some methods inside manage.py
    * The data is extracted from the IDR/Omero database using some SQL queries ({path/to/project}/omero_search_engine/search_engine/cache_functions/elasticsearch/sql_to_csv.py)
    * The image index data is generated in a big file, so it is recommended to split it into several files to facilitate processing the data and inserting it into the index. In Linux os, users can use the split command to divide the file, for example:
        * split -l 2600000 images.csv
    * create_index: Create the Elasticsearch indices, it can be used to create a single index or all the indices; the default is creating all the indices.
    * the indices are saved in this script ({path/to/project}/omero_search_engine/search_engine/cache_functions/elasticsearch/elasticsearch_templates.py)
    * add_resourse_data_to_es_index: Insert the data to the ELasticsearch index; the data can be in a single file (CSV format) or multiple files.

* The names and values have been cashed from the database (key-value pairs) in hd5f files.
    * These cashed data is available to the user through URLs
