Data Indexing: Instructions and Guidelines 
==========================================
The `ansible-role-omero-searchengine <https://github.com/ome/ansible-role-omero-searchengine/>`_  allows the user to trigger the indexing process on a remote server.bFor more information, refer to the Ansible role README.

An alternative approach is to use the ``maintenance scripts`` that run locally.
When the searcher runs for the first time, it copies the maintenance scripts to the following folder on the host machine:
``$App_folder/searchengine/searchengine/test_scripts``.

***These scripts assist the user in running the indexing functions, as described below:***

* Index the data from a database data source
  - ``get_data_from_datasource_database.sh``
* Index the data using CSV files
  - ``get_data_from_csv_datasource.sh``
* The indexer can handle one or more container(s) (project or screen). No mixing containers type (screen with project) is supported 
  - ``index_container_from_database.sh``
* If the user adds a container and would like to modify anything, the container should first be deleted and then re-indexed
  - ``delete_container.sh``
* After indexing or deleting the container(s), the script to update the cache must be run
  - ``update_datasource_cache.sh``
* If an error occurs, the user can restore the original status by restoring the backup data.     
  - ``restore_searchengine_data.sh``
* After finishing the work and checking everything, the data backup should run.
  - ``backup_searchengine_data.sh``
* There is a text file (``vars.txt``) containing the required attributes for running the scripts.

The user must edit this file with the appropriate values before executing any script.
