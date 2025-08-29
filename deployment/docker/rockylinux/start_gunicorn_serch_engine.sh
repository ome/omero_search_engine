#!/bin/sh
NAME="omero_search_engine"
APPPATH=/searchengine
SOCKFILE=/etc/searchengine/sock3 #change this to project_dir/sock (new file will be created)
echo "Starting $NAME as `whoami`"
export PATH="$APPPATH:$PATH"
echo "staring the app"
# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
echo "$RUNDIR"
test -d $RUNDIR || mkdir -p $RUNDIR
LOGS=/etc/searchengine/logs
LOGSDIR=$(dirname $LOGS)
test -d $LOGSDIR || mkdir -p $LOGSDIR
user=$USER
echo "Start Gunicorn ...."
echo "$HOME"
echo $PWD
echo $APPPATH
cd $APPPATH
if [ -z  "$@" ]; then
  exec gunicorn "omero_search_engine:create_app('production')" -b 0.0.0.0:5577 --timeout 0 --name "$NAME"   --bind=unix:$SOCKFILE  --log-file=$LOGSDIR/logs/engine_gunilog.log --access-logfile=$LOGSDIR/logs/engine_access.log -error-logfile=$LOGSDIR/logs/engine_logs/engine_error.log  --workers 8
else
  echo Run with SCRIPT_NAME=$@
  SCRIPT_NAME=/"$@"/ exec gunicorn "omero_search_engine:create_app('production')" -b 0.0.0.0:5577 --timeout 0 --name "$NAME"   --bind=unix:$SOCKFILE  --log-file=$LOGSDIR/logs/engine_gunilog.log --access-logfile=$LOGSDIR/logs/engine_access.log -error-logfile=$LOGSDIR/logs/engine_logs/engine_error.log  --workers 8
fi
