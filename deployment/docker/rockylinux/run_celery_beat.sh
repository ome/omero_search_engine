#run beat
cd /searchengine
celery -A  omero_search_engine.api.v1.resources.asyn_quries.clean_quires_files  worker  --beat  --loglevel=info
