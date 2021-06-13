""" Content Views. CRUD & Ratings """

from fabrikApi.models.user import DBUser
from cornice.service import Service
from fabrikApi.views.lib.factories import ContentManagerFactory
import logging

from sqlalchemy_continuum import Operation

logger = logging.getLogger(__name__)

service_content_detail = Service(cors_origins=('*',), 
    name='service_content_detail',
    description='Edit / View / Delete a content.',
    path='/assembly/{assembly_identifier}/content/{content_id:\d+}/detail',
    traverse='/{content_id}',
    factory=ContentManagerFactory)


@service_content_detail.get(permission='observe')
def content_detail(request):
    """Shows detail of a content entry."""

    # Compose Dateil Information...
    history = []
    for version in request.content.versions:
        if version.operation_type == Operation.INSERT:
            continue
        user_id = version.user_modified_id if version.user_modified_id else version.user_created_id
        item = {
            'id': len(history),
            'user_id': user_id,
            'user_profile': request.dbsession.query(DBUser).get(user_id),
            'date': version.date_modified,
            'changeset': version.changeset
        }
        history.append(item)

    # load Autor
    user = request.dbsession.query(DBUser).get(request.content.user_created_id)
    response = {
        'OK': True,
        'history': history,
        'statistic': {
            'user': user.statistics,
            'content': request.content.statistics
        },
    }

    return(response)
