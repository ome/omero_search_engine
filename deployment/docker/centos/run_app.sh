#!/bin/bash
echo "$@"

#test if the configuration file exists, if not it will copy it from the app configuration folder
test -f /etc/searchengine/.app_config.yml || cp /searchengine/configurations/app_config.yml /etc/searchengine/.app_config.yml

#Check inequality of a variable with a string value
if [ -z  "$@" ] || [ "$@" = "run_app" ]; then
  echo "Starting the app"
  bash start_gunicorn_serch_engine.sh
else
  echo "$@"
  python3.9 manage.py "$@"
fi

