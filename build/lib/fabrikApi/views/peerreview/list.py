""" List all PeerReviews within this assembly (also the rejected and archieved) """

import logging
from cornice.service import Service

from fabrikApi.util.peerreview_manager import PeerreviewManager
from fabrikApi.views.lib.factories import ContentTreeManagerFactory


logger = logging.getLogger(__name__)

service_peerreview_list = Service(
    cors_origins=('*',), 
    name='peerreview_list',
    description='List Peerreview.',
    path='/assembly/{assembly_identifier}/contenttree/{contenttree_id:\d+}/peerreviews',
    traverse='/{contenttree_id}',
    factory=ContentTreeManagerFactory)


@service_peerreview_list.get(permission='observe')
def peerreview_list(request):
    """Returns all content of a given contenttree."""
    assert request.contenttree.patched, "assembly should be patched here..."

    # Load Peerreviews
    peerreview_manager = PeerreviewManager(request, contenttree=request.contenttree)
    content_peerreviews = peerreview_manager.load_peerreviews()

    return({
        'OK': True,
        'peerreviews': content_peerreviews
    })
