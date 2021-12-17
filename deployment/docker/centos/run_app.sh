#!/bin/bash
echo "$@"

#check args and run the docker accoringly
#if no arguments or argument == run_app, then it will start the gunicorn
#otherwise it will run manage.py with the provided arguemts

if [ -z  "$@" ] || [ "$@" = "run_app" ]; then
  echo "Windows operating system"
  bash start_gunicorn_serch_engine.sh
else
  python3.9 manage.py "$@"
fi

