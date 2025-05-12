source vars.txt
echo  $SEARCHENGINE_IMAGE
sudo docker run -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net $SEARCHENGINE_IMAGE set_database_configuration -u $data_base_url -s  5432 -n omeroreadonly -p $data_base_user_bassword -w omero_train -d omero_train -b omero_train.pgdump