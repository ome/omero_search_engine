source searchengine_image_name.txt
sudo docker run  --name dump_projects   -d -v /data/data_dump:/data/data_dump  -v /data/searchengine/searchengine/:/etc/searchengine/  -v /data/searchengine/searchengine/logs/:/opt/app-root/src/logs/ --network searchengine-net $searchengine_docker_image dump_searchengine_data -d idr -r project  -f csv_bff -t /data/data_dump/idr/csv_bff -o True
