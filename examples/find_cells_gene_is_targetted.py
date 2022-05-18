from utils import query_the_search_ending, logging

#Find images of cells where a specific gene was targetted
#Cell line = "HeLa" and Gene Symbol = "KIF11"

#and filters
and_filters=[{"name": "Cell Line", "value": "HeLa", "operator":"equals"},{"name": "Gene Symbol", "value":"KIF11", "operator":"equals"}]
main_attributes=[]
query={"and_filters": and_filters}

recieved_results_data=query_the_search_ending(query, main_attributes)

# Another Example: Cell line="U2OS" and Gene Symbol = "RHEB"

and_filters_2=[{"name": "Cell Line", "value": "U2OS", "operator":"not_equals"},{"name": "Gene Symbol", "value":"RHEB", "operator":"equals"}]
query_2={"and_filters": and_filters_2, "case_sensitive":True}
recieved_results_data_2=query_the_search_ending(query_2, main_attributes)
