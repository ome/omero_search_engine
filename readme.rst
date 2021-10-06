Omero Search Engine
--------------------
* Omero search engine app  is used to search metadata (key-value pairs)
* The app supports asynchronous searching
    * It will not block the server in case of a long query.
    * The user can submit their search and either wait or return later to retrieve the search results
* I have cached names and values from the database (key-value pairs) in hdf5 files.
    * It detects the "no existence attributes" before attempting to query the database.
* Also, the app caches the queries which leads to reduced query time by re-using the cached values
* When a query is submitted:
    * It will check the cached values
        * If all or part of the query are cached, then it will use the cached value(s)
        * Otherwise it will query the database and save (cache) the results so that it can be used if it is needed again

* There is a simple GUI (https://github.com/ome/omero_search_engine_client) which is used to build the query and send it to the search engine
    * It is used to build the query
    * It will display the results when they are ready
* The query can be submitted using a script
    * There is a sample script to submit the query and get the results:

.. code-block:: python

         import sys
         import requests
         import json
         import time

         base_url="http://127.0.0.1:5556/api/v1/"
         image_ext="/resources/image/searchannotation/"
         query_details={"and_filters": [{"Cell Line": "HeLa"},{"Gene Symbol" : "NCAPD2"},{ "Cell Cycle Phase": "anaphase"}], "not_filters": [], "or_filters": []}
         q_data = {"query": {'query_details': query_details}}

         resp = requests.get(url="{base_url}{image_ext}".format(base_url=base_url,image_ext=image_ext), data=json.dumps(q_data))

         res = resp.text
         ress = json.loads(res)
         task_id = ress.get('task_id')

         status="PENDING"
         url_="http://127.0.0.1:5556/searchresults/?task_id={task_id}".format(task_id=task_id)

         while status=="PENDING":
             try:
                 resp = requests.get(url_)
                 res=resp.text
                 results=json.loads(res)
                 status=results.get("Status")
                 print ("Ststus: ", status)
                 print (results.keys())
                 if status=="PENDING":
                     time.sleep(2)
                 elif status=="FAILURE":
                     print ("Failed, reason: {reason}".format(reason=results.get("Results")))
             except Exception as ex:
                 print ("Error: {error}".format(error=str(ex)))
                 time.sleep(2)

         print ("Results: ",results.get('Results').get('results'))
Please note that: 
   * The app requires a direct connection to the PostgreSQL database server.
   * The app configuration is read from a yml file (".app_config.yml") which is saved in the user's home folder. 
      * The user should write the yml file to configure the database server and redis server connections.
* The app needs 
Known issues
============
* Although the search engine will work, in some cases the search takes a long time to complete (Asynchronous search). It is important to improve the user experience and reduce the search time as much as possible.
* Sometimes the search engine fails to complete a user request when the number of parallel jobs is high and the search contains terms which have a large number of records (e.g. “Home Species” contains more than 12 million records). We may need to customise the queuing system, scale the worker (celery workers), improve the search mechanism, and manage the memory more efficiently.
* When the data is changed inside the database, this will invalidate the cached data and it will need to be cached again. We need to have a mechanism to update the cached data rather than recreate them.
* The search engine lacks a user access permission system; this is fine when working with the IDR but if we need to deploy it on an Omero server, the access permission is required.
