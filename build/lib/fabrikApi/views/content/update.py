""" List all Content of a specific ContentTree """

import arrow
from fabrikApi.views.lib.helpers import remove_unvalidated_fields
from fabrikApi.views.content.meta import content_validator
import logging
from cornice.service import Service
from fabrikApi.util.contenttree_manager import ContentTreeManager
from fabrikApi.views.lib.factories import ContentTreeManagerFactory

logger = logging.getLogger(__name__)

contenttree_update_schema = {
    "type": "object",
    "properties": {
        "update_date": {"type": ["string"], "format": "date-time"},
    },
    "required": ["update_date"]
}

service_content_tree_update = Service(
    cors_origins=('*',), 
    name='contenttree_route222',
    description='Create or List content.',
    path='/assembly/{assembly_identifier}/contenttree/{contenttree_id:\d+}/update',
    traverse='/{contenttree_id}',
    factory=ContentTreeManagerFactory)

@service_content_tree_update.post(permission='observe',
    schema=contenttree_update_schema,
    validators=(content_validator,)
)
def content_tree_update(request):
    """Returns all content of a given contenttree."""
    assert request.contenttree.patched, "contenttree should be patched here..."

    # SANITIZE JSON DATA
    jsoncontent = request.json_body['content']
    data = remove_unvalidated_fields(jsoncontent, contenttree_update_schema)
    modificationDate = data['update_date']
    assert modificationDate, "modification date is missing (invalid format?)"
    
    # Load ContentTree Content
    treema = ContentTreeManager(request, contenttree=request.contenttree)
    contents = treema.load_modified_content(modificationDate)

    return({
        'OK': True,
        'update_date': arrow.utcnow(),
        'contents': contents
    })
