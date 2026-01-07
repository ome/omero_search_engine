Developer documentation
=====================

Clone the code from the project repo using the following command::

    git clone https://github.com/ome/omero_search_engine.git

Then create a Python virtual environment using either venv or conda and install the packages inside requirements.txt

Set up the application configuration as it is explained in the System configuration part inside :omero_search_engine:`configuration_installation.rst <docs/configurations/configuration_installation.rst>`


After that, run the indexer to index OMERO's data using the following command::

    export FLASK_APP=commands.py
    flask get_index_data_from_database -d datasoource_name

Run the application using the following command (for developers)::

    export FLASK_APP=commands.py
    flask run -p 5577

Running the scripts inside the examples folder can be a good starting point.
