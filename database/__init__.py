'''
@author: PUM
'''
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config
from sqlalchemy.orm.scoping import scoped_session
from contextlib import contextmanager

db = None
Base = declarative_base()
session_factory = sessionmaker()
Session = scoped_session(session_factory)
#Session = sessionmaker()

connection_str = config.database_connection_str

def setup_db():
    global db

    # Multiple calls to setup_db should be ignored
    if db is None:
        db = create_engine(connection_str, echo=True)
        event.listen(db, "connect", set_sqlite_pragma)
        Session.configure(bind=db)

def create_schema():
    Base.metadata.create_all(db)

def insert_initial_data():
    session = Session()

    # Add CloudProvider
    session.add(cloudprovider.CloudProvider(name='EC2'))

    # Add DataProvider
    session.add(dataprovider.DataProvider(name='S3'))
    session.add(dataprovider.DataProvider(name='HTTP'))
    session.add(dataprovider.DataProvider(name='Git'))

    session.commit()

#see http://docs.sqlalchemy.org/en/latest/orm/session_basics.html#session-faq-whentocreate
@contextmanager
def get_session():
    """Provide a transactional scope around a series of operations."""
    session = Session()

    # This is a workaround as we generally re-use a thread-local session (using a scoped_session) but want to make sure that in a nested Situation
    # (FuncA calls get_session() and calls FuncB whereas FuncB itself calls get_session as well) the inner session doesn't rollback the outer one.
    # Although this might lead to a problem if the outer function relies on the results of the inner function. Maybe a reference counter
    # would be an alternative here...
    if session.info.get("inUse", False):
        session = session_factory()
    else:
        session.info['inUse'] = True

    try:
        yield session
    except:
        session.rollback()
        raise
    finally:
        session.info['inUse'] = False
        session.close()


def set_sqlite_pragma(dbapi_connection, connection_record):
    if connection_str.lower().startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

from database.model import *
