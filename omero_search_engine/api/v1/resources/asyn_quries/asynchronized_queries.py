import copy
import os
import redis
import json
import shutil

from elasticsearch import Elasticsearch

from omero_search_engine import search_omero_app

from omero_search_engine.api.v1.resources.asyn_quries.make_celery import make_celery

celery_app, app_config = make_celery()
search_omero_app.config.from_object(app_config)
r = redis.Redis(host=app_config.REDIS_URL, port=app_config.REDIS_PORT, db=0)


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
    search_omero_app.config["PAGE_SIZE"] = search_omero_app.config.get("MAX_PAGE_SIZE")


def check_jobs_queue():
    search_omero_app.config.get("REDIS_URL")
    # app_config.REDIS_URL, app_config.REDIS_PORT
    reds = redis.Redis(host=app_config.REDIS_URL, port=app_config.REDIS_PORT, db=0)

    queries = reds.lrange("celery", 0, -1)

    for query in queries:
        query_data = json.loads(query)
        if query_data.status == "SUCCESS" or query_data.status == "FAILURE":
            print(query_data["headers"]["id"], query_data["headers"]["task"])


def get_query_file_name(job_id):
    file_path = f"{app_config.DATA_DUMP_FOLDER}{app_config.QUIRES_FOLDER}"
    file_name = os.path.join(file_path, f"{job_id}.csv")
    return file_path, file_name


@celery_app.task(bind=True, queue="queries")
def add_query(self, query, data_source, submit_query=False):
    load_the_app_config()
    task_id = self.request.id

    file_path, file_name = get_query_file_name(self.request.id)
    folder_name = os.path.join(file_path, task_id)

    from omero_search_engine.api.v1.resources.data_dumper import (
        get_all_query_results,
        get_submitquery_results,
    )
    from omero_search_engine.api.v1.resources.utils import (
        write_BBF,
        write_csv_parquet_from_folder,
    )

    query_details = copy.deepcopy(query.get("query_details"))

    if not submit_query:
        all_results = get_all_query_results(query, {}, data_source, [])
    else:
        os.mkdir(folder_name)
        total = get_submitquery_results(query, data_source, folder_name)

    if total == 0:
        return "The query returned no results"
    if not submit_query:
        write_BBF(results=all_results, file_name=file_name)
        results = {
            "total_results": len(all_results),
            "csv": f"{self.request.id}.csv",
            "parquet": f"{self.request.id}.parquet",
            "query": query_details,
            "data_source": data_source,
        }
    else:
        write_csv_parquet_from_folder(folder_name, file_name)
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)

        results = {
            "total_results": total,
            "csv": f"{self.request.id}.csv",
            "parquet": f"{self.request.id}.parquet",
            "query": query_details,
            "data_source": data_source,
        }
    r.rpush("tasks_ids", task_id)
    return results


def check_single_task(task_id):
    from celery.result import AsyncResult

    res = AsyncResult(task_id, app=celery_app)
    print(
        "Task state:", res.state
    )  # e.g. PENDING, SUCCESS, FAILURE, STARTED, RETRY, REVOKED
    if res.successful():
        return {"status": "SUCCESS", "Result": res.result}

    elif res.failed():
        return {"status": "FAILURE"}
    else:
        return {"status": res.state}


def check_tasks_status(query=None, data_source=None):
    from deepdiff import DeepDiff

    # r = redis.Redis(host=app_config.REDIS_URL, port=app_config.REDIS_PORT, db=0)
    tasks = r.lrange("tasks_ids", 0, -1)
    results = []
    for tid in tasks:
        tid = tid.decode()
        res = celery_app.AsyncResult(tid)
        if not query:
            results.append(
                {
                    "id": tid,
                    "state": res.state,
                    "result": res.result if res.ready() else None,
                }
            )
        elif res.result and res.result.get("query"):
            diff = DeepDiff(
                query.get("query_details"), res.result.get("query"), ignore_order=True
            )
            if (
                len(diff) == 0
                and data_source
                and res.result.get("data_source")
                and res.result.get("data_source").lower() == data_source.lower()
            ) or (
                len(diff) == 0 and not data_source and not res.result.get("data_source")
            ):
                return tid
    if not query:
        return results
    else:
        return None
