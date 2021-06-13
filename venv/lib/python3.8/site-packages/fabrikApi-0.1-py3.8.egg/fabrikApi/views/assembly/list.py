""" Assemblies List View. """

import logging
from datetime import datetime

from cornice.service import Service

from fabrikApi.models.assembly import DBAssembly
from fabrikApi.models.mixins import arrow
# from fabrikApi.util.cors import CORS_LOCATION, CORS_MAX_AGE

logger = logging.getLogger(__name__)


# SERVICES
assemblies = Service(cors_origins=('*',),
    name='assemblies', 
    description='List Assemblies.', 
    path='/assemblies')

@assemblies.get(permission='public')
def get_assemblies(request):
    """Returns all assemblies which are either public or accessible by the current user.
    """

    # load all active assemblies
    # TODO: filter only active assemblies
    assemblies = request.dbsession.query(DBAssembly).all()

    for assembly in assemblies:
        # assembly.patch()
        assembly.setup_lineage(request)

    # show only assemblies with at least view permission.
    assemblies = list(
        filter(lambda assembly: request.has_public_permission(assembly),
               assemblies)
    )

    assemblies = {v.identifier: v for v in assemblies}

    return({
        'assemblies': assemblies,
        'access_date': arrow.utcnow()
    })
