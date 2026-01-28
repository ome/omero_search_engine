#run beat
cd /searchengine
celery -A  omero_search_engine.api.v1.resources.asyn_queries.clean_query_files  worker  --beat  --loglevel=info
