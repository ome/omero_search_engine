from search_engine import search_omero_app
from  search_engine.api.v1.resources.urls import search_resource_annotation, get_resource_names
import json

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
    def __init__(self,and_query_group,  or_query_group, case_sensitive, mode, bookmark, raw_elasticsearch_query):
        self.or_query_group=or_query_group
        self.and_query_group=and_query_group
        self.case_sensitive=case_sensitive
        self.mode=mode
        self.bookmark=bookmark
        self.raw_elasticsearch_query=raw_elasticsearch_query
        self.image_query={}
        self.additional_image_conds=[]

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
        return res



def seracrh_query(query,resource,bookmark,raw_elasticsearch_query, main_attributes=None):
    print (query)
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
        return {"Error": "Something went wrong, please try later"}

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

def determine_search_results_(query_):
    if query_.get("query_details"):
        case_sensitive = query_.get("query_details").get("case_sensitive")
    else:
        case_sensitive = False
    mode = query_.get("mode")
    bookmark = query_.get("bookmark")
    raw_elasticsearch_query = query_.get("raw_elasticsearch_query")
    and_filters = query_.get("query_details").get("and_filters")
    or_filters = query_.get("query_details").get("or_filters")
    and_query_group = QueryGroup("and_filters")
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
    query_runner=QueryRunner(and_query_group, or_query_groups, case_sensitive, mode, bookmark, raw_elasticsearch_query)
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
