#import psql_templates
from omero_search_engine import search_omero_app
from datetime import datetime
from omero_search_engine.api.v1.resources.query_handler import determine_search_results_, query_validator
from omero_search_engine.validation.psql_templates import query_images_key_value, query_image_project_meta_data, \
    query_images_screen_key_value, query_images_in_project_name, query_images_screen_name,query_image_or

query_methods={"image":query_images_key_value,"project":query_image_project_meta_data, "screen":query_images_screen_key_value,
               "project_name":query_images_in_project_name,"screen_name":query_images_screen_name, "query_image_or": query_image_or}



class Validator(object):
    '''
    Compare the results which are coming from postgresql server and from  the searchengine
    '''

    def __init__ (self):
        pass

    def set_simple_query (self, resource, name, value, type="keyvalue"):
        '''
        simple query
        '''
        self.resource=resource
        self.type=type
        self.name=name
        self.value=value
        self.postgres_results=[]
        self.sql_statament=query_methods[resource]
        self.searchengine_results = {}

    def set_complex_query (self, name, clauses, resource="image", type="complex"):
        '''
        complex query
        '''
        self.resource=resource
        self.clauses=clauses
        self.name=name
        self.value=clauses
        self.type=type
        self.postgres_results = []
        self.searchengine_results = {}

    def get_or_sql(self, clauses, name="query_image_or"):
        names = ''
        values = ''
        for claus in clauses:
            if names:
                names = names + ",'%s'" % claus[0].lower()
                values = values + ",'%s'" % claus[1].lower()
            else:
                names = "'%s'" % claus[0].lower()
                values = "'%s'" % claus[1].lower()
        sql = query_methods[name].substitute(names=names, values=values)
        postgres_results = search_omero_app.config["database_connector"].execute_query(sql)
        results = [item['id'] for item in postgres_results]
        search_omero_app.logger.info("results for or received %s" % len(results))
        return results


    def get_and_sql(self, clauses):
        results = []
        co = 0
        for claus in clauses:
            sql = query_methods["image"].substitute(name=claus[0].lower(), value=claus[1].lower())
            postgres_results = search_omero_app.config["database_connector"].execute_query(sql)
            res = [item['id'] for item in postgres_results]
            search_omero_app.logger.info("results for and  received recived %s" % len(res))
            if co == 0:
                results = res
            else:
                results = list(set(results) & set(res))
            co += 1
        return results

    def get_results_postgres(self):
        '''
        Query the postgresql
        '''
        search_omero_app.logger.info("Getting results from postgres")
        if self.type=="complex":
            if self.name == "query_image_or":
                self.postgres_results=self.get_or_sql(self.clauses)
            elif self.name == "query_image_and":
                self.postgres_results =self.get_and_sql(self.clauses)
            else:
                for name, clauses in self.clauses.items():
                    if name == "query_image_or":
                        or_postgres_results = self.get_or_sql(clauses)
                    elif name == "query_image_and":
                        and_postgres_results = self.get_and_sql(clauses)
                self.postgres_results = list(set(or_postgres_results) & set(and_postgres_results))
            return
        else:
            if self.name!="name":
                sql=self.sql_statament.substitute(name=self.name.lower(), value=self.value.lower())
            else:
                sql=self.sql_statament.substitute(name=self.value)
        #search_omero_app.logger.info ("sql: %s"%sql)
        postgres_results=search_omero_app.config["database_connector"].execute_query(sql)
        self.postgres_results = [item['id'] for item in postgres_results]
        search_omero_app.logger.info("results recived %s"%len(self.postgres_results))

    def get_results_searchengine(self):
        '''
        Query the results from the serachengine
        '''
        if self.type == "complex":
            filters = []
            if self.name!="query_image_and_or":
                for claus in self.clauses:
                    filters.append(
                        {"name": claus[0], "value": claus[1], "operator": "equals", "resource": self.resource})
                if self.name=="query_image_or":
                    query = {"or_filters": [], "or_filters": [filters]}
                elif self.name == "query_image_and":
                    query = {"and_filters": filters, "or_filters": []}
            else:
                query={}
                or_filters=[]
                query["or_filters"]=or_filters
                for filter_name, clauses in self.clauses.items():
                    filters=[]
                    if filter_name=="query_image_or":
                        or_filters.append(filters)
                    else:
                        query["and_filters"] = filters
                    for claus in clauses:
                        filters.append(
                            {"name": claus[0], "value": claus[1], "operator": "equals", "resource": self.resource})

        else:
            if self.name!="name":
                and_filters=[{"name": self.name.lower(), "value": self.value.lower(), "operator": "equals", "resource": self.resource}]
            else:
                and_filters=[{'name': 'Name (IDR number)', 'value': self.value,'resource': 'project','operator': 'equals'}]
            query = {"and_filters": and_filters, "or_filters": []}
        query_data = {'query_details': query}
        #validate the query syntex
        query_validation_res = query_validator(query_data)
        if query_validation_res == "OK":
            search_omero_app.logger.info("Getting results from search engine")
            searchengine_results=determine_search_results_(query_data)
            size=searchengine_results.get("results").get("size")
            ids = [item["id"] for item in searchengine_results["results"]["results"]]
            #### get all the results if the total number is bigger than the page size
            if size >= search_omero_app.config["PAGE_SIZE"]:
                bookmark = searchengine_results["results"]["bookmark"]
                while len(ids) < size:
                    search_omero_app.logger.info("Recieved %s/%s"%(len(ids), size))
                    query_data_ = {"query_details": query, "bookmark": bookmark}
                    searchengine_results_ = determine_search_results_(query_data_)
                    ids_ = [item["id"] for item in searchengine_results_["results"]["results"]]
                    ids=ids+ids_
                    bookmark = searchengine_results_["results"]["bookmark"]
            self.searchengine_results={"size":size, "ids": ids}
            search_omero_app.logger.info\
                ("no of recived results from searchengine  : %s"% self.searchengine_results.get("size") )
        else:
            search_omero_app.logger.info("The query is not valid")

    def compare_results(self):
        '''
        call the results
        '''
        st_time=datetime.now()
        self.get_results_postgres()
        st2_time = datetime.now()
        self.get_results_searchengine()
        st3_time = datetime.now()
        sql_time=st2_time-st_time
        searchengine_time= st3_time - st2_time

        if len(self.postgres_results)==self.searchengine_results.get("size") :
            ids_in=True
            is_it_repated=[]
            for id in self.searchengine_results.get("ids"):
                if id in is_it_repated:
                    print("ERRORRRRRRRR, REPATED ID .......................")
                    sys.exit()
                    break
                else:
                    is_it_repated.append(id)
                if id not in self.postgres_results:
                    ids_in=False
                    break
            if ids_in:
                search_omero_app.logger.info("No of retuned results are similar ...")
                return "equal (%s images), \n database server query time= %s, searchengine query time= %s" %(len(self.postgres_results),sql_time, searchengine_time)
        if self.searchengine_results:
            searchengine_no=self.searchengine_results.get("size")
        else:
            searchengine_no=self.searchengine_results
        return "not equal, database no of results from server is: %s and the number of results from searchengine is %s?, \ndatabase server query time= %s, searchengine query time= %s" %(len(self.postgres_results),searchengine_no ,sql_time, searchengine_time)


