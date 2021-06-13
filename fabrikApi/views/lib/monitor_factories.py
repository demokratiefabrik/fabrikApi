"""
The following Events can be raised by Clients via API requests /notify/CLASSNAME.
This allows to inform the API about user activities that take only place on the client side.
"""

from fabrikApi.models.contenttree.content_peerreview import DBContentPeerReview, DBContentPeerReviewProgression
import logging
import jsonschema

from fabrikApi.models.assembly import DBAssemblyProgression,\
  get_assembly_by_identifier
from fabrikApi.models.lib.core import get_or_create_progression
from fabrikApi.models.stage import DBStage, DBStageProgression
from fabrikApi.models.contenttree.content import DBContent, DBContentProgression

from fabrikApi.util.events import EventAssemblyVisit, EventContentVisit, \
    EventFirstAssemblyVisit, EventFirstContentVisit, EventFirstPeerReviewVisit, EventFirstStageVisit, EventPeerReviewVisit, \
    EventStageVisit
from fabrikApi.views.lib.helpers import remove_unvalidated_fields

logger = logging.getLogger(__name__)


def factory_assembly_tuple(request, response, event):

    if 'assemblies' not in response:
        response['assemblies'] = {}

    if 'data' not in event:
        return None

    # SANITIZE Assembly DATA
    schema = {
        "type": "object",
        "properties": {
            "assemblyIdentifier": {"type": "string"},
        },
        "required": []
    }
    jsonschema.validate(event['data'], schema)
    data = remove_unvalidated_fields(event['data'], schema)

    assembly_identifier = data.get('assemblyIdentifier')
    if not assembly_identifier:
        # no assembly action or assembly action already handled...
        return None

    if assembly_identifier in response['assemblies']:
        # no assembly action or assembly action already handled...
        return response['assemblies'].get(assembly_identifier)

    assembly = get_assembly_by_identifier(request, assembly_identifier)
    request.assembly = assembly
    # assembly.patch()
    assembly.setup_lineage(request)
    assert request.has_observe_permission(assembly), "no observe permission for the assembly."

    # Get AssemblyProgression
    assembly_progression = get_or_create_progression(
        request,
        DBAssemblyProgression,
        event_when_creating_entry=EventFirstAssemblyVisit,
        event_when_reusing_entry=EventAssemblyVisit,
        user_id=request.local_userid,
        is_manager=assembly.is_manager,
        assembly=assembly)

    assemblytuple = {
        'assembly': assembly,
        'progression': assembly_progression
        }

    # Return object, if it just has been created.
    # if assembly_progression.date_created >= now:
    response['assemblies'][assembly_identifier] = assemblytuple

    return assemblytuple


def factory_stage_tuple(request, response, event):
    """
    Event is raised when user enters a stage.
    """

    if 'stages' not in response:
        response['stages'] = {}

    if 'data' not in event:
        return None

    stage_id = int(event['data'].get('stageID')) if event['data'].get('stageID') else None
    if not stage_id:
        # no stage action...
        return None
        
    if stage_id in response['stages']:
        # no stage action or stage action already handled...
        return response['stages'].get(stage_id)

    stage = request.dbsession.query(DBStage).get(stage_id)
    assert stage, "stage is missing"
    # stage.patch()
    stage.setup_lineage(request)
    request.assembly = stage.assembly
    assert request.has_observe_permission(stage), "no observe permission for the stage..."
    # stage.patch()

    # Get StageProgression
    progression = get_or_create_progression(
        request,
        DBStageProgression,
        auto_create=True,
        event_when_creating_entry=EventFirstStageVisit,
        event_when_reusing_entry=EventStageVisit,
        user_id=request.local_userid,
        stage=stage,
        stage_id=stage.id)

    stagetuple = {
        'stage': stage,
        'progression': progression}

    response['stages'][int(stage_id)] = stagetuple

    return stagetuple


