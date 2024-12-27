import logging
import json
import requests

from utils import base_url

'''
Call the search engine to determine the available data sources'''

data_source_url = "{base_url}resources/data_sources/".format(
    base_url=base_url)

logging.info(" getting the available data sources")
resp = requests.get(url=data_source_url)
data_sources = json.loads(resp.text)
logging.info("There are %s data sources available, i.e. %s "%(len(data_sources), ', '.join(data_sources)))
'''
"The data source can be linked to queries to return search results from the specified data source.
For example, the user can limit the search results to "bia" data source when querying the searchengine for "Organism" and "homo sapiens"
 '''

key="Organism"
value="homo sapiens"
data_source="bia"
search_url= "{base_url}resources/image/search/?key={key}&value={value}&data_source={data_source}".format(
    base_url=base_url, key=key, value=value, data_source=data_source)

resp = requests.get(url=search_url)
results = json.loads(resp.text)

logging.info("The size of the returned results is %s" %results.get("results").get("size"))
