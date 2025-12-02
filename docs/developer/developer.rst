Developer's documents
=====================

The developer should clone the code from the project repo using the following command::

    git clone https://github.com/ome/omero_search_engine.git

Then they need to create a Python virtual environment variable using either venv or conda and install the packages inside requirements.txt

The developer needs to set up the application configuration as it is explained in the System configuration part inside "docs\configuration\configuration_installation.rst"

After that, they should run the indexer to index Omero's data using the following command::

    python manage.py get_index_data_from_database

The developer can run the application using the following command::

    export FLASK_APP=commands.py
    flask run -p 5577

Running the scripts inside the examples folder can be a good starting point.
