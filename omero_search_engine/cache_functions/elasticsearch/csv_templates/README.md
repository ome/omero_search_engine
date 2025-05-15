The search engine can automatically extract the data from the ``OMERO`` database.
If the data does not come from ``OMERO`` or the data source provider prefers not to share their databases, it is still possible to extract the data from CSV files if it is provided in a specific format.
It is assumed that a project (``study``) contains one or more datasets, and each dataset holds one or more images. 

Each project, dataset, and image needs to have:
* id (``integer``), 
* name (``string``), 
* optionally, a description (``string``). 

Each image should also include the following columns:
* project_id (``integer``)
* project_name (``string``)
* dataset_id (``integer``)
* dataset_name (``string``)
* thumb_url (``URL for the image thumbnail``)
* image_url (``URL for the image viewer or download URL``)
* image_webclient_url (``This attribute should be set if the repository is available via a Web client``)

Additionally, each project, dataset, and image may have one or more associated attributes (e.g. ``organism``, ``cell line``, ``protein name``, etc.)
The two following CSV files ``images_template.csv`` and ``container_template.csv`` should be provided.

The ``convert_to_searchengine_indexer_format`` method ``inside manage.py`` can be used to convert the content of the files to the search engine indexer format.

Alternatively, there is the ``-n`` argument for the ``get_index_data_from_csv_files`` method. If set to True, it will convert the file automatically during the indexing.
