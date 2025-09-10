
from celery import Celery

from configurations.configuration import (
    configLooader,
    load_configuration_variables_from_file,
    set_database_connection_variables,
)


def make_celery(beat=None):
    app_config = configLooader.get("development")
    load_configuration_variables_from_file(app_config)
    set_database_connection_variables(app_config)

    celery_app = Celery(
        # app.import_name,
        # backend=config.CELERY_RESULT_BACKEND,
        # broker=config.CELERY_BROKER_URL
        "tasks",
        broker="redis://%s:%s/0" % (app_config.REDIS_URL, app_config.REDIS_PORT),
        backend="redis://%s:%s/0" % (app_config.REDIS_URL, app_config.REDIS_PORT),
    )
    if beat:
        from datetime import timedelta

        celery_app.conf.beat_schedule = {
            f"{beat}-every-hour": {
                "task": beat,
                #"schedule": 30.0,
                'schedule': timedelta(hours=1),
                "args": ()
            }
        }
    return celery_app, app_config
