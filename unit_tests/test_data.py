
sql="select count (id) from image"

valid_and_filters = [{"name": "Organism", "value": "Homo sapiens", "operator": "equals"},
                     {"name": "Antibody Identifier", "value": "CAB034889", "operator": "equals"}]

valid_or_filters = [{"name": "Organism Part", "value": "Prostate", "operator": "equals"},
                    {"name": "Organism Part Identifier", "value": "T-77100", "operator": "equals"}]

not_valid_and_filters = [{"name": "Organism", "value": "Mus musculus"},
               {"name": "Organism Part", "operator": "equals", "value": "Prostate"}]
not_valid_or_filters = []

query = {"query_details":{"and_filters": [{"name": "Organism", "value": "Homo sapiens", "operator": "equals"},
                                {"name": "Antibody Identifier", "value": "CAB034889", "operator": "equals"}],
                "or_filters": [{"name": "Organism Part", "value": "Prostate", "operator": "equals"},
                               {"name": "Organism Part Identifier", "value": "T-77100", "operator": "equals"}]}}