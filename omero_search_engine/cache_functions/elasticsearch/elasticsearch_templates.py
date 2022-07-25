"""
Template to be used with project, dataset, well, plate, screen.
It is derived from some Omero tables depending on the resource.
For example for the project, it combines project,
projectannotationlink and annotation_mapvalue.
"""
non_image_template = {
    "settings": {
        "analysis": {
            "normalizer": {
                "valuesnormalizer": {"type": "custom", "filter": ["lowercase"]}
            }
        }
    },
    "mappings": {
        "properties": {
            "doc_type": {"type": "keyword"},
            "id": {"type": "long"},
            "name": {
                "type": "text",
                "fields": {"keyvalue": {"type": "keyword"}},
            },  # noqa
            "owner_id": {"type": "long"},
            "group_id": {"type": "long"},
            "permissions": {"type": "long"},
            "key_values": {
                "type": "nested",
                "properties": {
                    "name": {
                        "type": "text",
                        "fields": {
                            "keynamenormalize": {
                                "type": "keyword",
                                "normalizer": "valuesnormalizer",
                            },
                            "keyword": {"type": "keyword"},
                        },
                    },
                    "value": {
                        "type": "text",
                        "fields": {
                            "keyvaluenormalize": {
                                "type": "keyword",
                                "normalizer": "valuesnormalizer",
                            },
                            "keyvalue": {"type": "keyword"},
                        },
                    },
                    "index": {"type": "short"},
                },
            },
        }
    },
}

"""
image_template is derived from  Omero tables into
a single Elasticsearch index (image, annoation_mapvalue,
imageannotationlink, project, dataset, well, plate and screen
to generate a single index.
"""
image_template = {
    "settings": {
        "analysis": {
            "normalizer": {
                "valuesnormalizer": {"type": "custom", "filter": ["lowercase"]}  # noqa
            }
        }
    },
    "mappings": {
        "properties": {
            "doc_type": {"type": "keyword"},
            "id": {"type": "long"},
            "experiment": {"type": "long"},
            "owner_id": {"type": "long"},
            "group_id": {"type": "long"},
            "permissions": {"type": "long"},
            "project_id": {"type": "long"},
            "dataset_id": {"type": "long"},
            "screen_id": {"type": "long"},
            "plate_id": {"type": "long"},
            "well_id": {"type": "long"},
            "wellsample_id": {"type": "long"},
            "name": {
                "type": "text",
                "fields": {"keyvalue": {"type": "keyword"}},
            },  # noqa
            "project_name": {
                "type": "text",
                "fields": {"keyvalue": {"type": "keyword"}},
            },
            "dataset_name": {
                "type": "text",
                "fields": {"keyvalue": {"type": "keyword"}},
            },
            "plate_name": {
                "type": "text",
                "fields": {"keyvalue": {"type": "keyword"}},
            },  # noqa
            "screen_name": {
                "type": "text",
                "fields": {"keyvalue": {"type": "keyword"}},
            },
            "key_values": {
                "type": "nested",
                "properties": {
                    "name": {
                        "type": "text",
                        "fields": {
                            "keynamenormalize": {
                                "type": "keyword",
                                "normalizer": "valuesnormalizer",
                            },
                            "keyword": {"type": "keyword"},
                        },
                    },
                    "value": {
                        "type": "text",
                        "fields": {
                            "keyvaluenormalize": {
                                "type": "keyword",
                                "normalizer": "valuesnormalizer",
                            },
                            "keyvalue": {"type": "keyword"},
                        },
                    },
                    "index": {"type": "short"},
                },
            },
        }
    },
}

"""
Template rebresents a bucket in a resource, i.e. key and value
and the total number of values (number of images)
"""
key_values_resource_cache_template = {
    "mappings": {
        "properties": {"doc_type": {"type": "keyword"}},
        "resource": {
            "type": "text",
            "fields": {"keyresource": {"type": "keyword"}},
        },  # noqa
        "name": {"type": "text", "fields": {"keyname": {"type": "keyword"}}},
    }
}

key_value_buckets_info_template = {
    "settings": {
        "analysis": {
            "normalizer": {
                "valuesnormalizer": {"type": "custom", "filter": ["lowercase"]}
            }
        }
    },
    "mappings": {
        "properties": {
            "doc_type": {"type": "keyword"},
            "id": {
                "type": "keyword",
            },
            "resource": {
                "type": "text",
                "fields": {
                    "keyresource": {"type": "keyword"},
                    "keyresourcenormalize": {
                        "type": "keyword",
                        "normalizer": "valuesnormalizer",
                    },
                },
            },
            "Attribute": {
                "type": "text",
                "fields": {
                    "keyname": {"type": "keyword"},
                    "keyrnamenormalize": {
                        "type": "keyword",
                        "normalizer": "valuesnormalizer",
                    },
                },
            },
            "Value": {
                "type": "text",
                "fields": {
                    "keyvalue": {"type": "keyword"},
                    "keyvaluenormalize": {
                        "type": "keyword",
                        "normalizer": "valuesnormalizer",
                    },
                },
            },
            "items_in_the_bucket": {"type": "long"},
            "total_buckets": {"type": "long"},
            "total_items": {"type": "long"},
            "total_items_in_saved_buckets": {"type": "long"},
        }
    },
}

"""
Template contains list of attributes for each resource"""

key_values_resource_cache_template = {
    "mappings": {
        "properties": {
            "doc_type": {"type": "keyword"},
            "resource": {
                "type": "text",
                "fields": {"keyresource": {"type": "keyword"}},
            },
            "name": {
                "type": "text",
                "fields": {"keyname": {"type": "keyword"}},
            },  # noqa
            "resourcename": {
                "type": "text",
                "fields": {"keyresourcename": {"type": "keyword"}},
            },
        }
    }
}
