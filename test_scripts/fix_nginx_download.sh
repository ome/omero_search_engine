 sudo find /data/data_dump/idr/csv_bff -type d -exec chmod 755 {} \;
 sudo find  /data/data_dump/idr/csv_bff -type f -exec chmod 644 {} \;
 sudo chown -R nginx:nginx /data/data_dump/idr/csv_bff
 sudo chcon -Rt httpd_sys_content_t /data/data_dump/idr/csv_bff
  
