0.5.2 (June 2023):
------------------
- Return all the available values for a key in a container [#77](https://github.com/ome/omero_search_engine/pull/77)
- Return the available attributes with a container 

0.5.1 (February 2023):
----------------------
- Fix the issue of filtering images by the container name [#81](https://github.com/ome/omero_search_engine/pull/81)
- Add 'Organism' to the project search terms

0.5.0 (January 2023):
---------------------
- Enable searching by container name [#57](https://github.com/ome/omero_search_engine/pull/57)
- Allow the use of a container as a resource [#69](https://github.com/ome/omero_search_engine/pull/69)
- Use 'name' for the container instead of 'Name (IDR number)' [#72](https://github.com/ome/omero_search_engine/pull/72)

 0.4.1 (December 2022):
----------------------
- Add disclaimer to readme [#64](https://github.com/ome/omero_search_engine/pull/64)

0.4.0 (December 2022):
---------------------
- Support working with multiple Elasticsearch nodes [#61](https://github.com/ome/omero_search_engine/pull/61).
- Backup and restore Elasticsearch indices data.

0.3.0 (September 2022)
----------------------
- Add pagination section to the query results [#56](https://github.com/ome/omero_search_engine/pull/56).
- Return the closest match first for a query using /searchvalues/ endpoint and subsequently include all possible matches [#53](https://github.com/ome/omero_search_engine/pull/53).
- Searching for * or ? queries for strings containing those literal characters and they are not treated as wild-cards [#51](https://github.com/ome/omero_search_engine/pull/51).
- Return containers (project or screen) which include image count and title for query results [#19](https://github.com/ome/omero_search_engine/pull/19) and [#41](https://github.com/ome/omero_search_engine/pull/41). 
- Allow return number of the images for each value for a specific key [#40](https://github.com/ome/omero_search_engine/pull/40).
- Fix issue of the "or" conditions [#38](https://github.com/ome/omero_search_engine/pull/38).
- Fix the issues of getting resource names and unit tests [#28](https://github.com/ome/omero_search_engine/pull/28)17/Jul/2022).
- Generate a csv file for the attribute buckets [#20](https://github.com/ome/omero_search_engine/pull/20).

0.2.0 (June 2022)
-----------------
- Test indexing and queries [#17](https://github.com/ome/omero_search_engine/pull/17).
- Improve documentation [#15](https://github.com/ome/omero_search_engine/pull/15).
- Add "key sensitive" option [#14](https://github.com/ome/omero_search_engine/pull/14).
- Reduce indexing time[#13](https://github.com/ome/omero_search_engine/pull/13). 
- Add validation JSON schema for the search query.
- Add the swagger documentations.
- Search for any value.
- Cache the value buckets for each key for each resource. 
- Add submitquery endpoint.
- Add Examples.

0.1.0 (February 2022)
---------------------
- Initial release
