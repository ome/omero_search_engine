source vars.txt
echo  $SEARCHENGINE_IMAGE
echo $NEW_DATA_SOURCE
sudo docker run -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net $SEARCHENGINE_IMAGE set_data_source_files -n  $NEW_DATA_SOURCE
