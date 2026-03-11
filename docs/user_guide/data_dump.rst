Dumping Container Data
======================

The `ansible-role-omero-searchengine <https://github.com/ome/ansible-role-omero-searchengine/>`_
can trigger exporting the data remotely without the need to log in to the server directly. For more information, refer to the Ansible role README.

Alternatively, export the data by running a Docker command on the host where the IDR Search resides.

- SSH into the machine where the IDR-Searcher is deployed.
- Replace the Docker image with one that supports the data dump functionality, i.e. openmicroscopy/omero-searchengine:0.8.0 or recent

- To export the data in JSON format .::

    docker run --rm -v /data/data_dump:/data/data_dump  -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net  Docker_image_support_data_dump  dump_searchengine_data -t /data/data_dump/data_source -f json -d data_source -r container*
    * container parameter in the command can be set to either project or screen

- This will generate JSON files in /data/data_dump.

- To dump data in BFF CSV format::

    docker run --rm -v /data/data_dump:/data/data_dump  -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net  Docker_image_support_data_dump dump_searchengine_data -t /data/data_dump/data_source -f csv_bff -d data_source -r container


- To dump a single container (i.e. project or screen), specify its type and ID. For example, to export project 501::

    docker run --rm -v /data/data_dump:/data/data_dump  -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net Docker_image_support_data_dump  dump_searchengine_data -t /data/data_dump/data_source -d datasource -f csv_bff -i 501 -r project


- By default, it will checks if the CSV or JSON file already exists and skips it, to force overwrite, add "-o true" to the command.

- These functions can run using the OMERO-Searchengine Ansible Role (https://github.com/ome/ansible-role-omero-searchengine)