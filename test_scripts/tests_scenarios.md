Test delete and index container
===============================
* Perform a search and check the results to identify a container in which the results contain images from it.
For example, search the Gene Symbol=pax6
https://idr-testing.openmicroscopy.org/search/?key=Gene+Symbol&value=pax6&operator=equals
* In this search there are results come from this project idr0114-lindsay-hdbr/experimentA, its id=2151
* Delete this project, the cache will be updated (take some time to be completed, I am looking to improve this, though perhaps not in this PR)
* Perform the same search and then the results should not have a results from this project
* Then we can index this project again and update the cache and search again, the results from this project should be displayed in the results

I have included scripts for deleting containers, indexing containers, updating the cache, and checking the progress of delete tasks in case of asynchronous deletion. The user should configure these scripts using the attributes inside the vars.txt file.

* if restoring the original data is necessary, the restore_searchengine_data.sh script can be used to recover it from the indexed data snapshot


