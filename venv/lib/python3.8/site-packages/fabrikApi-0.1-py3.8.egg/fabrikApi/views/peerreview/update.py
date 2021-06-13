""" List updated Peerreviews entries of a specific ContentTree """

import arrow
from fabrikApi.views.lib.helpers import remove_unvalidated_fields
from fabrikApi.views.content.meta import content_validator
import logging
from cornice.service import Service
from fabrikApi.util.peerreview_manager import PeerreviewManager
from fabrikApi.views.lib.factories import ContentTreeManagerFactory

logger = logging.getLogger(__name__)

peerreview_update_schema = {
    "type": "object",
    "properties": {
        "update_date": {"type": ["string"], "format": "date-time"},
    },
    "required": ["update_date"]
}

service_peerreview_update = Service(
    cors_origins=('*',), 
    name='peerreview_update_route',
    description='Create or List content.',
    path='/assembly/{assembly_identifier}/contenttree/{contenttree_id:\d+}/peerreviewupdate',
    traverse='/{contenttree_id}',
    factory=ContentTreeManagerFactory)


@service_peerreview_update.post(
    permission='observe',
    schema=peerreview_update_schema,
    validators=(content_validator,)
)
def content_tree_update(request):
    """Returns all content of a given contenttree."""
    assert request.contenttree.patched, "contenttree should be patched here..."

    # SANITIZE JSON DATA
    jsoncontent = request.json_body['content']
    data = remove_unvalidated_fields(jsoncontent, peerreview_update_schema)
    modificationDate = data['update_date']
    assert modificationDate, "modification date is missing (invalid format?)"
    
    # Load Peerreviews
    peerreview_manager = PeerreviewManager(request, contenttree=request.contenttree)
    content_peerreviews = peerreview_manager.load_modified_peerreviews(modificationDate)

    return({
        'OK': True,
        'update_date': arrow.utcnow(),
        'peerreviews': content_peerreviews
    })
