source vars.txt
echo  $SEARCHENGINE_IMAGE
sudo docker run -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net $SEARCHENGINE_IMAGE get_index_data_from_csv_files -d $NEW_DATA_SOURCE  -f  $NEW_DATA_SOURCE_IMAGES_CVS -r image -u $UPDATE_CACHE
sudo docker run -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net $SEARCHENGINE_IMAGE get_index_data_from_csv_files -d $NEW_DATA_SOURCE  -f  $NEW_DATA_SOURCE_PROJECTS_CVS -r  project -u $UPDATE_CACHE
