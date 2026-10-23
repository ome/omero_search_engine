from omero_search_engine.api.auth.utils import get_data_source_server_url
from omero.gateway import BlitzGateway


def connect_omero(username, password, datasource):
    host, port = get_data_source_server_url(datasource)
    if not host:
        return None
    print("Establish connection to omero server")
    conn = BlitzGateway(
        username=username, passwd=password, host=host, port=port, secure=True
    )
    conn.connect()
    return conn


def search_omero(name, value, conn):
    print("Searching foe %s:%s" % (name, value))
    query_service = conn.getQueryService()
    context_map = {str(k): str(v) for k, v in dict(conn.SERVICE_OPTS).items()}
    # search using all user groups
    context_map["omero.group"] = "-1"
    hql_query = (
        "select img from Image img "
        "join img.annotationLinks l "
        "join l.child a "
        "join a.mapValue mv "
        "where a.class = MapAnnotation "
        "and mv.name = '%s' "
        "and mv.value = '%s'" % (name, value)
    )
    print("hql_query: %s" % hql_query)
    print("Running corrected database HQL lookup...")

    try:
        results = query_service.findAllByQuery(hql_query, None, context_map)
        conn.SERVICE_OPTS.setOmeroGroup("-1")
        if not results:
            print("No matching objects found in the database tables.")
        else:
            print(f"Found {len(results)} exact matching Image(s):")
            # for img in results:
            #    image = conn.getObject("Image", img.id.val)
            #    print(
            #        f" - [ID: {image.id}] Name: {image.name} "
            #        f"(Owner: {image.getOwnerOmeName()})"
            #   )

    except Exception as e:
        print(f"Query Execution Error: {e}")


if __name__ == "__main__":
    conn = connect_omero("user-49", "omero", "omero")
    if conn and conn.connect():
        search_omero("Cell Line", "HeLa", conn)
        print("===========================================")
        search_omero("Organism", "Homo sapiens", conn)  # 15757 #15755
        conn.close()
    else:
        print("connection to omero server failed")
