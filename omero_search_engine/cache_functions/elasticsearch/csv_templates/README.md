The search engine can automatically extract the data from the OMERO database.
If the data does not come from OMERO or the data source provider prefers not to share their databases, it is still possible to extract the data from ccs files if it is provided in a specific format.
It is assumed that a project (study) contains one or more datasets, and each datasets holds one or more images. 
Each project, dataset, and image have an ID (integer), a name (string), and optionally, a description (string). 
Additionally, each project, dataset, and image may have one or more associated attributes (e.g. organism, cell line, protein name, etc.)
There are two csv files should be provided, i.e. images_template.csv and container_template.csv.
