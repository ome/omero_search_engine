* The user must change the file path for each data source.
* Next, the user should run the script to read the files containing the provided data.
* Each script will generate two files: one for the projects and one for the images.
* These files will be in a format that can be indexed by the search engine.
* The data source should be added to the search engine before running the indexer.
This can be achieved using a method in manage.py. For example, you can use the following command:

        python manage.py set_data_source_files -d csv -n bia

* Then the indexer can push the data source to Elasticsearch by running a method in manage.py. This should run  for each resource

        python manage get_index_data_from_csv_files -s bia -f /path/to/bia_images.csv -r image
        python manage get_index_data_from_csv_files -s bia -f /path/to/bia_projects.csv -r project
