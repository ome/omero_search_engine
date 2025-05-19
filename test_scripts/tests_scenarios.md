Test delete and index container
===============================
* Perform a search and check the results to identify a container in which the results contain images.
For example, search the Gene Symbol=pax6
https://idr-testing.openmicroscopy.org/search/?key=Gene+Symbol&value=pax6&operator=equals
* In this search there are results that come from project **idr0114-lindsay-hdbr/experimentA**, its is id=**2151**
* When deleting a project using the **delete_container.sh** script,  the cache will also be deleted. The cache will have to be manually created if the flag to update the cache automatically is set to ``false``. This process may take time depending on the number of containers inside the data source.
* Perform the same search and then the results should not contain any image from this project
* This project should be re-indexed and the data source cache updated using **index_container_from_database.sh** script. Then search again, the results from this project should be displayed.

Scripts for deleting containers, indexing containers, updating the cache, and checking the progress of deleted containers in the case of an asynchronous deletion are available. The user should configure these scripts using the attributes inside the ``vars.txt`` file.

Test data sources
=================
* The default data source is idr, so the IDR-Gallery only returns the results from IDR.
* It is possible to change the default data source using **update_datasource_cache.sh**  
* Use the endpoint ``searchengine/api/v1/resources/data_sources/`` to check all the available data sources in the search engine,
* It is possible to override the default data source by adding a data source attribute to the request. For example, the following endpoint ``searchengine/api/v1/resources/image/search/?key=cell%20line&value=hela&data_source=ssbd&random_results=0`` will return the results for this query
**cell line=hela** from the **SSBD** data source only
* Add a new data source
  * There are two types of data sources
    * Database data source  
      * First add the database data source
        * This can be achieved using **add_new_database_data_source.sh** script to add omero_train datasource
      * Then index the data from the database
        * run the **get_data_from_datasource_database.sh** script to extract the data from the database and index them
    * CSV data source
      * It is required to add the CSV data source using **add_csv_data_source.sh** script
      * Then add the data from the CSV file using **get_data_from_csv_datasource.sh** script
      
* It is possible to delete a data source from the search engine using **delete_data_source.sh** script
  * Then, to check  all the available data sources use https://idr-testing.openmicroscopy.org/searchengine//api/v1/resources/data_sources/,  the response should not include the deleted datasource

Restoring the original data
===========================
* If restoring the original data is required, you can use the **restore_searchengine_data.sh** script to recover it from the indexed data snapshot.
* Additionally, it is recommended to restore the original app configuration file by running the**restore_searchengine_data.sh** script.
