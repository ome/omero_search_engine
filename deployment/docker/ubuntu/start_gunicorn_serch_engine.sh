#!/bin/sh
NAME="omero_search"
PYTHONPATH=/usr/local/bin
APPPATH=/searchengine
SOCKFILE=$HOME/sock #change this to project_dir/sock (new file will be created)
echo "Starting $NAME as `whoami`"
export PATH="$PYTHONPATH:$PATH"
export PATH="$APPPATH:$PATH"
echo "staring the app"
# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
echo "$RUNDIR"
test -d $RUNDIR || mkdir -p $RUNDIR
user=$USER
echo "Start Gunicorn ...."
#exec $PYTHONPATH/gunicorn "omero_search_engine:create_app('production')" -b 0.0.0.0:5569 --timeout 0 --name "$NAME"   --bind=unix:$SOCKFILE  --log-file=$HOME/logs/engine_gunilog.log --access-logfile=$HOME/logs/engine_access.log -error-logfile=$HOME/engine_logs/error.log  --workers 2
exec gunicorn "omero_search_engine:create_app('production')" -b 0.0.0.0:5569 --timeout 0 --name "$NAME"   --bind=unix:$SOCKFILE  --log-file=/etc/searchengine/logs/engine_gunilog.log --access-logfile=/etc/searchengine/logs/engine_access.log -error-logfile=/etc/searchengine//engine_logs/error.log  --workers 2
