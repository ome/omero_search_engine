
import sys
from utils import query_the_search_ending, logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

'''
Find images of cells treated with specific drug Cell Type = "induced pluripotent stem cell" and compound = "fibronectin"
The and query clauses should be as follows:
'''

recieved_results_data=[]
and_filters= [
    {
        "name": "Cell Type",
        "value": "induced pluripotent stem cell",
        "operator": "equals",
        "resource": "image"
    },
    {
        "name": "Compound Name",
        "value": "fibronectin",
        "operator": "equals",
        "resource": "image"
    }
]

recieved_results_data=[]
'''
If we need to restrict the results to a specific owner,
we can use the main attribute that can be used to add to the search terms like owner id, group id etc.
'''
main_attributes={"and_main_attributes":[ {"name":"group_id","value": 3, "operator":"equals"}, {"name":"owner_id","value": 2, "operator":"equals"}]}

query = {"and_filters":and_filters}

results=query_the_search_ending(query,main_attributes)
