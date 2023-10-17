#!/bin/bash
source vars.txt

sudo docker run  -d --rm \
  -v /searchengine_backup:/searchengine_backup \
  -v  /data/searchengine/elasticsearch/node2/data:/var/lib/elasticsearch \
  -v  /data/searchengine/elasticsearch/node2/logs:/var/log/elasticsearch \
  -v $elast_certs_folder:/usr/share/elasticsearch/config/certificates \
  -p  9202:9200 \
  -p 9302:9300 \
  --network searchengine-net  \
  --ip 10.11.0.3  \
  -e "path.data=/var/lib/elasticsearch" \
  -e "path.logs=/var/log/elasticsearch" \
  -e "path.repo=/searchengine_backup"  \
  -e "ingest.geoip.downloader.enabled=false" \
  -e "network.host=0.0.0.0" \
  -e "cluster.name=searchengine-cluster" \
  -e "discovery.seed_hosts=searchengine_elasticsearch_node1" \
  -e "http.host=0.0.0.0" \
  -e "ES_JAVA_OPTS=-Xms2g -Xmx2g" \
  -e "node.name=searchengine_elasticsearch_node2" \
  -e "bootstrap.memory_lock=true"  \
  -e "discovery.seed_hosts=searchengine_elasticsearch_node1" \
  -e "cluster.initial_master_nodes=earchengine_elasticsearch_node1,searchengine_elasticsearch_node2,searchengine_elasticsearch_node3" \
  -e "es_api_basic_auth_username=elastic" \
  -e "ELASTIC_PASSWORD=$elastic_password" \
  -e "es_validate_certs=no" \
  -e "es_enable_http_ssl=true" \
  -e "xpack.security.http.ssl.enabled=true" \
  -e "xpack.security.enabled=true" \
  -e "xpack.security.authc.realms.file.file1.order=0" \
  -e "xpack.security.authc.realms.native.native1.order=1" \
  -e "xpack.security.http.ssl.keystore.path=/usr/share/elasticsearch/config/certificates/elastic-ca.p12" \
  -e "xpack.security.http.ssl.truststore.password=$elastic_ca_password" \
  -e "xpack.security.http.ssl.keystore.password=$elastic_ca_password" \
  -e "xpack.security.transport.ssl.enabled=true" \
  -e "xpack.security.transport.ssl.verification_mode=certificate" \
  -e "xpack.security.transport.ssl.keystore.path=/usr/share/elasticsearch/config/certificates/searchengine_elasticsearch_node2/searchengine_elasticsearch_node2.p12" \
  -e "xpack.security.transport.ssl.truststore.path=/usr/share/elasticsearch/config/certificates/searchengine_elasticsearch_node2/searchengine_elasticsearch_node2.p12" \
  -e "xpack.security.transport.ssl.keystore.password=$keystore_password" \
  -e  "xpack.security.transport.ssl.truststore.password=$keystore_password" \
  --ulimit memlock=-1:-1 \
  --name searchengine_elasticsearch_node2 \
  $ELASTICSEARCH_IMAGE
