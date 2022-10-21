import os
from omero_search_engine import search_omero_app

def get_backup_repository(es):
    Backup_folder = search_omero_app.config.get("ELASTICSEARCH_BACKUP_FOLDER")
    repository_folder=os.path.join(Backup_folder, "backup_data")
    search_omero_app.logger.info("Backup folder: %s" % repository_folder)
    snap_body = {
        "type": "fs",
        "settings": {
            "location": repository_folder
        }
    }
    es.snapshot.create_repository(repository='repository', body=snap_body)

def backup_indices_data():
    es = search_omero_app.config.get("es_connector")
    get_backup_repository(es)
    all_indexes = es.indices.get("*")
    indx=[]
    for index in all_indexes:
        indx.append(index)

    index_body = {
        "indices": ','.join(indx)
    }
    #try to delete the snapshot if exist
    try:
        es.snapshot.delete(repository='repository', snapshot='searchengine_snapshot')
    except:
        pass
    res=es.snapshot.create(repository='repository', snapshot='searchengine_snapshot', body=index_body)
    search_omero_app.logger.info("Backup data: %s" % str(res))


def restore_indices_data():
    es = search_omero_app.config.get("es_connector")
    get_backup_repository(es)
    res=es.snapshot.restore(repository='repository', snapshot='searchengine_snapshot')
    search_omero_app.logger.info("restore data: %s" % str(res))
