Test delete and index container
===============================
* Perform a search and check the results to identify a container in which the results contain images.
For example, search the Gene Symbol=pax6
https://idr-testing.openmicroscopy.org/search/?key=Gene+Symbol&value=pax6&operator=equals
* In this search there are results that come from project **idr0114-lindsay-hdbr/experimentA**, its id=**2151**
* Delete this project using **delete_container.sh** script, then update the cache which will be updated. this process may take a long time  depending on the number of container inside the data source , I am looking to improve this, though perhaps not in this PR)
* Perform the same search and then the results should not have results from this project
* This project should be indexed and the data source cache updated using **index_continer_from_dataase.sh** script. Then search again, the results from this project should be displayed.

I have included scripts for deleting containers, indexing containers, updating the cache, and checking the progress of deleted containers in cthe ase of an asynchronous deletion. The user should configure these scripts using the attributes inside the vars.txt file.

* if restoring the original data is necessary, the **restore_searchengine_data.sh** script can be used to recover it from the indexed data snapshot

Test data sources
=================
* The default data source is idr, so the IDR-Gallery only returns the results from IDR.
  * It is possible to change the default data source using **update_datasource_cache.sh**  
* This URL should be used to check all the available data sources in the search engine,
  * https://idr-testing.openmicroscopy.org/searchengine//api/v1/resources/data_sources/
* It is possible to override the default data source by adding a data source attribute to the request. For example, the following URL will return the results for this query
**cell ine=hela** from the **SSBD** data source only
  * https://idr-testing.openmicroscopy.org/searchengine//api/v1/resources/image/search/?key=cell%20line&value=hela&data_source=ssbd&random_results=0
* Add a new data source
  * There are two types of data sources
    * Database data source  
      * First add the database data source
        * This can be achieved using **add_new_database_data_source.sh** script to add omero_train datasource
      * Then index the data from the database
        * run the **get_data_from_datasource_database.sh** script to extract the data from the database and index them
    * CSV data source
      * It is required to add the csv data source using **add_csv_data_source.sh** script
      * Then add the data from the csv file using **get_data_from_csv_datasource.sh** script
      
* It is possible to delete a data source from the search engine using **delete_data_source.sh** script
  * Then, to check  all the available data sources use https://idr-testing.openmicroscopy.org/searchengine//api/v1/resources/data_sources/,  the response should not include the deleted datasource
