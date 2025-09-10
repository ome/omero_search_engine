import os
import time

from omero_search_engine.api.v1.resources.asyn_quries.make_celery import make_celery


celery_app, app_config = make_celery("clean_query_files")


@celery_app.task(
    name="clean_query_files",
    bind=True,
)
def clean_query_files(self):
    """
    check quires  files and delete them after the configured time (QUIRES_TTL)

    """

    quires_ttl = app_config.QUIRES_TTL
    quires_files_path = os.path.join(
        app_config.DATA_DUMP_FOLDER, app_config.QUIRES_FOLDER
    )
    quires_ttl_in_sec = time.time() - (quires_ttl * 86400)

    for filename in os.listdir(quires_files_path):
        file_path = os.path.join(quires_files_path, filename)

        if os.path.isdir(file_path):
            continue

        file_last_modifiied = os.path.getmtime(file_path)

        if file_last_modifiied < quires_ttl_in_sec:
            print(f"Deleting: {file_path} ")
            # os.remove(file_path)
