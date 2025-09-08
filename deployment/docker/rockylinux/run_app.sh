#!/bin/bash
echo "$@"

#test if the configuration file exists, if not it will copy it from the app configuration folder
test -f /etc/searchengine/.app_config.yml || cp /searchengine/configurations/app_config.yml /etc/searchengine/.app_config.yml

#Check the script input
if [[ $@ == celery* ]] ; then
  bash run_celery.sh
elif [[ $@ == run_app* ]] ; then
  url_perfix=${@/run_app/}
  echo using prefix: $url_perfix
  bash start_gunicorn_serch_engine.sh $url_perfix
elif [ -z  "$@" ] || [ "$@" = "run_app" ]; then
  echo "Starting the app"
  bash start_gunicorn_serch_engine.sh
else
  echo "$@"
  export FLASK_APP=commands.py
  flask "$@"
fi
