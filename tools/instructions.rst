Post deployment tools
---------------------
The ``test_scripts sub-folder`` contains many scripts which can be used to check and maintain the health of the searchengine which includes the elasticsearch cluster nodes. The scripts should be used after deploying the searchengine.

The Elasticsearch cluster has three nodes. Each of them is both a master and a data node. The searchengine is configured to connect to Elasticsearch using a list containing the three nodes. It will try to connect to the first node in the list; if it is down, it will try to connect to the second node and so on.

The cluster itself is up if at least two nodes are running.

* ``image_name.txt`` file contains the docker image name

* The ``check_cluster_health.sh`` script is used to check the cluster status at any time.

* The searchEngine functions can be tested using the ``check_searchengine_health.sh`` script. The script takes about 15 minutes to run. The script output is saved to a text file check_report.txt in the``/data/searchengine/searchengine/`` folder.

* Stop an elasticsearch cluster node using this script (replace n with an integer which represents the node number, e.g. 1,2,3)::

    bash stop_node.sh n

* backup_elasticsearch_data.sh script is used to backup the Elasticsearch data.

* Index or re-index the data using the ``scrpt index_data.sh`` script.

* Restore the Elasticsearch data from the backup (snapshot) using the following command::

    bash restore_elasticsearch_data.sh

 It may take up to 15 minutes to restore the data.

* Check the progress of the data indexing using the ``check_indexing_process.sh`` script
