import os
import sys
import subprocess


def restore_database():
    """
    restote the database from a database dump file
    """
    from omero_search_engine import search_omero_app

    main_dir = os.path.abspath(os.path.dirname(__file__))
    mm = main_dir.replace("omero_search_engine/database", "")
    sys.path.append(mm)
    dat_file_name = os.path.join(
        mm, "app_data/omero.pgdump"
    )  # app_data/omero_backup.tar")
    restore_command = "psql --username %s  --host %s --port %s -d %s -f  %s" % (
        search_omero_app.config.get("DATABASE_USER"),
        search_omero_app.config.get("DATABASE_SERVER_URI"),
        search_omero_app.config.get("DATABASE_PORT"),
        search_omero_app.config.get("DATABASE_NAME"),
        dat_file_name,
    )
    try:
        proc = subprocess.Popen(
            restore_command,
            shell=True,
            env={"PGPASSWORD": search_omero_app.config.get("DATABASE_PASSWORD")},
        )
        proc.wait()
    except Exception as e:
        print("Exception happened during dump %s" % (e))
