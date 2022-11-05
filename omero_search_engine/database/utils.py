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
    create_database_command = (
        "psql --username %s --host %s -c 'CREATE DATABASE %s' "
        % (
            search_omero_app.config.get("DATABASE_USER"),
            search_omero_app.config.get("DATABASE_SERVER_URI"),
            search_omero_app.config.get("DATABASE_NAME"),
        )
    )

    drop_database_command = "psql --username %s --host %s -c 'DROP DATABASE %s' " % (
        search_omero_app.config.get("DATABASE_USER"),
        search_omero_app.config.get("DATABASE_SERVER_URI"),
        search_omero_app.config.get("DATABASE_NAME"),
    )
    print(create_database_command)
    print("###################################")
    try:
        proc = subprocess.Popen(
            drop_database_command,
            shell=True,
            env={"PGPASSWORD": search_omero_app.config.get("DATABASE_PASSWORD")},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = proc.communicate()

        print("delete output : ", out, err)

        proc = subprocess.Popen(
            create_database_command,
            shell=True,
            env={"PGPASSWORD": search_omero_app.config.get("DATABASE_PASSWORD")},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = proc.communicate()

        print("create output: ", out, err)

    except Exception as e:
        print(e)
        return

    restore_command = "pg_restore -W -c --host %s -U %s -d %s -v %s " % (
        search_omero_app.config.get("DATABASE_SERVER_URI"),
        search_omero_app.config.get("DATABASE_USER"),
        search_omero_app.config.get("DATABASE_NAME"),
        dat_file_name,
    )
    restore_command = "psql --username khaled --host %s -d %s -f  %s" % (
        search_omero_app.config.get("DATABASE_SERVER_URI"),
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
