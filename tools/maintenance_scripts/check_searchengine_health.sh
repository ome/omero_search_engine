#!/bin/bash
source vars.txt
sudo rm /data/searchengine/searchengine/check_report.txt
sudo docker run  --rm --name searchengine_validator  -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/  --network=searchengine-net  $SEARCHENGINE_IMAGE test_indexing_search_query
