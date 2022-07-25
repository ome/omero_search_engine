import psycopg2
from sqlalchemy.orm import scoped_session, sessionmaker
from psycopg2.extras import (
    DictCursor,
    RealDictCursor,
    RealDictConnection,
    DictCursor,
    DictCursorBase,
)
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine, func, select, exists, text as sqlformat


class DatabaseConnector(object):
    """
    An abstract base class which is inhearted to provide diffrent database operations,
    child classes need to implement all its methods:
    """

    DATABASE_BIND = ""
    DATABASE_NAME = ("",)
    session = ""
    engine = ""

    def _conn(self):
        return psycopg2.connect(self.DATABASE_BIND)

    def __init__(self, name, db_uri, echo_db=False):
        self.DATABASE_NAME = name
        self.DATABASE_URI = db_uri
        engine = create_engine(
            self.DATABASE_URI,
            convert_unicode=True,
            echo=echo_db,
            pool=QueuePool(self._conn, pool_size=20, max_overflow=3, timeout=30),
        )
        self.engine = engine
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.session._model_changes = {}

    def execute_query(self, query, return_results=True):
        results = {}
        try:
            conn = psycopg2.connect(
                self.DATABASE_URI
            )  # options='-c statement_timeout=300000') #default units ms
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SET statement_timeout = '5000 s'")
            cursor.execute(query)
            if return_results:
                results = cursor.fetchall()
            else:
                conn.commit()
                cursor.close()

            conn.close()
        except Exception as e:
            from omero_search_engine import search_omero_app

            search_omero_app.logger.info(
                "Error in performing query %s, error message: %s" % (query, e)
            )
            # return None
            pass
        return results
