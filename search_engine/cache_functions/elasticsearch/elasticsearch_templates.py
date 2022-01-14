'''
Template to be used with project, dataset, well, plate, screen.
It is derived from some Omero tables depending on the resource.
For example for the project, it combines project, projectannotationlink and annotation_mapvalue.
'''
non_image_template={
  "mappings": {
    "properties": {
      "doc_type": {
        "type": "keyword"
    },
    "id": {
      "type": "long"
    },
    "name": {
      "type": "text",
            "fields": {
                "keyvalue": {
                    "type": "keyword"
                }
            }
    },
        "owner": {
            "type": "long"
        },

        "group_id": {
            "type": "long"
        },
        "permissions": {
            "type": "long"
        },
      "key_values": {
        "type": "nested",
          "properties": {
            "name": {
                "type":"text",
                  "fields":{
                      "keyword":{
                        "type":"keyword"
                     }
             }
         },
            "value": {
              "type": "text",
                "fields": {
                 "keyvalue": {
                    "type": "keyword"
              }
            }
          },
              "index":{
                "type": "short"
              }
        }
      }
    }
  }
}

'''
image_template is derived from  Omero tables into a single Elasticsearch index (image, annoation_mapvalue, imageannotationlink, 
project, dataset, well, plate and screen to generate a single index.
'''
image_template={
  "mappings": {
    "properties": {
      "doc_type": {
        "type": "keyword"
    },
    "id": {
      "type": "long"
    },
        "experiment": {
            "type": "long"
        },
        "owner": {
            "type": "long"
        },
        "group_id": {
            "type": "long"
        },
        "permissions": {
            "type": "long"
        },
        "project_id": {
            "type": "long"
        },
        "dataset_id": {
            "type": "long"
        },
        "screen_id": {
            "type": "long"
        },
        "plate_id": {
            "type": "long"
        },
        "well_id": {
            "type": "long"
        },
        "wellsample_id": {
            "type": "long"
        },
    "name": {
      "type": "text",
        "fields": {
              "keyvalue": {
                  "type": "keyword"
                      }
            }
    },
        "project_name": {
            "type": "text",
            "fields": {
                "keyvalue": {
                    "type": "keyword"
                }
            }
        },
        "dataset_name": {
            "type": "text",
            "fields": {
                "keyvalue": {
                    "type": "keyword"
                }
            }
        },
        "plate_name": {
            "type": "text",
            "fields": {
                "keyvalue": {
                    "type": "keyword"
                }
            }
        },
        "screen_name": {
            "type": "text",
            "fields": {
                "keyvalue": {
                    "type": "keyword"
                }
            }
        },

      "key_values": {
        "type": "nested",
          "properties": {
            "name": {
                "type":"text",
                  "fields":{
                      "keyword":{
                        "type":"keyword"
                 }
             }
         },
            "value": {
              "type": "text",
                "fields": {
                 "keyvalue": {
                    "type": "keyword"
              }
            }
          },
           "index":{
                "type": "short"
              }
        }
      }
    }
  }
}