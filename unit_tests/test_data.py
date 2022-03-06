#sql="select count (id) from image"
sql="select current_database()"
valid_and_filters = [{"name": "Organism", "value": "Homo sapiens", "operator": "equals"},
                     {"name": "Antibody Identifier", "value": "CAB034889", "operator": "equals"}]

valid_or_filters = [[{"name": "Organism Part", "value": "Prostate", "operator": "equals"},
                    {"name": "Organism Part Identifier", "value": "T-77100", "operator": "equals"}]]

not_valid_and_filters = [{"name": "Organism", "value": "Mus musculus"},
               {"name": "Organism Part", "operator": "equals", "value": "Prostate"}]
not_valid_or_filters = []

#query = {"query_details":{"and_filters": [{"name": "Organism", "value": "Homo sapiens", "operator": "equals", 'resource': "image"},
#                                {"name": "Antibody Identifier", "value": "CAB034889", "operator": "equals", "resource": "image"}],
#                "or_filters": [{"name": "Organism Part", "value": "Prostate", "operator": "equals", "resource": "image"},
#                               {"name": "Organism Part Identifier", "value": "T-77100", "operator": "equals", "resource": "image"}]}}

query={"query_details":{"and_filters":[]}}
