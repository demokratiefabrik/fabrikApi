""" ContentTree (Full-Content Views): """
import logging
from fabrikApi.views.contenttree.meta import service_contenttree_id

logger = logging.getLogger(__name__)


@service_contenttree_id.get(permission='observe')
def contenttree_read(request):
    """Returns the contenttree data."""

    return({
        'contenttree': request.contenttree,
        'progresssion': request.contenttree_progresssion
    })
