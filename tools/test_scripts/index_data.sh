#!/bin/bash
source image_name.txt
echo  $SEARCHENGINE_IMAGE
sudo docker run -d  --name searchengine_index   -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/  --network=searchengine-net $SEARCHENGINE_IMAGE get_index_data_from_database

