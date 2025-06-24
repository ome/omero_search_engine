Data Indexing: Instructions and Guidelines for Using Maintenance Scripts
========================================================================
* The maintenance scripts are copied automatically to the following folder:
``/data/searchengine/searchengine/test_scripts``

***These scripts assist the user in running the indexing functions, as described below:***

* The indexer can handle one or more container (project or screen). No mixing containers type (screen with project) is supported 
``index_container_from_database.sh``

* If the user added a container and they would like to modify something they should delete the container and then indexing it again
``delete_container.sh``
* After indexing or deleting the container/s, the cache update needs to be run.
``update_datasource_cache.sh``
* If something went wrong, the user can restore the original status by restoring the backup data.     
``restore_searchengine_data.sh``
* After finishing the work and checking everything, the data backup should run.
``backup_searchengine_data.sh``
* There is a text file (``vars.txt``) containing the required attributes for running the scripts.
The user must edit this file with the appropriate values before executing the scripts.
