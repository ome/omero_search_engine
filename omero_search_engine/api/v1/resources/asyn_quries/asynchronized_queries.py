import os
import redis
import json
import time
from celery import Celery

from elasticsearch import Elasticsearch

from omero_search_engine import search_omero_app

from configurations.configuration import (
    configLooader,
    load_configuration_variables_from_file,
    set_database_connection_variables,
)

app_config = configLooader.get("development")
load_configuration_variables_from_file(app_config)
set_database_connection_variables(app_config)
search_omero_app.config.from_object(app_config)


def load_the_app_config():
    search_omero_app.app_context()
    search_omero_app.app_context().push()
    search_omero_app.app_context()
    search_omero_app.app_context().push()
    ELASTIC_PASSWORD = app_config.ELASTIC_PASSWORD
    es_connector = Elasticsearch(
        app_config.ELASTICSEARCH_URL.split(","),
        verify_certs=app_config.verify_certs,
        request_timeout=130,
        max_retries=20,
        retry_on_timeout=True,
        connections_per_node=10,
        http_auth=("elastic", ELASTIC_PASSWORD),
    )
    search_omero_app.config.database_connectors = app_config.database_connectors
    search_omero_app.config["es_connector"] = es_connector


celery_app = Celery(
    # app.import_name,
    # backend=config.CELERY_RESULT_BACKEND,
    # broker=config.CELERY_BROKER_URL
    "tasks",
    broker="redis://%s:%s/0" % (app_config.REDIS_URL, app_config.REDIS_PORT),
    backend="redis://%s:%s/0" % (app_config.REDIS_URL, app_config.REDIS_PORT),
)


# @celery_app.task(name ="check_queries_queue")
def check_jobs_queue():
    search_omero_app.config.get("REDIS_URL")
    # app_config.REDIS_URL, app_config.REDIS_PORT
    reds = redis.Redis(host=app_config.REDIS_URL, port=app_config.REDIS_PORT, db=0)

    qureies = reds.lrange("celery", 0, -1)

    for query in qureies:
        query_data = json.loads(query)
        if query_data.status == "SUCCESS" or query_data.status == "FAILURE":
            print(query_data["headers"]["id"], query_data["headers"]["task"])


# celery -A synchronized_queries worker -n queries_worker1@%h
# -Q queries --concurrency=1 --loglevel=info


def get_query_file_name(job_id):
    file_path = f"{app_config.DATA_DUMP_FOLDER}{app_config.QUIRES_FOLDER}"
    file_name = os.path.join(file_path, f"{job_id}.csv")
    return file_name


@celery_app.task(bind=True, queue="queries")
def add_query(self, query, data_source, submit_query=False):
    load_the_app_config()
    print(data_source, query)
    time.sleep(1)
    file_name = get_query_file_name(self.request.id)
    print(file_name)
    from omero_search_engine.api.v1.resources.data_dumper import (
        get_all_query_results,
        get_submitquery_results,
    )
    from omero_search_engine.api.v1.resources.utils import write_BBF

    if not submit_query:
        all_results = get_all_query_results(query, {}, data_source, [])
    else:
        all_results = get_submitquery_results(query, data_source)

    if len(all_results) == 0:
        return "The query returned no results"
    write_BBF(results=all_results, file_name=file_name)
    print(len(all_results))
    return {
        "total_results": len(all_results),
        "csv": f"{self.request.id}.csv",
        "parquet": f"{self.request.id}.parquet",
    }


def check_singel_task(task_id):
    from celery.result import AsyncResult

    res = AsyncResult(task_id, app=celery_app)
    print(
        "Task state:", res.state
    )  # e.g. PENDING, SUCCESS, FAILURE, STARTED, RETRY, REVOKED
    if res.successful():
        return {"status": "SUCCESS", "Result": res.result}

    elif res.failed():
        return {"status": "FAILURE", "Result": res.result}
    else:
        return {"status": res.state}


def check_tasks_status():

    r = redis.Redis(host=app_config.REDIS_URL, port=app_config.REDIS_PORT, db=0)
    tasks = r.lrange("task_ids", 0, -1)
    print("Tasks: ", tasks)
    results = []

    for tid in tasks:
        tid = tid.decode()
        res = celery_app.AsyncResult(tid)
        results.append(
            {
                "id": tid,
                "state": res.state,
                "result": res.result if res.ready() else None,
            }
        )

    return results
