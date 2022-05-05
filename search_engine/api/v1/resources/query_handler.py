from search_engine import search_omero_app
from  search_engine.api.v1.resources.urls import search_resource_annotation, get_resource_names
import json
from jsonschema import validate, ValidationError, SchemaError, RefResolver
from os.path import abspath,dirname
from pathlib import Path

mapping_names={"project":{"Name (IDR number)":"name"},"screen":{"Name (IDR number)":"name"}}
class QueryItem (object):
    def __init__ (self, filter):
        '''
        define query and adjust resource if it is needed
        Args:
            resource:
            attribute_name:
            attribute_value:
            operator:
        '''
        self.resource=filter.get("resource")
        self.name=filter.get("name")
        self.value=filter.get("value")
        self.operator=filter.get("operator")
        self.query_type="keyvalue"
        self.adjust_resource()
        #it will be used when buildingthe query

    def adjust_resource(self):
        if self.resource in mapping_names :
            if mapping_names[self.resource].get(self.name):
                pr_names=get_resource_names (self.resource)
                if not self.value in pr_names:
                    ##Assuming that the names is either project or screen
                    self.resource="screen"
                self.name=mapping_names[self.resource].get(self.name)
                self.query_type="main_attribute"

class QueryGroup(object):
    '''
    check query list and check it is has  multiple resource queries
    '''
    def __init__ (self, group_type):
        self.query_list=[]
        self.group_type = group_type
        self.resourses_query = {}
        self.main_attribute={}
        self.resource=[]

    def add_query(self,query):
        self.query_list.append(query)

    def divide_filter(self):
        for filter in self.query_list:
            if not filter.resource in self.resourses_query:
                flist=[]
                self.resourses_query[filter.resource]=flist
            else:
                flist=self.resourses_query[filter.resource]
            flist.append(filter)
            self.resource=self.resourses_query.keys()


    def adjust_query_main_attributes(self):
        to_be_removed= {}
        for resource, queries in self.resourses_query.items():
            for query in queries:
                if query.query_type=="main_attribute":
                    if not resource in self.main_attribute:
                        self.main_attribute[resource]={"and_main_attributes":[query]}
                    else:
                        self.main_attribute[resource]["and_main_attributes"].append(query)
                    if resource not in to_be_removed:
                        to_be_removed[resource]=[query]
                    else:
                        to_be_removed[resource].append(query)

        for resource, queries in to_be_removed.items():
            for query in queries:
                self.resourses_query[resource].remove(query)



class QueryRunner(object, ):
    def __init__(self,and_query_group,  or_query_group, case_sensitive,  bookmark, raw_elasticsearch_query,columns_def, return_columns):
        self.or_query_group=or_query_group
        self.and_query_group=and_query_group
        self.case_sensitive=case_sensitive
        self.bookmark=bookmark
        self.columns_def=columns_def
        self.raw_elasticsearch_query=raw_elasticsearch_query
        self.image_query={}
        self.additional_image_conds=[]
        self.return_columns=return_columns

    def get_iameg_non_image_query(self):
        has_main=False
        res=None
        or_queries=[]
        if len (self.and_query_group.query_list)==0:
            for or_grp_ in self.or_query_group:
                for resource, or_grp in or_grp_.resourses_query.items():
                    or_queries.append(or_grp_.resourses_query[resource])
            self.image_query["or_filters"] = or_queries
        else:
            for resource, and_query in self.and_query_group.resourses_query.items():
                if resource=="image":
                    or_queries=[]
                    self.image_query["and_filters"]=and_query
                    self.image_query["or_filters"] = or_queries
                    if self.and_query_group.main_attribute.get(resource):
                        self.image_query["main_attribute"]=self.and_query_group.main_attribute.get(resource)
                    else:
                        self.image_query["main_attribute"] =[]
                    for or_grp in self.or_query_group:
                        if resource in or_grp.resourses_query:
                            or_queries.append(or_grp.resourses_query[resource])
                else:
                    has_main=True
                    query={}
                    query["and_filters"]=and_query
                    or_queries = []
                    query["or_filters"] = or_queries
                    for or_grp in self.or_query_group:
                        if resource in or_grp.resourses_query:
                            or_queries.append(or_grp.resourses_query[resource])
                    if self.and_query_group.main_attribute.get(resource):
                        query["main_attribute"]=self.and_query_group.main_attribute.get(resource)
                    else:
                        query["main_attribute"]= {}
                    res=self.run_query(query, resource)
                    new_cond=get_ids(res, resource)
                    if new_cond:
                        self.additional_image_conds.append(new_cond)
                    else:
                        return {"Error": "Your query returns no results"}
        #for add_query in self.additional_image_conds:

        if len(self.additional_image_conds)==0 and has_main:
            return {"Error" : "Your query returns no results"}
        self.image_query["main_attribute"]={"or_main_attributes": self.additional_image_conds}
        return  self.run_query(self.image_query, "image")

    def run_query(self, query_, resource):
        main_attributes= {}
        query={"and_filters":[],"or_filters":[]}

        if query_.get("and_filters"):
            for qu in query_.get("and_filters"):
                query.get("and_filters").append(qu.__dict__)

        if query_.get("or_filters"):
            for qu_ in query_.get("or_filters"):
                qq=[]
                query.get("or_filters").append(qq)
                for qu in qu_:
                    qq.append(qu.__dict__)

        if query_.get("main_attribute"):
            ss=[]
            #this should be checked again ........
            for key, qu in query_.get("main_attribute").items():
                if type(qu)!=list:
                    ss.append(qu.__dict__)
                else:
                    for qu__ in qu:
                        bb=[]
                        ss.append(bb)
                        if isinstance(qu__,QueryItem):
                            bb.append(qu__.__dict__)
                        elif isinstance(qu__, list):
                                for qu_ in qu__:
                                    bb.append(qu_.__dict__)
                        else:
                            return {"Error": "M"}
            main_attributes[key]=ss
        query["case_sensitive"]=self.case_sensitive
        res=seracrh_query(query, resource, self.bookmark, self.raw_elasticsearch_query, main_attributes)
        if resource != "image":
            return res
        elif self.return_columns:
            return process_search_results(res, "image", self.columns_def)
        else:
            return res

