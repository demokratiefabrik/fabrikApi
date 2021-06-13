""" ContentTree (Full-Content Views): """
import logging
from fabrikApi.views.contenttree.meta import service_contenttree_update
from fabrikApi.views.content.meta import content_validator
from fabrikApi.views.lib.helpers import remove_unvalidated_fields


logger = logging.getLogger(__name__)

contenttree_update_schema = {
    "type": "object",
    "properties": {
        "update_date": {"type": ["string"], "format": "date-time"},
    },
    "required": ["update_date"]
}


@service_contenttree_update.post(
    permission='observe',
    schema=contenttree_update_schema,
    validators=(content_validator,),
)
def contenttree_update(request):
    """Returns modified / and newly added contenttree data."""

    # SANITIZE JSON DATA
    jsoncontent = request.json_body['content']
    data = remove_unvalidated_fields(jsoncontent, contenttree_update_schema)

    assert data['update_date'], "update_date must be specified."

    return({
        'progresssion': request.contenttree_progresssion
    })
