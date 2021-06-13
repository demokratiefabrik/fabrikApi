""" Unalert a Stage of a user. => Used for embedding external services.... """

from fabrikApi.models.assembly import get_assembly_by_identifier
from fabrikApi.models.user import DBUser
from fabrikApi.models.lib.core import get_or_create_progression
from fabrikApi.models.stage import DBStage, DBStageProgression
import logging
import transaction
import pyramid.httpexceptions as exc
from zope.sqlalchemy.datamanager import mark_changed
from cornice.service import Service
from get_docker_secret import get_docker_secret


logger = logging.getLogger(__name__)

# SERVICES
unalert = Service(
    cors_origins=('*',),
    name='unalert',
    description='Unalert A stage progression...',
    path='/stage/unalert')

@unalert.get()
def unalert_view(request):
    """ Unalert a stage progression by external api call """

    external_service_secret = get_docker_secret('fabrikapi_external_service_secret')
    assert external_service_secret
    if external_service_secret != request.params.get('external'):
        raise exc.HTTPNotFound()

    stage_id = request.params.get('S')
    if not stage_id:
        # Probably not a real Demokratiefabrik User...Survey-Test?
        raise exc.HTTPNotFound()

    user_id = int(request.params.get('U'))
    assembly_identifier = request.params.get('A')


    # Check data
    request.assembly = get_assembly_by_identifier(request, assembly_identifier)
    if not request.assembly:
        raise exc.HTTPNotFound()
    user = request.dbsession.query(DBUser).filter(DBUser.oauth2_user_id == user_id).one()
    if not user:
        raise exc.HTTPNotFound()
    stage = request.dbsession.query(DBStage).get(stage_id)
    if not stage:
        raise exc.HTTPNotFound()
    
    # Create content progression
    progression = get_or_create_progression(
        request,
        DBStageProgression,
        user_id=user.id,
        stage_id=stage.id)

    assert progression
    progression.complete()

    logger.info("STAGE PROGRESSION UNALERTED %s", progression.id)
    return True
