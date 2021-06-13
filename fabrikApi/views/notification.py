""" EntryPoint for User Notifications  (List View). """

import arrow
from sqlalchemy.sql.elements import and_, or_
from fabrikApi.models.notification import DBNotification
from fabrikApi.views.lib.helpers import remove_unvalidated_fields
import logging

from cornice.service import Service
import jsonschema

from fabrikApi.views.lib import monitor_events

logger = logging.getLogger(__name__)


notifications = Service(
    cors_origins=('*',), 
    name='notifications',
    description='Receive Notifcations for the user.',
    path='/notifications')

@notifications.post(permission='observe')
def receive_notifications(request):
    """USER MONITOR: CALL defs"""
    
    # SANITIZE JSON DATA
    schema = {
        "type": "object",
        "properties": {
            "update_date": {"type": "string"},
        },
        "required": []
    }

    # CONTINUEING ONLY WITH AUTHENTICATED USER
    assert request.local_userid, "invalid localuserid..."
    assert request.body, "invalid request body..."
    jsonschema.validate(request.json_body, schema)
    body = remove_unvalidated_fields(request.json_body, schema)
    update_date = body.get('update_date')

    NOTIFICATION_LIMIT = request.registry.settings.get('fabrikapi.notification.limit', 20)

    if update_date:
        update_date = arrow.get(update_date)
        notifications = request.dbsession.query(DBNotification)\
            .filter(and_(
                or_(
                    DBNotification.date_last_interaction > update_date,
                    DBNotification.date_created > update_date),
                DBNotification.user_id == request.local_userid))\
            .order_by(DBNotification.date_created.desc()).all()
    else:
        notifications = request.dbsession.query(DBNotification)\
            .filter(and_(
                DBNotification.user_id == request.local_userid))\
            .order_by(DBNotification.date_created.desc()).limit(NOTIFICATION_LIMIT).all()
    
    return ({'OK': True, 'notifications': notifications})
