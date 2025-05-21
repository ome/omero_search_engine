source vars.txt
echo  $SEARCHENGINE_IMAGE
sudo docker run -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net $SEARCHENGINE_IMAGE set_database_configuration -u $data_base_url -s  $database_port_number -n $database_user_name -p  $data_base_user_bassword -w $working_data_source -d $database_name -b $backup_file_name
