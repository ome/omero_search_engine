Developer documentation
=====================

Clone the code from the project repository using the following command::

    git clone https://github.com/ome/omero_search_engine.git

Then create a Python virtual environment using either venv or conda. Install the packages using the 
:omero_search_engine:`requirements.txt <requirements.txt>` file.

Set up the application configuration as it is explained in the System configuration part inside :omero_search_engine:`configuration_installation.rst <docs/configuration/configuration_installation.rst>`

Run the indexer to index OMERO's data using the following command::

    export FLASK_APP=commands.py
    flask get_index_data_from_database -d datasource_name

Run the application using the following command (for developers)::

    export FLASK_APP=commands.py
    flask run -p 5577

Running the scripts inside the examples folder can be a good starting point.
