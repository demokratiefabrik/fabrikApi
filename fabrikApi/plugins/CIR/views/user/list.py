""" Assemblies List View. """

import logging
# from datetime import datetime

from cornice.service import Service

from fabrikApi.models import DBUser
from fabrikApi.models.mixins import arrow
# from fabrikApi.util.cors import CORS_LOCATION, CORS_MAX_AGE

logger = logging.getLogger(__name__)


# SERVICES
# user = Service(cors_origins=('*',),
#     name='users', 
#     description='List Users.', 
#     path='/users')


# SERVICES
users = Service(
    cors_origins=('*',),
    name='users', 
    description='Show Assemblys Users.', 
    path='/users')

# , headers={'Content-Disposition': 'File Transfer', 'Content-Type': 'application/force-download'})
@users.get(permission='public')
def get_users(request):
    """Returns all users which are part of this assembly.
    """

    # load all active assemblies
    # TODO: filter only active assemblies
    users = request.dbsession.query(DBUser).all()

    # for user in users:
    #     # assembly.patch()
    #     user.setup_lineage(request)
    # show only users with ...
    # users = list(
    #     filter(lambda assembly: request.has_public_permission(assembly),
    #            assemblies)
    # )

    users = {v.id: v for v in users}

    return({
        'users': users,
        'access_date': arrow.utcnow()
    })
