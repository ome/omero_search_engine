source vars.txt
echo  $SEARCHENGINE_IMAGE
sudo docker run -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net $SEARCHENGINE_IMAGE set_database_configuration -u $dDATABASE_URL -s  $DATABASE_PORT_NUMBER -n $DATABASE_USERNAME -p  $DATABASE_USER_PASSWORD -w $WORKING_DATA_SOURCE -d $DATABASE_NAME -b $BACKUP_FILE_NAME
