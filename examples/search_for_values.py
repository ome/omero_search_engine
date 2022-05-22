import logging
import requests
import json
import sys

# url to send the query
image_value_search = "/resources/image/searchvalues/"
# searchengine url
base_url = "http://127.0.0.1:5577/api/v1/"
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

'''
If the user needs to search for a value whose attribute is not known e.g 
search to find if diabetes is a part of any attribute values:
'''
search_url="%S/%s%value=diabetes"
search_url="{base_url}{image_value_search}?value={value}".format(base_url=base_url, image_value_search=image_value_search, value="diabetes")
resp = requests.get(url=search_url)
res = json.loads(resp.text)
#total items
logging.info ("total_items: %s"%res.get("total_items"))
logging.info ("total_number: %s"%res.get("total_number"))
#total number of buckets
logging.info ("Number of buckets: %s"%res.get("total_number_of_buckets"))
#data
data=res.get("data")
logging.info ("Number of buckets: %s"%len(data))
total_number_of_images=0
for data_ in data:
    total_number_of_images+=data_.get("Number of images")

logging.info ("Total number of images: %s"%total_number_of_images)