def seracrh_query(query,resource,bookmark,raw_elasticsearch_query, main_attributes=None):
    search_omero_app.logger.info(("%s, %s") % (resource, query))
    if not main_attributes:
        q_data = {"query": {'query_details': query}}
    elif resource=="image":
        q_data = {"query": {'query_details': query,"main_attributes":   main_attributes}}
    else:
        q_data = {"query": {'query_details': query , "main_attributes": main_attributes}}
    try:
        if bookmark:
            q_data["bookmark"] =bookmark
            q_data["raw_elasticsearch_query"] = raw_elasticsearch_query
            ress=search_resource_annotation(resource, q_data.get("query"), raw_elasticsearch_query=raw_elasticsearch_query,
                                       page=query.get("page"), bookmark=bookmark)
        else:
            ress=search_resource_annotation(resource, q_data.get("query"))
        ress["Error"] = "none"
        return ress
    except Exception as ex:
        search_omero_app.logger.info("Error: " + str(ex))
        return {"Error": "Something went wrong, please try later. If you have this error again, please contact the system administrator."}

def get_ids(results, resource):
    ids=[]
    if results.get("results") and results.get("results").get("results"):
        for item in results["results"]["results"]:
            qur_item={}
            #ids.append(qur_item)
            qur_item["name"]="{resource}_id".format(resource=resource)
            qur_item["value"]=item["id"]
            qur_item["operator"]="equals"
            qur_item["resource"] = resource
            qur_item_=QueryItem(qur_item)
            ids.append(qur_item_)
        return ids
    return None

def process_search_results(results, resource, columns_def):
    returned_results={}

    if not results.get("results") or len(results["results"])==0:
        returned_results["Error"] = "Your query returns no results"
        return returned_results
    cols=[]
    values=[]
    urls = {"image": search_omero_app.config.get("IMAGE_URL"),
            "project":search_omero_app.config.get("PROJECT_URL"),
            "screen": search_omero_app.config.get("SCREEN_URL")}
    extend_url=urls.get(resource)
    if not extend_url:
        extend_url = search_omero_app.config.get("RESOURCE_URL")
    names_ids={}
    for item in results["results"]["results"]:
        value = {}
        values.append(value)
        value["Id"] = item["id"]
        names_ids[value["Id"]]=item.get("name")

        value["Name"]=item.get("name")
        value["Project name"] = item.get("project_name")
        if item.get("screen_name"):
            to_add=True
            value["Study name"] = item.get("screen_name")
        elif  item.get("project_name"):
            to_add=True
            value["Study name"] =  item.get("project_name")

        for k in item["key_values"]:
            if k['name'] not in cols:
                cols.append(k['name'])
            if value.get(k["name"]):
                value[k["name"]]=value[k["name"]]+"; "+ k["value"]
            else:
                value[k["name"]]=k["value"]

    columns=[]
    for col in cols:
        columns.append({
            "id": col,
            "name": col,
            "field": col,
            "hide": False,
            "sortable": True,
        })
    main_cols=[]
    if not columns_def:
        columns_def = []
        cols.sort()
        if resource == "image":
            cols.insert(0, "Study name")
            main_cols.append(("Study name"))
        cols.insert(0, "Name")
        main_cols.append(("Name"))
        cols.insert(0, "Id")
        main_cols.append(("Id"))

        for col in cols:
                columns_def.append({
                    "field": col,
                    "hide":False,
                    "sortable": True,
                })
    else:
        for col_def in columns_def:
            if col_def["field"] not in cols:
                    cols.append(col_def["field"])
    for val in values:
        if len(val)!=len(cols):
            for col in cols:
                if not val.get(col):
                    val[col]='""'
    #print (columns_def)
    returned_results["columns"]=columns
    returned_results["columns_def"]=columns_def
    returned_results["values"]=values
    returned_results["server_query_time"]=results["server_query_time"]
    returned_results["query_details"]=results["query_details"]
    returned_results["bookmark"]=results["results"]["bookmark"]
    returned_results["page"] = results["results"]["page"]
    returned_results["size"] = results["results"]["size"]
    returned_results["total_pages"] = results["results"]["total_pages"]
    returned_results["extend_url"]=extend_url
    returned_results["names_ids"]=names_ids
    returned_results["raw_elasticsearch_query"] = results["raw_elasticsearch_query"]
    if len(values)<=results["results"]["size"]:
        returned_results["contains_all_results"]=True
    else:
        returned_results["contains_all_results"] = False
    returned_results["Error"]=results["Error"]
    returned_results["resource"]=results["resource"]+"s"
    return returned_results



