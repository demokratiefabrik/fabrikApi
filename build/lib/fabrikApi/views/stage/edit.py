""" Stage (Full-Content Views): """

import logging
import arrow

from fabrikApi.views.lib.helpers import remove_unvalidated_fields
from fabrikApi.views.stage.meta import service_stage_id, stage_schema,\
                                           stage_validator

logger = logging.getLogger(__name__)


@service_stage_id.post(
    schema=stage_schema, validators=(stage_validator,), permission='manage',
    content_type="application/json")
def stage_edit(request):
    """Edits a content."""

    assert request.assembly, "invalid assembly"
    assert request.stage, "invalid stage"

    # SANITIZE JSON DATA
    jsoncontent = request.json_body['stage']
    assert request.stage.id == jsoncontent['id'], "invalid stage_id"
    stage = remove_unvalidated_fields(jsoncontent, stage_schema)

    new_order_position = request.stage.order_position != stage['order_position']
    # update order position if needed
    if new_order_position:
        # The list of stages attached to the assembly becomes rewritten
        # request.dbsession.refresh(request.assembly)
        # request.stage.order_position = stage['order_position']
        request.assembly.stages.remove(request.stage)
        request.assembly.stages.insert(stage['order_position']-1, request.stage)
        request.assembly.stages.reorder()
        # request.assembly.stages.reorder()

    # all other values...
    # update values
    request.stage.title = stage['title']
    request.stage.info = stage['info']
    request.stage.group = stage['group']
    # request.stage.contenttree_id = stage['contenttree_id']
    request.stage.type_ = stage['type']
    request.stage.custom_data = stage['custom_data']
    request.date_modified = arrow.now()
    request.stage.disabled = stage['disabled']
    request.stage.date_end = arrow.get(stage['date_end']) if stage['date_end'] else None
    request.stage.date_start = arrow.get(stage['date_start']) if stage['date_start'] else None

    stages = request.assembly.get_stages_with_view_permission(request)

    # assembly remains untouched
    return({
        'stages': stages,
        'assembly': request.assembly
    })
