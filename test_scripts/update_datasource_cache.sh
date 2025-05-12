source vars.txt
echo  $SEARCHENGINE_IMAGE
sudo docker run   -d  -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net $SEARCHENGINE_IMAGE update_data_source_cache -d $DATA_SOURCE