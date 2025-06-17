- SSH into the machine where the search engine is installed.
- Replace the Docker image with one that supports the data dump functionality.

- To export all data in JSON format::

    docker run --rm -v /data/data_dump:/data/data_dump  -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net  Docker_imag_support_data_dump  dump_searchengine_data -t /data/data_dump

- This will generate JSON files in /data/data_dump.

- To dump data in BFF CSV format::

    docker run --rm -v /data/data_dump:/data/data_dump  -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net  Docker_imag_support_data_dump dump_searchengine_data -t /data/data_dump - b true




- To dump a single container (i.e. project or screen), specify its type and ID. For example, to export project 501::

    docker run --rm -v /data/data_dump:/data/data_dump  -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net Docker_imag_support_data_dump  dump_searchengine_data -t /data/data_dump - b true -i 501 -r project



- By default, it will checks if the CSV or JSON file already exists and skips it, to force overwrite, add "-o true" to the command.