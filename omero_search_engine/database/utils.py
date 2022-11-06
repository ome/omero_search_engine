import os
import sys
import subprocess


def restore_database():
    from omero_search_engine import search_omero_app

    main_dir = os.path.abspath(os.path.dirname(__file__))
    print(main_dir)
    "/mnt/d/Projects/forks/omero_search_engine/omero_search_engine/database" ""
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
        print("===========================================")
        print(restore_command)
        print("===========================================")
        proc = subprocess.Popen(
            restore_command,
            shell=True,
            env={"PGPASSWORD": search_omero_app.config.get("DATABASE_PASSWORD")},
        )
        proc.wait()
    except Exception as e:
        print("Exception happened during dump %s" % (e))
