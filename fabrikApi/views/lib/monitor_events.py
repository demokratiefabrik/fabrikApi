"""
The following Events can be raised by Clients via API requests /notify/CLASSNAME.
This allows to inform the API about user activities that take only place on the client side.
"""

from zope.sqlalchemy.datamanager import mark_changed
from fabrikApi.models.notification import DBNotification
from fabrikApi.util.contenttree_manager import ContentTreeManager
import arrow
import random
from fabrikApi.views.lib.monitor_factories import factory_assembly_tuple, factory_peerreview_tuple, factory_stage_tuple, factory_content_tuple
import logging
import jsonschema

from fabrikApi.models.log import DBLog
from fabrikApi.util.events import EventContentRated, EventContentRead,\
    EventContentSalienced, EventSetContentAsDiscussed, EventStageCompleted, EventStageFocusContent, EventStageUnalert
from fabrikApi.views.lib.helpers import remove_unvalidated_fields

logger = logging.getLogger(__name__)


def MonitorCore(request, response, event):
    """
    Event is raised when user enters an assembly.
    """

    # SANITIZE JSON DATA
    schema = {
        "type": "object",
        "properties": {
            "assembly_identifier": {"type": ["string", "null"]},
            "eventString": {"type": ["string"]},
            "date": {"type": ["string", "null"]},
            "data": {"type": ["object", "null"]}
        },
        "required": []
    }

    # CONTINUEING ONLY WITH AUTHENTICATED USER
    # dont log unauthenticated users...
    jsonschema.validate(event, schema)
    event = remove_unvalidated_fields(event, schema)

    # prepare value property (allows to store most indicative value to log table... eg.g rating)
    event['value'] = None

    # FETCH DATA
    # ASSEMBLY: MONITORING
    assembly = _MonitoredAssemblyEvents(request, response, event)

    # STAGE: MONITORING
    _MonitorStageEvents(request, response, event)

    # CONTENT: MONITORING
    _MonitorContentEvents(request, response, event)
    _MonitorPeerReviewEvents(request, response, event)


    # PLUGIN EVENTS
    ##################################################
    # THIS allows to hook into any monitoring actions...
    # PLUGIN_MODULES['MONITOR']
    # plugin_name = PLUGIN_EVENTS.get(event_string)
    # if plugin_name:
    #     # Note: it is possible to overwrite Core App monitors within plugins...
    #     plugin = plugins.__dict__[plugin_name]
    #     module = plugin.__dict__['monitors'].__dict__[event_string]
    #     response.append(module.monitor(request))
    ##################################################
   
    elog = DBLog.create_from_json(
        user_id=request.local_userid,
        assembly_id=assembly.id if assembly else None,
        contenttree_id=int(event['data'].get('contenttreeID')) if event['data'].get('contenttreeID') else None,
        content_id=int(event['data'].get('contentID')) if event['data'].get('contentID') else None,
        peerreview_id=int(event['data'].get('peerreviewID')) if event['data'].get('peerreviewID') else None,
        stage_id=int(event['data'].get('stageID')) if event['data'].get('stageID') else None,
        action=event.get('eventString'),
        value=event.get('value'),
        ip=request.client_addr,
        date_created=arrow.get(event['date'])
    )

    if event['data'].get('extra'):
        elog.extra = event['data'].get('extra')

    assert elog.user_id, "elog_user_id is missing"
    return elog


def _MonitoredAssemblyEvents(request, response, event):
    """
    Event is raised when user enters a stage.
    """

    if event.get('eventString') == "NOTIFICATION_SHOW":
        if "NOTIFICATION_SHOW" not in request.processed_events:
            """ Notfication menu has been expanded => show all as read.."""
            request.dbsession.execute(
                """
                UPDATE notification SET is_read = 1, date_last_interaction = '%s' WHERE user_id = %s
                """ % (arrow.utcnow(), request.local_userid)
            )
            mark_changed(request.dbsession)

    assembly_tuple = factory_assembly_tuple(request, response, event)
    return assembly_tuple.get('assembly') if assembly_tuple else None


