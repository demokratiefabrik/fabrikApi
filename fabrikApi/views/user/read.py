""" Assembly Read. """

from fabrikApi.models.notification import DBNotification
import logging

import arrow
from cornice.service import Service

logger = logging.getLogger(__name__)

from get_docker_secret import get_docker_secret

# SERVICES
user = Service(
    cors_origins=('*',),
    name='profile',
    description='Read/List/Manage Userprofiles.',
    path='/profile')

@user.get(permission='observe')
def get_profile(request):
    """Returns the public user-profile """

    return({'user': request.current_user,
            'configuration': {'t': int(get_docker_secret('fabrikapi_testing_phase', default=0)) == 1},
            'access_date': arrow.utcnow(),
            'access_sub': request.authenticated_userid
            })
