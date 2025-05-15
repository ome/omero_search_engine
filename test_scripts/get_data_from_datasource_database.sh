source vars.txt
echo  $SEARCHENGINE_IMAGE
sudo docker run -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net $SEARCHENGINE_IMAGE get_index_data_from_database -b False -d omero_train
