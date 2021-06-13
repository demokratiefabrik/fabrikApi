""" Content Views. CRUD & Ratings """
from pyramid.httpexceptions import HTTPBadRequest
from fabrikApi.models.lib.core import get_or_create_progression
from fabrikApi.models.contenttree.content import DBContentProgression
from fabrikApi.util.events import EventContentCreated, EventPeerReviewInitialized
import logging

from cornice.service import Service

from fabrikApi.models import DBContent
# from fabrikApi.models.contenttree.content import validate_parent_and_type_data
from fabrikApi.models.contenttree.content_peerreview import DBContentPeerReview, \
    initiate_peer_review
from fabrikApi.views.content.meta import content_schema, content_validator
from fabrikApi.views.lib.factories import ContentManagerFactory, ContentTreeManagerFactory
from fabrikApi.views.lib.helpers import remove_unvalidated_fields

logger = logging.getLogger(__name__)


service_content_create = Service(
    cors_origins=('*',), 
    name='content_add',
    description='Create content.',
    path='/assembly/{assembly_identifier}/contenttree/{contenttree_id:\d+}/addcontent',
    traverse='/{contenttree_id}',
    factory=ContentTreeManagerFactory)


@service_content_create.post(
    schema=content_schema, validators=(content_validator,),
    permission='add', content_type="application/json")
def content_create(request):
    """Creates a new entry."""

    # SANITIZE JSON DATA
    jsoncontent = request.json_body['content']
    # remove unvalidated attributes from the content dict
    jsoncontent = remove_unvalidated_fields(jsoncontent, content_schema)

    # PREPARE DB OBJECT
    # Create a new content object (even if peer-review is still ongoing)
    newentry = DBContent(
        text=jsoncontent.get('text'),
        title=jsoncontent.get('title'),
        type_=jsoncontent.get('type'),
        contenttree_id=request.contenttree.id,
        user_id=request.local_userid,
        parent_id=jsoncontent.get('parent_id'))
    newentry.contenttree = request.contenttree
    # newentry.patch()
    newentry.setup_lineage(request) 
    
    # EVERYTHING okay. Update DB
    request.dbsession.add(newentry)
    request.dbsession.flush()

    # VALIDATE DATA:
    if newentry.parent_id:
        assert newentry.db_parent, "no parent could be loaded... (is it missing?)"
        newentry.db_parent.patch()
    assert newentry.validate_parent_and_type_data(), "content type is not valid..."
    assert newentry.path, "path is empty. "
    assert request.has_permission('add', newentry)

    # Create content progression
    progression = get_or_create_progression(
        request,
        DBContentProgression,
        user_id=request.local_userid,
        content_id=newentry.id)

    progression.set_read()

    # Notify Event
    raiseEvent = EventContentCreated(
        request=request,
        content=newentry,
        progression=progression)
    request.registry.notify(raiseEvent)
    
    return({
        'OK': True,
        'content': {
            'path': newentry.path,
            'creator': request.current_user,
            'content': newentry,
            'progression': progression}
    })


service_content_propose_insert = Service(
    cors_origins=('*',),
    name='content_propose_insert',
    description='Propose new content.',
    path='/assembly/{assembly_identifier}/contenttree/{contenttree_id:\d+}/propose',
    traverse='/{contenttree_id}',
    factory=ContentTreeManagerFactory)

@service_content_propose_insert.post(
    schema=content_schema,
    validators=(content_validator,),
    permission='propose_add',
    content_type="application/json")
def propse_content(request):
    """Propose a new entry."""

    # SANITIZE JSON DATA
    jsoncontent = request.json_body['content']
    jsoncontent = remove_unvalidated_fields(jsoncontent, content_schema)

    # PREPARE DB OBJECT
    # Create a new content object (even if peer-review is still ongoing)
    newentry = DBContent(
        text=jsoncontent.get('text'),
        title=jsoncontent.get('title'),
        type_=jsoncontent.get('type'),
        contenttree_id=request.contenttree.id,
        user_id=request.local_userid,
        parent_id=jsoncontent['parent_id'])
    # newentry.contenttree = request.contenttree
    # newentry.disabled = True
    newentry.pending_peerreview_for_insert = True

    # try to add new content (as disabled)
    request.dbsession.begin_nested()  # establish a savepoint (to simulate modifications)
    # VALIDATE DATA:
    request.dbsession.add(newentry)
    request.dbsession.flush()
    newentry.setup_lineage(request)
    val1 = newentry.validate_parent_and_type_data(), "content type is not valid..."
    val2 = newentry.path, "path is empty. "
    val3 = request.has_permission('propose_add', newentry)
    if not val3 or not val2 or not val1:
        request.dbsession.rollback()  # rolls back simulation
        raise HTTPBadRequest
    
    # PEER REVIEW HANDLER
    # Add PeerReview (Type: INSERT) Object
    # Content is marked as peerreviewd only after peerreview has been successfull)
    peerreview = initiate_peer_review(
        request,
        operation=DBContentPeerReview.INSERT,
        content=newentry,
        user_created_id=request.local_userid
        # Close peerreview flag after peer review has been passed.
    )

    # Create content progression
    progression = get_or_create_progression(
        request,
        DBContentProgression,
        user_id=request.local_userid,
        content_id=newentry.id)

    # Notify Event
    raiseEvent = EventPeerReviewInitialized(
        request=request,
        content=newentry,
        peerreview=peerreview)
    request.registry.notify(raiseEvent)
    
    return({
        'OK': True,
        'content': {
            'path': newentry.path,
            'creator': request.current_user,
            'content': newentry,
            'progression': progression},
        'peerreview': {
            'creator': request.current_user,
            'content': newentry,
            'peerreview': peerreview}
    })
