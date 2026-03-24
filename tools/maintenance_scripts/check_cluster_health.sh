#!/bin/bash
source vars.txt
curl -k -u elastic:$elastic_password  https://127.0.0.1:9201/_cluster/health?pretty
