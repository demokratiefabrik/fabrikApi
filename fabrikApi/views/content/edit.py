""" Content Views. CRUD & Ratings """

from fabrikApi.models.contenttree.content import DBContentProgression
from fabrikApi.util.events import EventContentDeleted, EventContentEdited, EventContentMoved, EventPeerReviewInitialized
import arrow
from fabrikApi.models.lib.core import get_or_create_progression
from cornice.service import Service
from fabrikApi.views.lib.factories import ContentManagerFactory
import logging

from fabrikApi.models import DBContentPeerReview, DBContent
from fabrikApi.models.contenttree.content_peerreview import initiate_peer_review
from fabrikApi.views.content.meta import content_schema, content_validator
from fabrikApi.views.lib.helpers import remove_unvalidated_fields

logger = logging.getLogger(__name__)


service_content_save = Service(cors_origins=('*',), 
    name='service_content_modify',
    description='Edit / View / Delete a content.',
    path='/assembly/{assembly_identifier}/content/{content_id:\d+}/save',
    traverse='/{content_id}',
    factory=ContentManagerFactory)

@service_content_save.post(
    schema=content_schema,
    validators=(content_validator,),
    permission='modify',
    content_type="application/json"
    )
def content_save(request):
    """Edits an entry."""
    
    # SANITIZE JSON DATA
    jsoncontent = request.json_body['content']
    editedcontent = remove_unvalidated_fields(jsoncontent, content_schema)

    # type and parent modification proposals are only implemented for managers.
    is_it_a_type_modification = editedcontent['type'] != request.content.type_
    assert not is_it_a_type_modification or request.assembly.is_manager, "only managers can modify type"
    is_it_a_parent_modification = 'parent_id' in editedcontent and jsoncontent['parent_id'] != request.content.parent_id
    assert not is_it_a_parent_modification or request.assembly.is_manager, "only managers can modify parent_id."
    is_it_a_deletion = jsoncontent.get('disabled') and not request.content.disabled

    # TODO: how to prevent circular hierarchies?

    # PEER REVIEW HANDLER
    # Open new Modificaction Peer Review

    # update values
    request.content.title = editedcontent['title']
    request.content.text = editedcontent['text']
    request.content.parent_id = editedcontent['parent_id']
    request.content.type_ = editedcontent['type']
    request.content.date_modified = arrow.now()
    request.content.disabled = editedcontent['disabled']

    assert request.content.validate_parent_and_type_data(), "invalid type/parent setting."
    assert request.content.patched, "content should be patched here.."

    if not request.assembly.is_manager:
        request.content.reviewed = False

    # TODO: check type specific max length....
    # CONTENT_TITLE_MAX_LENGTH_BY_TYPES
    
    # Create content progression
    progression = get_or_create_progression(
        request,
        DBContentProgression,
        user_id=request.local_userid,
        content_id=request.content.id)

    # Notify Event
    if is_it_a_deletion:
        raiseEvent = EventContentDeleted(
            request=request,
            progression=progression,
            content=request.content)
        request.registry.notify(raiseEvent)

    elif is_it_a_parent_modification:

        # TODO: two notifications for simultanious edit and moves
        raiseEvent = EventContentMoved(
            request=request,
            progression=progression,
            content=request.content)
        request.registry.notify(raiseEvent)

    else:

        raiseEvent = EventContentEdited(
            request=request,
            progression=progression,
            content=request.content)
        request.registry.notify(raiseEvent)

    # Prepare Response Object
    response = {
        'OK': True,
        'content': {'content': request.content}
    }

    return(response)


service_content_propose = Service(cors_origins=('*',), 
    name='service_content_modify_propose', description='Edit / View / Delete a content.',
    path='/assembly/{assembly_identifier}/content/{content_id:\d+}/propose',
    traverse='/{content_id}',
    factory=ContentManagerFactory)


@service_content_propose.post(
    schema=content_schema,
    validators=(content_validator,),
    permission='propose_modify',
    content_type="application/json"
    )
def content_modify_propose(request):
    """Edits an entry."""
    
    assert not request.content.pending_peerreview_for_update
    assert not request.content.pending_peerreview_for_insert

    # SANITIZE JSON DATA
    jsoncontent = request.json_body['content']
    jsoncontent = remove_unvalidated_fields(jsoncontent, content_schema)
    
    # type and parent modification proposals are not yet implentent.
    is_it_a_type_modification = 'type' in jsoncontent and jsoncontent.get('type') != request.content.type_
    assert not is_it_a_type_modification, "NOT YET IMPLEMENTED: is_it_a_type_modification"
    is_it_a_parent_modification = 'parent_id' in jsoncontent and jsoncontent['parent_id'] != request.content.parent_id
    assert not is_it_a_parent_modification, "NOT YET IMPLEMENTED: is_it_a_parent_modification"

    peerreview = initiate_peer_review(
        request,
        operation=DBContentPeerReview.UPDATE,
        content=request.content,
        user_created_id=request.local_userid,
        data_to_apply_on_success={'title': jsoncontent.get('title'), })

    request.content.pending_peerreview_for_update = True

    # Validate data by simulating modifications
    # START SIMULATION -------------------------------
    request.dbsession.begin_nested()  # establish a savepoint (to simulate modifications)
    peerreview.approve(request)
    assert peerreview.content.validate_parent_and_type_data(), "invalid parent/type setting"
    request.dbsession.rollback()  # rolls back simulation
    # END SIMULATION -------------------------------

    # EVERYTHING VALIDATED: 
    # Discussion entry: Entry to the contenttree to allow discussion...
    updateproposal = DBContent(
        title=jsoncontent.get('title'),
        text=jsoncontent.get('text'),
        type_='UPDATEPROPOSAL',
        contenttree_id=request.contenttree.id,
        user_id=request.local_userid,
        parent_id=request.content.id)
    request.dbsession.add(updateproposal)
    request.dbsession.flush()

    # Create content progression
    progression = get_or_create_progression(
        request,
        DBContentProgression,
        user_id=request.local_userid,
        content_id=updateproposal.id)

    # now, we can add the peerreview object to the session.
    request.dbsession.add(peerreview)
    request.dbsession.flush()
    peerreview.discussion_content_id = updateproposal.id

    response = {
        'OK': True,
        'content': {
            'creator': request.current_user,
            'content': updateproposal,
            'progression': progression
        },
        'peerreview': {
            'creator': request.current_user,
            'content': request.content,
            'peerreview': peerreview
        }
    }

    # Notify Event
    raiseEvent = EventPeerReviewInitialized(
        request=request,
        response=response,
        content=request.content,
        peerreview=peerreview)
    request.registry.notify(raiseEvent)

    return response
