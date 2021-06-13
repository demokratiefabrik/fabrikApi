""" List all Content of a specific ContentTree """

import logging
from cornice.service import Service

from fabrikApi.util.contenttree_manager import ContentTreeManager
from fabrikApi.views.lib.factories import ContentTreeManagerFactory


logger = logging.getLogger(__name__)

service_content_tree = Service(
    cors_origins=('*',),
    name='contenttree_route',
    description='List contenttree.',
    path='/assembly/{assembly_identifier}/contenttree/{contenttree_id:\d+}/contenttree',
    traverse='/{contenttree_id}',
    factory=ContentTreeManagerFactory)

@service_content_tree.get(permission='observe')
def tree_content(request):
    """Returns all content of a given contenttree."""
    assert request.contenttree.patched, "contenttree should be patched here..."

    # Load ContentTree Content
    treema = ContentTreeManager(request, contenttree=request.contenttree)
    contenttree = treema.load_content()

    # Load available contenttree configurations
    configuration = request.contenttree.get_configuration(request)

    return({
        'OK': True,
        'configuration': configuration,
        'contenttree': contenttree
    })
