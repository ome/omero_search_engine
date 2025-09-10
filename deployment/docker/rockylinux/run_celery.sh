cd /searchengine
celery -A  omero_search_engine.api.v1.resources.asyn_quries.asynchronized_queries  worker  -Q queries --hostname=worker1@%h  --loglevel=info
