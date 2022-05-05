User Guide
===========
A search engine is a tool that is used to search the metadata (key/value pairs). ELasticsearch search engine (https://www.elastic.co/) is utilized to perform the search
Special indices are created to facilitate querying the data and searching the values. It supports almost all SQL like search operators.
It is fast, scalable and future proof as it is possible to deploy more than one Elastic search node to perform the search efficiency

* Get all the available resources (image, project, plate, etc.) and their keys (names) using the following URL:

    * /api/v1/resources/all/keys

 * It will return a JSON string that contains the resources and all available keywords (names) for all the resources, i.e. image, project, plate, well, and well sample.

* If the user wants to know the available values for a keyword in a particular resource, he can use this URL:

    * /api/v1/resources/{resource}/getannotationvalueskey/?key={keyword}

* for example, the following URL will return all the available values for the Organism keyword for the image.
    * /api/v1/resources/image/getannotationvalueskey/?key=Organism

* The query is a JSON string that contains two parts:
    * query_details which has two parts:
    * and_filters, a list of dict, the dict take this form:
        {"name": {keyword}, "value": {value}, "operator": {operator}
        * keyword, the name of the attribute to search its value
        * value is the value for which the attribute should be searched; the search is depending on the operator
        * operator is the search criteria which is used to search the keyword value; it can be either:

            * equals, not_equals, contains (like), not_contains (not like), lt (<), gt (>), lte (<=), and gte (>=)

        * The user can use a combination of keywords and values and operators in  his search
        * Example of and_filters, the following filter search the data using these conditions: (Organism ="'Mus musculus" and "Organism Part" ="Prostate")
          * [{"name":"Organism", "value": "Mus musculus", 'operator': 'equals'},{"name":"Organism Part", "operator":"equals", "value": "Prostate"}]

    * or_filters, is a list that also contains dicts, each of them has the same format as in and_filters
        * it searches the data to satisfy at least one condition in this list
            * The dict has the same format as the one inside and_filters
            * Example of or filters, the following example queries the database with these conditions (Organism Part = "Prostate" OR Organism Part Identifier = "T-77100")
            * [{"name": "Organism Part", "value": "Prostate", "operator": "equals"},{"name": "Organism Part Identifier", "value": "T-77100", "operator": "equals"}]

    * main_attributes allows the user to search using one or more of
        * project _id, dataset_id, owner_id, group_id, owner_id, etc.
        * It supports two operators, equals and not_equals.
        * Hence, it is possible to search one project instead of all the projects or exclude one project from the search
        * Also, it is possible to search the results which belong to a specific user or a group.
        * The dict has the same format as the one inside and_filters
        * It supports also and (and_main_attributes) and or (or_main_attributes) filters
        * For example, the following query will limit the search to the project with Id =501 (HPA)
            * {"and_main_attributes": [{"name": "project_id", "value":501, "operator": "equals"}]}

* The user can combine one or more of these parts
    * Example of a query to be sent to the search engine, it will search project with id = 501 with the following criterias:
        * Organism ="Homo sapiens" and "Antibody Identifier" ="CAB034889" and (Organism Part = "Prostate" OR Organism Part Identifier = "T-77100")
        * query = {"and_filters": [{"name": "Organism", "value": "Homo sapiens", "operator": "equals"}, {"name": "Antibody Identifier", "value": "CAB034889", "operator": "equals"}], "or_filters": [{"name": "Organism Part", "value": "Prostate", "operator": "equals"}, {"name": "Organism Part Identifier", "value": "T-77100", "operator": "equals"}]}
        * main_attributes_query={"and_main_attributes":[{"name": "project_id", "value":501, "operator": "equals"}]}
        * query_details = {"query": {"query_details": query,"main_attributes":main_attributes}}