def validate_quries(json_file):
    import json
    import os
    if not os.path.isfile(json_file):
        return ("file: %s is not exist" % json_file)

    with open(json_file) as json_data:
        test_data = json.load(json_data)

    #Setthe number pf returend results in one call to 10000
    search_omero_app.config["PAGE_SIZE"]=10000

    test_cases = test_data.get("test_cases")
    complex_test_cases = test_data.get("complex_test_cases")
    messages = []
    from datetime import datetime
    for resource, cases in test_cases.items():
        for case in cases:
            start_time = datetime.now()
            name = case[0]
            value = case[1]
            search_omero_app.logger.info("Testing %s for name: %s, key: %s" % (resource, name, value))
            validator = Validator()
            validator.set_simple_query(resource, name, value)
            res = validator.compare_results()
            elabsed_time = str(datetime.now() - start_time)
            messages.append("Results form  PostgreSQL and search engine for name: %s , value: %s are: %s" % (
            validator.name, validator.value, res))
            search_omero_app.logger.info("Total time=%s" % elabsed_time)

    for name, cases in complex_test_cases.items():
        start_time = datetime.now()
        validator_c = Validator()
        validator_c.set_complex_query(name, cases)
        res = validator_c.compare_results()
        messages.append("Results form  PostgreSQL and search engine for %s name: %s and value: %s are %s" % (
        name, validator_c.name, validator_c.value, res))
        search_omero_app.logger.info("Total time=%s" % str(datetime.now() - start_time))
    search_omero_app.logger.info(
        "############################################## Check Report ##############################################")
    for message in messages:
        search_omero_app.logger.info(message)
        search_omero_app.logger.info("-----------------------------------------------------------------------------")
    search_omero_app.logger.info(
        "###########################################################################################################")
    ###save the check report to a text file
    base_folder = "/etc/searchengine/"
    if not os.path.isdir(base_folder):
        base_folder = os.path.expanduser('~')

    report_file = os.path.join(base_folder, 'check_report.txt')

    report = "\n-----------------------------------------------------------------------------\n".join(messages)
    with open(report_file, 'w') as f:
        f.write(report)
