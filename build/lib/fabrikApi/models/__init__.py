# import sqlalchemy
import zope.sqlalchemy
from get_docker_secret import get_docker_secret
from sqlalchemy import create_engine
from sqlalchemy.orm import configure_mappers, sessionmaker


# from fabrikApi.util.versionmanager import make_versioned

from .user import *
from .log import *
from .assembly import *
from .stage import *
from .contenttree.content import *
from .contenttree.contenttree import *
from .contenttree.content_peerreview import *
from .mixins import *
# from .artificial_moderation import *


# all relationships can be setup
configure_mappers()


def get_database_url(use_pymsql):
    """Custom method to get config from the environmental variables.

    Based on: http://allan-simon.github.io/blog/posts/python-alembic-with-environment-variables/
    """
    return "mysql+pymysql://{}:{}@{}:3306/{}?charset=utf8".format(
        get_docker_secret('fabrikapi_db_user', default=''),
        get_docker_secret('fabrikapi_db_password', default=''),
        get_docker_secret('fabrikapi_db_host', default=''),
        get_docker_secret('fabrikapi_db_name', default='')
    )


def get_engine(settings, prefix='sqlalchemy.'):
    url = get_database_url(settings.get("sqlalchemy.use_pymysql")=="true")
    # addded pre-ping to avoid "pipe broke" errors on production system. Does this help? (after mysql server is restarted...)
    return create_engine(url, pool_pre_ping=True)
    # return create_engine(url)


def get_session_factory(engine):
    """Return a generator of database session objects."""
    factory = sessionmaker(autoflush=False)
    factory.configure(bind=engine)
    # NOTE: autoflush or not: more query vs. less lock duration, right?
    return factory


def get_tm_session(session_factory, transaction_manager):
    """Build a session and register it as a transaction-managed session."""
    dbsession = session_factory()
    zope.sqlalchemy.register(dbsession, transaction_manager=transaction_manager)
    return dbsession


def includeme(config):
    """
    Initialize the models
    """
    settings = config.get_settings()
    settings['tm.manager_hook'] = 'pyramid_tm.explicit_manager'

    # use pyramid_tm to hook the transaction lifecycle to the request
    config.include('pyramid_tm')

    session_factory = get_session_factory(get_engine(settings))
    config.registry['dbsession_factory'] = session_factory

    # make request.dbsession available for use in Pyramid
    config.add_request_method(
        # request.tm is the transaction manager used by pyramid_tm
        lambda request: get_tm_session(session_factory, request.tm), 'dbsession', reify=True
    )

    

db_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_fabrikApi_db" script
    to initialize your database tables.  Check your virtual
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""
