Omero Search Engine
--------------------
* Omero search engine app  is used to search metadata (key-value pairs)
* The app supports asynchronous searching
    * It will not block the server in case of a long query.
    * The user can submit their search and either wait or return later to retrieve the search results
* I have cached names and values from the database (key-value pairs) in hd5f files.
    * It detects the "no existence attributes" before attempting to query the database.
* Also, the app caches the queries which leads to reduced query time by re-using the cached values
* When a query is submitted:
    * It will check the cached values
        * If all or part of the query are cached, then it will use the cached value(s)
        * Otherwise it will query the database and save (cache) the results so that it can be used if it is needed again

* There is a simple GUI (link to the project) which is used to build the query and send it to the search engine
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

         resp = requests.get(url=base_url + image_ext, data=json.dumps(q_data))
         res = resp.text
         ress = json.loads(res)
         task_id = ress.get('task_id')

         status="PENDING"
         url_="http://127.0.0.1:5556/searchresults/?task_id={task_id}".format(task_id=task_id)

         while status!="SUCCESS":
             try:
                 resp = requests.get(url_)
                 res=resp.text
                 results=json.loads(res)
                 status=results.get("Status")
                 print ("Ststus: ", status)
                 print (results.keys())
                 if status!="SUCCESS":
                     time.sleep(2)
                 elif status=="FAILURE":
                     print ("Failed, reason: {reason}".format(reason=results.get("Results")))
             except Exception as ex:
                 print ("Error: {error}".format(error=str(ex)))
                 time.sleep(2)

         print ("Results: ",results.get('Results').get('results'))

