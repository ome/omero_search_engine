import sys
from utils import (
    query_the_search_ending,
    logging
)


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

query_1 = {
    "and_filters": [
        {
            "name": "Organism",
            "value": "Homo sapiens",
            "operator": "equals"
        },
        {
            "name": "Antibody Identifier",
            "value": "CAB034889",
            "operator": "equals"
        },
    ],
    "or_filters": [
        [
            {
                "name": "Organism Part",
                "value": "Prostate",
                "operator": "equals"
            },
            {
                "name": "Organism Part Identifier",
                "value": "T-77100",
                "operator": "equals",
            },
        ]
    ],
}
query_2 = {
    "and_filters": [
        {
            "name": "Organism",
            "value": "Mus musculus",
            "operator": "equals"
        }
    ]
}
main_attributes = []
logging.info("Sending the first query:")
results_1 = query_the_search_ending(query_1, main_attributes)
logging.info("=========================")
logging.info("Sending the second query:")
# It is possible to get the results and exclude one project, e.g. 101
# owner_id': 2

main_attributes_3 = {
    "and_main_attributes": [
        {
            "name": "project_id",
            "value": 101,
            "operator": "equals"
        }
    ]
}
results_4 = query_the_search_ending(query_2, main_attributes_3)