def _MonitorStageEvents(request, response, event):
    """
    Event is raised when user enters a stage.
    """

    stagetuple = factory_stage_tuple(request, response, event)

    if event.get('eventString') == "STAGE.UNALERT":
        assert stagetuple, "stage tuples are not transmitted...."
        stage = stagetuple.get('stage')
        progression = stagetuple.get('progression')
        assert request.has_permission('observe', stage), "no observe permissions..."
        progression.setUnalert()

        raiseEvent = EventStageUnalert(
            request=request,
            stage=stage,
            progression=stagetuple.get('progression'))
        request.registry.notify(raiseEvent)

    if event.get('eventString') == "STAGE.COMPLETED":
        assert stagetuple, "stage tuples not yet transmitted"
        stage = stagetuple.get('stage')
        progression = stagetuple.get('progression')
        assert request.has_permission('observe', stage), "no oberve permission"
        progression.complete()
        raiseEvent = EventStageCompleted(
            request=request,
            stage=stage,
            progression=progression)
        request.registry.notify(raiseEvent)

    if event.get('eventString') == "STAGE.RANDOM_SAMPLING_CONTENT":
        assert stagetuple, "stage tuples not yet transmitted"
        stage = stagetuple.get('stage')
        progression = stagetuple.get('progression')
        assert request.has_permission('observe', stage), "no oberve permission"

        assert stage.custom_data.get('RANDOM_FOCUS')
        excluded_from_random = stage.custom_data.get('EXCLUDE_FROM_RANDOM')
        contenttree_id = stage.contenttree_id

        treema = ContentTreeManager(request, contenttree=request.contenttree)
        topics = treema.load_toppic_contents(contenttree_id, excluded_from_random)
        content = random.sample(topics, 1)[0]
        # Seek all topic contents...
        assert content
        progression.setFocusedContent(content)
        event['value'] = str(content.id)
    
        raiseEvent = EventStageFocusContent(
            request=request,
            stage=stage,
            response=response,
            progression=progression,
            content=content)
        request.registry.notify(raiseEvent)


def _MonitorContentEvents(request, response, event):
    """
    Event is raised when user enters a stage.
    """

    contenttuple = factory_content_tuple(request, response, event)
    # Note: contenttree is loaded as contenttuple.get('content).contenttree
    # PROCESS EVENTS
    if event.get('eventString') == "CONTENT.SALIENCE":
        assert contenttuple, "contenttuple is missing"
        content = contenttuple.get('content')
        assert request.has_permission('saliencing', content), "saliencing permission is missing."
        salience = int(event['data'].get('salience'))
        progression = contenttuple.get('progression')
        prior = progression.salience
        progression.set_salience(salience)
        raiseEvent = EventContentSalienced(
            request=request,
            content=content,
            progression=progression,
            prior=prior)
        request.registry.notify(raiseEvent)
        event['value'] = str(salience)

    if event.get('eventString') == "CONTENT.RATING":
        assert contenttuple, "contenttuple is not transmitted"
        content = contenttuple.get('content')
        assert request.has_permission('rating', content), "rating permission is missing.,"
        rating = int(event['data'].get('rating'))
        progression = contenttuple.get('progression')
        prior = progression.rating
        progression.set_rating(rating)
        event['value'] = str(rating)

        # TODO: prior does not work, right? by ref.
        raiseEvent = EventContentRated(
            request=request,
            content=contenttuple.get('content'),
            progression=contenttuple.get('progression'),
            prior=prior)            
        request.registry.notify(raiseEvent)

    if event.get('eventString') == "CONTENT.READ":
        assert contenttuple, "contenttuple is missing"
        content = contenttuple.get('content')
        assert request.has_permission('observe', content), "observe permission for this content is missing."
        progression = contenttuple.get('progression')
        raiseEvent = EventContentRead(
            request=request,
            content=contenttuple.get('content'),
            progression=contenttuple.get('progression'))
        request.registry.notify(raiseEvent)

    if event.get('eventString') == "CONTENT.DISCUSSED":
        assert contenttuple, "contentuple is missing"
        content = contenttuple.get('content')
        assert request.has_permission('observe', content), "no observe permission for this content."
        progression = contenttuple.get('progression')
        
        # is there a topic id transmitted? 
        raiseDiscussedEvent = EventSetContentAsDiscussed(
            request=request,
            progression=progression,
            content=content)
        request.registry.notify(raiseDiscussedEvent)

    if event.get('eventString') == "CONTENT.REVIEWED":
        assert contenttuple, "contenttuple is missing "
        content = contenttuple.get('content')
        assert request.has_permission('manage', content), "manage permission is missing..."
        # Mark as reviewed
        content.set_reviewed()

    if event.get('eventString') == "STAGE.FOCUSED.CONTENT":
        assert contenttuple, "contentuple is missing"
        content = contenttuple.get('content') 
        assert request.has_permission('observe', content)     , "observe permission is missing."   
        assert content and not content.parent_id

        # get stage progression
        stage_id = event['data'].get('stageID')
        assert stage_id, "stageId is not specified..."
        stagetuple = response['stages'].get(stage_id)
        assert stagetuple, "stagetuple is missing."
        progression = stagetuple.get('progression')
        stage = stagetuple.get('stage')
        assert request.has_permission('observe', stage), "observe permission is missing."   
        assert stage.custom_data is None or stage.custom_data.get('RANDOM_FOCUS') is None

        progression.setFocusedContent(content)
        raiseEvent = EventStageFocusContent(
            request=request,
            stage=stagetuple.get('stage'),
            progression=stagetuple.get('progression'),
            content=content)
        request.registry.notify(raiseEvent)

    # is there a topic id transmitted? 
    # (highest content in hierarchy  )
    topic_id = int(event['data'].get('topicID')) if event['data'].get('topicID') else None
    topic_tuple = response['contents'].get(topic_id) if topic_id else None
    if topic_tuple:
        raiseReadEvent = EventContentRead(
            request=request,
            progression=progression,
            content=content,
            topic_progression=topic_tuple['progression'])
        request.registry.notify(raiseReadEvent)


