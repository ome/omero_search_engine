#!/bin/bash
echo "$@"

#Check inequality of a variable with a string value

#if [ -z  "$@" ]; then
#echo ("IT iS NULL")

if [ -z  "$@" ] || [ "$@" = "run_app" ]; then
  echo "Windows operating system"
  bash start_gunicorn_serch_engine.sh
else
  python3.9 manage.py "$@"
fi

