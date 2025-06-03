source vars.txt
echo  $SEARCHENGINE_IMAGE
curl  -X GET -u $USER_NAME:$PASSWORD https://192.168.10.38:9201/_tasks/$TASK_ID  --insecure
