import unittest
'''
Basic app unit tests
'''

from search_engine import search_omero_app, create_app
create_app('testing')


class BasicTestCase(unittest.TestCase):
    def setUp(self):
        pass#d_util.createdatabase(db)

    def tearDown(self):
        pass#d_util.drop_all_databases(db)

    def test_api_v1(self):
        '''test home page'''
        tester = search_omero_app.test_client(self)
        response = tester.get('/api/v1/resources/images?filters=""', content_type='html/text')
        self.assertEqual(response.status_code, 308)

    def test_not_found(self):
        '''
        test not found url
        :return:
        '''
        tester = search_omero_app.test_client(self)
        response = tester.get('a', content_type='html/text')
        self.assertEqual(response.status_code, 404)

    def test_query_database(self):
        from test_data import sql
        res = search_omero_app.config["database_connector"].execute_query(sql)
        self.assertIsNotNone(res)
        self.assertIsInstance(res[0]["count"], int)

    def test_submit_query(self):
       ''''
       '''
       pass

    def test_log_in_log_out(self):
        '''
        test login and log out functions
        :return:
        '''
        pass

    def test_drop_database(self):
        '''

        '''
        pass#d_util.drop_all_databases(db)

if __name__ == '__main__':
    unittest.main()