def determine_search_results_(query_, return_columns=False):
    if query_.get("query_details"):
        case_sensitive = query_.get("query_details").get("case_sensitive")
    else:
        case_sensitive = False
    bookmark = query_.get("bookmark")
    raw_elasticsearch_query = query_.get("raw_elasticsearch_query")
    and_filters = query_.get("query_details").get("and_filters")
    or_filters = query_.get("query_details").get("or_filters")
    and_query_group = QueryGroup("and_filters")
    columns_def = query_.get("columns_def")
    or_query_groups = []
    if and_filters and len(and_filters) > 0:
        for filter in and_filters:
            and_query_group.add_query(QueryItem(filter))
        and_query_group.divide_filter()
        and_query_group.adjust_query_main_attributes()
    if or_filters and len(or_filters) > 0:
        for filters_ in or_filters:
            or_query_group = QueryGroup("or_filters")
            or_query_groups.append(or_query_group)
            for filter in filters_:
                or_query_group.add_query((QueryItem(filter)))
            or_query_group.divide_filter()
            or_query_group.adjust_query_main_attributes()

    query_runner=QueryRunner(and_query_group, or_query_groups, case_sensitive, bookmark, raw_elasticsearch_query, columns_def,return_columns)
    return(query_runner.get_iameg_non_image_query())


def simple_search(key, value, operator,  case_sensitive, bookmark, resource):
    if not operator:
        operator='equals'
    and_filters=[{"name": key, "value": value, "operator": operator }]
    query_details={"and_filters": and_filters}
    if bookmark:
        bookmark=[bookmark]
    query_details["bookmark"]=[bookmark]
    query_details["case_sensitive"]=case_sensitive
    return (search_resource_annotation(resource, {"query_details": query_details},bookmark=bookmark))

def add_local_schemas_to(resolver, schema_folder, base_uri, schema_ext='.json'):
    ''' Add local schema instances to a resolver schema cache.

    Arguments:
        resolver (jsonschema.RefResolver): the reference resolver
        schema_folder (str): the local folder of the schemas.
        base_uri (str): the base URL that you actually use in your '$id' tags
            in the schemas
        schema_ext (str): filter files with this extension in the schema_folder
    '''
    from pathlib import Path
    import json
    import os
    from urllib.parse import urljoin

    for dir, _, files in os.walk(schema_folder):
        for file in files:
            if file.endswith(schema_ext):
                schema_path = Path(dir) / Path(file)
                rel_path = schema_path.relative_to(schema_folder)
                with open(schema_path) as schema_file:
                    schema_doc = json.load(schema_file)
                key = urljoin(base_uri, str(rel_path))
                resolver.store[key] = schema_doc

def query_validator(query):
    query_schema_file = "search_engine/api/v1/resources/schemas/query_data.json"
    base_uri = 'file:' + abspath('') + '/'
    with open(query_schema_file, 'r') as schema_f:
        query_schema = json.loads(schema_f.read())

    resolver = RefResolver(referrer=query_schema, base_uri=base_uri)
    schema_folder = dirname(query_schema_file)
    #schema_folder = Path('search_engine/api/v1/resources/schemas')
    add_local_schemas_to(resolver, schema_folder, base_uri)


    try:
        validate(query, query_schema, resolver=resolver)
        search_omero_app.logger.info("Data is valid")
        return "OK"
    except SchemaError as e:
        search_omero_app.logger.info("there is a schema error")
        search_omero_app.logger.info(e.message)
        return e.message
    except ValidationError as e:
        search_omero_app.logger.info("there is a validation error")
        search_omero_app.logger.info(e.message)
        return e.message