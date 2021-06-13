""" EntryPoint for Client Monitor  List View. """

from fabrikApi.util.lib import email_notification
from fabrikApi.views.lib.helpers import remove_unvalidated_fields
import logging
import traceback

from cornice.service import Service
import jsonschema

from fabrikApi.views.lib import monitor_events
# from fabrikApi import plugins
# from fabrikApi.models.lib.plugin_interfaces import PLUGIN_MODULES

logger = logging.getLogger(__name__)


monitors = Service(
    cors_origins=('*',), 
    name='monitor',
    description='Receive Notifcations from the Client.',
    path='/monitor')

@monitors.post(permission='observe')
def receive_monitor(request):
    """USER MONITOR: CALL defs"""

    # TODO: possible to sync wiht acls?
    
    # SANITIZE JSON DATA
    schema = {
        "type": "object",
        "properties": {
            "buffer": {"type": "array"},
        },
        "required": []
    }

    # CONTINUEING ONLY WITH AUTHENTICATED USER
    # dont log unauthenticated users...
    assert request.local_userid, "invalid localuserid..."
    assert request.body, "invalid request body..."
    jsonschema.validate(request.json_body, schema)
    body = remove_unvalidated_fields(request.json_body, schema)
    buffer = body.get('buffer')

    # take only max 500 events.
    if len(buffer) > 500:
        logger.info("buffered monitors action are too many. => cut to 500")
        buffer = buffer[0:500]
 
    response = {'errors': [], 'warnings': []}
    logs = []
    IGNORED_MONITOR_ACTIONS_FOR_DB = ['CONTENT.DISCUSSED',]

    # event = buffer[1]
    request.processed_events = []
    for event in buffer:

        # CORE APP EVENTS
        # elog = monitor_events.MonitorCore(request, response, event)
        try:
            elog = monitor_events.MonitorCore(request, response, event)
            assert elog.user_id == request.local_userid, 'wrong user: log and request user are not equal'
 
            if elog.action not in IGNORED_MONITOR_ACTIONS_FOR_DB:
                logs.append(elog)
            request.processed_events.append(event.get('eventString'))

        except Exception as e:

            # if request.registry.settings.get('debug_all'):
            #     # raise always in debug mode!!!
            #     raise e

            # first attempt can be returned to the client (by sending HTTP Status Error)
            # however, the second attempt can be catch (while notifying admin and user)
            if request.params.get('rty'):

                # notify client
                errorObj = {
                    'event': event,
                    'message': e.args[0] if e and e.args else 'error while performing event'
                }
                response['errors'].append(errorObj)

                # notify admin
                if not request.registry.settings.get('debug_all'):
                    # just raise the error again, (in case its the dev server)
                    # send email
                    var = traceback.format_exc()
                    message = "%s\n\n%s\n\n%s" % (e, event, var)
                    email_notification(message, "Monitor-Logs")

            else:
                # raise Exception (first one)
                raise e

    if logs:
        ##############
        # Try to save all logs together....
        # in the first attempt...
        error_bulk_save = not request.params.get('rty')
        
        if error_bulk_save:
            request.dbsession.begin_nested()
            request.dbsession.bulk_save_objects(logs)
            request.dbsession.commit()

        else:

            # add the second trial: save seperately each log
            for log in logs:
                try:
                    request.dbsession.begin_nested()
                    request.dbsession.add(log)
                    request.dbsession.flush()

                except Exception as e:
                    # One ore more rows are not possible to insert... (go on line by line..)            
                    request.dbsession.rollback()
                    # TODO: send email!!!!
                    # notify admin
                    if not request.registry.settings.get('debug_all'):
                        # send email
                        message = "%s" % (e)
                        email_notification(message, "Monitor-Logs-Inserts")
                    # Return to user
                    errorObj = {
                        'event': 'INSERTING LOGS', 
                        'message': 'Erro while monitoring activities. Probably a log table Integritiy error'}
                    response['errors'].append(errorObj)

    return ({'ok': True, 'response': response})
