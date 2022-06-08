#import psql_templates
from omero_search_engine import search_omero_app

from omero_search_engine.api.v1.resources.query_handler import determine_search_results_
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
        self.searchengine_results = []

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
        self.searchengine_results = []


    def get_results_postgres(self):
        '''
        Query the postgresql
        '''
        search_omero_app.logger.info("Getting results from postgres")
        if self.type=="complex":
            if self.name == "query_image_or":
                names = ''
                values = ''
                for claus in self.clauses:
                    if names:
                        names = names + ",'%s'" % claus[0].lower()
                        values = values + ",'%s'" % claus[1].lower()
                    else:
                        names = "'%s'" % claus[0].lower()
                        values = "'%s'" % claus[1].lower()
                sql = query_methods[self.name].substitute(names=names, values=values)
            elif self.name == "query_image_and":
                results=[]
                co=0
                for claus in self.clauses:
                    sql=query_methods["image"].substitute(name=claus[0].lower(), value=claus[1].lower())
                    search_omero_app.logger.info("and sql: %s" % sql)
                    postgres_results = search_omero_app.config["database_connector"].execute_query(sql)
                    res=[item['id'] for item in postgres_results]
                    search_omero_app.logger.info("results recived %s" % len(postgres_results))
                    if co==0:
                        results=res
                    else:
                        results=list(set(results) & set(res))
                    co+=1
                self.postgres_results=results
                return
        else:
            if self.name!="name":
                sql=self.sql_statament.substitute(name=self.name.lower(), value=self.value.lower())
            else:
                sql=self.sql_statament.substitute(name=self.value)
        search_omero_app.logger.info ("sql: %s"%sql)
        self.postgres_results=search_omero_app.config["database_connector"].execute_query(sql)
        search_omero_app.logger.info("results recived %s"%len(self.postgres_results))

    def get_results_searchengine(self):
        '''
        Query the results from the serachengine
        '''
        if self.type == "complex":
            filters = []
            for claus in self.clauses:
                filters.append(
                    {"name": claus[0], "value": claus[1], "operator": "equals", "resource": self.resource})
            if self.name=="query_image_or":
                query = {"and_filters": [], "or_filters": [filters]}
            elif self.name == "query_image_and":
                query = {"and_filters": filters, "or_filters": []}
        else:
            if self.name!="name":
                and_filters=[{"name": self.name.lower(), "value": self.value.lower(), "operator": "equals", "resource": self.resource}]

            else:
                and_filters=[{'name': 'Name (IDR number)', 'value': self.value,'resource': 'project','operator': 'equals'}]
            query = {"and_filters": and_filters, "or_filters": []}
        query_data = {'query_details': query}
        search_omero_app.logger.info("Getting results from search engine")
        self.searchengine_results=determine_search_results_(query_data, True)
        search_omero_app.logger.info\
            ("no of recived results from searchengine  : %s"% self.searchengine_results.get("size") )

    def compare_results(self):
        '''
        call the results
        '''
        self.get_results_postgres()
        self.get_results_searchengine()
        if len(self.postgres_results)==self.searchengine_results.get("size") :
            search_omero_app.logger.info("No of retuned results are identical ...")
            return "OK, Identical!"
        return "Does not return the same results???"

    def validateclauses(self):
        pass


'''
{'resource': 'image', 'query_details': {'and_filters': [{'name': 'Name (IDR number)', 'value': 'idr0027-dickerson-chromatin/experimentA', 'operator': 'equals', 'resource': 'project'}], 'or_filters': [], 'case_sensitive': False}, 'mode': 'usesearchterms'}
                    
{                      'query_details': {'and_filters': [{'name': 'Name (IDR number)', 'value': 'idr0027-dickerson-chromatin/experimenta', 'resource': 'project', 'operator': 'equals'}], 'or_filters': []}}



{                     'query_details': {'and_filters': [], 'or_filters': [{'name': 'Organism Part', 'value': 'Prostate', 'operator': 'equals', 'resource': 'image'}, {'name': 'Organism Part Identifier', 'value': 'T-77100', 'operator': 'equals', 'resource': 'image'}]}}

{'resource': 'image', 'query_details': {'and_filters': [], 'or_filters': [[{'name': 'Organism Part Identifier', 'value': 't-77100', 'operator': 'equals', 'resource': 'image'}, {'name': 'Organism Part', 'value': 'prostate', 'operator': 'equals', 'resource': 'image'}]], 'case_sensitive': False}, 'mode': 'usesearchterms'}

'''
