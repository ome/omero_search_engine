source vars.txt
echo  $SEARCHENGINE_IMAGE
sudo docker run   -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net  $SEARCHENGINE_IMAGE delete_containers  -i $IDs -d $DATA_SOURCE -r $RESOURCE -u $UPDATE_CACHE -s True