def factory_content_tuple(request, response, event):
    if 'contents' not in response:
        response['contents'] = {}

    if 'data' not in event:
        return None

    content_id = int(event['data'].get('contentID')) if event['data'].get('contentID') else None
    if not content_id:
        # no content action...
        return None
        
    if content_id in response['contents']:
        # no content action or content action already handled...
        return response['contents'].get(content_id)

    content = request.dbsession.query(DBContent).get(content_id)
    assert content, "no content transmitted..."
    # content.patch()
    content.setup_lineage(request)

    assemblyIdentifier = event['data'].get('assemblyIdentifier')
    assert assemblyIdentifier, "No assemblyIdentifier...."
    assert response['assemblies'][assemblyIdentifier], "assembly is not yet in cache..."
    assembly = response['assemblies'][assemblyIdentifier]['assembly']
    assert request.has_observe_permission(content), "no observe permission for this content..."

    # Get ContentProgression
    progression = get_or_create_progression(
        request,
        DBContentProgression,
        auto_create=True,
        event_when_creating_entry=EventFirstContentVisit,
        event_when_reusing_entry=EventContentVisit,
        user_id=request.local_userid,
        content=content,
        is_manager=assembly.is_manager,
        content_id=content.id)
    
    assert factory_contenttree(request, response, event, content), "facotry for contenttree has produced an error."

    logger.info("_get_contenttree_tuple: %s " % content.id)

    contenttuple = {
        'content': content,
        'progression': progression}
    response['contents'][int(content_id)] = contenttuple

    ## TOPIC PROGRESSION
    # create also a progression entry for the topic content
    topic_id = int(event['data'].get('topicID')) if event['data'].get('topicID') else None
    if topic_id and response['contents'].get(topic_id) is None:
        # Get ContentProgression
        topic = request.dbsession.query(DBContent).get(topic_id)
        topic.setup_lineage(request)
        topic_progression = get_or_create_progression(
            request,
            DBContentProgression,
            auto_create=True,
            event_when_creating_entry=EventFirstContentVisit,
            event_when_reusing_entry=EventContentVisit,
            user_id=request.local_userid,
            is_manager=assembly.is_manager,
            content=topic,
            content_id=topic_id)
        topictuple = {
            'content': topic,
            'progression': topic_progression}
        response['contents'][topic_id] = topictuple

    # return contenttuple
    return contenttuple


def factory_contenttree(request, response, event, content):
    if 'contenttrees' not in response:
        response['contenttrees'] = {}

    if 'data' not in event:
        return None
        
    # assert content.contenttree
    contenttree = content.contenttree
    contenttree_id = contenttree.id
    # contenttree.patch()
    contenttree.setup_lineage(request)
    assert request.has_observe_permission(contenttree), "observe permissions are missing"
    assert contenttree and contenttree_id, "contenttree seems to be empty.."

    if content.contenttree_id not in response['contenttrees']:
        
        # Check if this contenttree is indeed part of the assembly in the URL!
        assemblyIdentifier = event['data'].get('assemblyIdentifier')
        assert assemblyIdentifier, "assembly Identifier is missing"
        assembly = response['assemblies'][assemblyIdentifier]['assembly']
        assert assembly, "assembly is missing.."

    # Okay, everything fine!
    return contenttree


def factory_peerreview_tuple(request, response, event):
    if 'peerreviews' not in response:
        response['peerreviews'] = {}

    if 'data' not in event:
        return None

    peerreview_id = int(event['data'].get('peerreviewID')) if event['data'].get('peerreviewID') else None
    if not peerreview_id:
        # no content action...
        return None
        
    if peerreview_id in response['peerreviews']:
        # no content action or content action already handled...
        return response['peerreviews'].get(peerreview_id)

    peerreview = request.dbsession.query(DBContentPeerReview).get(peerreview_id)
    assert peerreview, "no content transmitted..."
    peerreview.setup_lineage(request)

    assemblyIdentifier = event['data'].get('assemblyIdentifier')
    assert assemblyIdentifier, "No assemblyIdentifier...."
    assert response['assemblies'][assemblyIdentifier], "assembly is not yet in cache..."
    assembly = response['assemblies'][assemblyIdentifier]['assembly']
    assert request.has_observe_permission(peerreview), "no observe permission for this content..."

    # Get ContentProgression
    progression = get_or_create_progression(
        request,
        DBContentPeerReviewProgression,
        auto_create=False,
        event_when_creating_entry=EventFirstPeerReviewVisit,
        event_when_reusing_entry=EventPeerReviewVisit,
        user_id=request.local_userid,
        content_peerreview=peerreview,
        is_manager=assembly.is_manager,
        content_peerreview_id=peerreview.id)
    
    assert factory_contenttree(request, response, event, peerreview), "factory for contenttree has produced an error."

    logger.info("_get_contenttree_tuple: %s " % peerreview.id)

    peerreviewtuple = {
        'peerreview': peerreview,
        'progression': progression}

    response['peerreviews'][int(peerreview_id)] = peerreviewtuple

    return peerreviewtuple
