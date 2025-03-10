The search engine can automatically extract the data from the OMERO database.
If the data does not come from ''OMERO'' or the data source provider prefers not to share their databases, it is still possible to extract the data from ccs files if it is provided in a specific format.
It is assumed that a project (study) contains one or more datasets, and each datasets holds one or more images. 

Each project, dataset, and image needs to have:
* id (``integer``), 
* name (``string``), 
* optionally, a description (``string``). 

Each image should also include the following columns:
* project_id (``integer``)
* project_name (``string``)
* dataset_id (``integer``)
* dataset_name (``string``)

Additionally, each project, dataset, and image may have one or more associated attributes (e.g. ``organism``, ``cell line``, ``protein name``, etc.)
There are two csv files should be provided, i.e. images_template.csv and container_template.csv.

The ``convert_to_searchengine_indexer_format`` method ``inside manage.py`` can be used to convert these file to search engine indexer foramt.

Alternatively, there is the ``-n`` argument for the ``get_index_data_from_csv_files`` method. If set to True, it will convert the file automatically during the indexing.
