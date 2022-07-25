import logging
import requests
import json
import sys

# url to send the query
image_value_search = "/resources/image/searchvalues/"
# search engine url
base_url = "http://127.0.0.1:5577/api/v1/"
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# Get the available attributes for a resource, e.g. image
image_attributes = "/resources/image/keys/"
# Get available values for a resourse attribute
image_key_values = "resources/image/searchvaluesusingkey/"


"""
In case the user needs to know the avilable attributes for images
"""
attrs_url = "{base_url}{image_attributes}".format(
    image_attributes=image_attributes, base_url=base_url
)

resp = requests.get(url=attrs_url)
res = json.loads(resp.text)
# a list contains the available attributes
attributes = res.get("image")
logging.info("Number of the available attributes  for images is %s" % len(attributes))

"""
The user can get the avilable values for the "Organism" attribute and the number of images for each value
"""
key = "Organism"
values_attr_url = "{base_url}{image_key_values}?key={key}".format(
    base_url=base_url, image_key_values=image_key_values, key=key
)
resp = requests.get(url=values_attr_url)
res = json.loads(resp.text)
# a list contains dicts of the available values with the number of images
buckets = res.get("data")
logging.info(
    "Number of the available buckets for attribute %s is %s" % (key, len(buckets))
)
# The first bucket
logging.info("First bucket: %s " % buckets[0])
