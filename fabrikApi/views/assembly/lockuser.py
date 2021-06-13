""" EntryPoint for User Notifications  (List View). """

from fabrikApi.views.lib.factories import AssemblyFactory
from cornice.service import Service
import jsonschema
import logging

from fabrikApi.models.assembly import DBAssemblyProgression
from fabrikApi.models.user import DBUser
from fabrikApi.views.lib.helpers import remove_unvalidated_fields
from fabrikApi.models.notification import initiate_notification
from fabrikApi.util.constants import NOTIFICATION_ACTION_LOCK_USER
from fabrikApi.models.lib.core import get_or_create_progression


logger = logging.getLogger(__name__)


user_lock_from_assembly = Service(
    cors_origins=('*',),
    name='user_lock_from_assembly',
    description='Send Notifcation Message to the user.',
    traverse='/{assembly_identifier}',
    path='/assembly/{assembly_identifier}/lockuser',
    factory=AssemblyFactory)

@user_lock_from_assembly.post(permission='manage')
def lock_user_from_assembly(request):
    """USER MONITOR: CALL defs"""
    
    # SANITIZE JSON DATA
    schema = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "maxLength": 300},
            "user_id": {"type": ["number"]},
        },
        "required": ['message']
    }

    # CONTINUEING ONLY WITH AUTHENTICATED USER
    assert request.local_userid, "invalid localuserid..."
    assert request.body, "invalid request body..."
    jsonschema.validate(request.json_body, schema)
    body = remove_unvalidated_fields(request.json_body, schema)
    message = body.get('message')
    user_id = body.get('user_id')

    user = request.dbsession.query(DBUser).get(user_id)
    assert user
    assert user.id is not request.local_userid, "cannot lock oneself"
    
    # Get AssemblyProgression
    assembly_progression = get_or_create_progression(
        request,
        DBAssemblyProgression,
        auto_create=False,
        user_id=user_id,
        assembly=request.assembly)
    if not assembly_progression:
        return ({'error': True, 'response': 'NOT.PART.OF.THIS.ASSEMBLY'})
    
    # lock assembly for this user....
    assembly_progression.lock_user()

    # add notification
    initiate_notification(
        request=request,
        action=NOTIFICATION_ACTION_LOCK_USER,
        user_id=user_id,
        assembly=request.assembly,
        value=message)

    return ({'ok': True})
