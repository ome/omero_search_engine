#!/bin/bash
source vars.txt
echo  $SEARCHENGINE_IMAGE
sudo docker run   --name searchenginecach  --rm  -v /searchengine_backup/:/searchengine_backup/ -v /data/searchengine/searchengine/:/etc/searchengine/ --network=searchengine-net  $SEARCHENGINE_IMAGE backup_elasticsearch_data