def _MonitorPeerReviewEvents(request, response, event):
    """
    Event is raised when user enters a stage.
    """

    peerreviewtuple = factory_peerreview_tuple(request, response, event)

    # PEERREVIEW EVENTS
    if event.get('eventString') == "PEERREVIEW.RESPONSE":

        assert peerreviewtuple, "peerreviewtuple is missing"
        peerreview = peerreviewtuple.get('peerreview')
        content = peerreview.content
        content.setup_lineage(request)
        content.__acl__
        assert request.has_permission('delegate', content), "delegate permission is missing."
        peerreview_response = event['data'].get('response')
        criteria_accept1 = event['data'].get('criteria_accept1')
        criteria_accept2 = event['data'].get('criteria_accept2')
        criteria_accept3 = event['data'].get('criteria_accept3')

        progression = peerreviewtuple.get('progression')
        assert progression, "progression entry must already exist!!!!"
        peerreview = peerreviewtuple.get('peerreview')

        assert peerreview_response is True or peerreview_response is False
        assert criteria_accept1 is not None and isinstance(criteria_accept1, bool)
        assert criteria_accept2 is not None and isinstance(criteria_accept2, bool)
        assert criteria_accept3 is not None and isinstance(criteria_accept3, bool)

        # already closed? (ignored statment...)
        # feedback only when outcome conflicts with own response... (this would be irritating)
        if not peerreview_response:
            if (peerreview.approved and peerreview_response is False) or \
                    (peerreview.rejected and peerreview_response is True):
                errorObj = {
                    'event': event,
                    'message': 'PEERREVIEW_ALREADY_CLOSED_USER_RESPONSE_IGNORED'
                }
                response['warnings'].append(errorObj)

        if peerreview.rejected or peerreview.approved:
            # just ignore. No need to inform the user...
            return None
            
        response_changed = progression.response != peerreview_response
        progression.set_response(peerreview_response, criteria_accept1, criteria_accept2, criteria_accept3)
        event['value'] = str(progression.response)
        if response_changed:
            peerreview.check(request)
