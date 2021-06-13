""" Stage Create  Views """

import copy

import arrow
from fabrikApi.views.lib.helpers import remove_unvalidated_fields
import logging
import dateutil.parser

from fabrikApi.models import DBStage
from fabrikApi.views.stage.meta import service_stage, stage_schema, stage_validator


logger = logging.getLogger(__name__)


# stage_schema_create = copy.deepcopy(stage_schema)
# stage_schema_create["properties"]["type"] = {"type": "string"}

@service_stage.post(
    schema=stage_schema, validators=(stage_validator,),
    content_type="application/json", permission='manage')
def create_stage(request):
    """Creates new stage """

    assert request.assembly, "assembly is empty"

    jsoncontent = request.json_body['stage']
    assert not jsoncontent['id'], "stage id is missing"
    stage = remove_unvalidated_fields(jsoncontent, stage_schema)

    # Create a new Continer Entry
    request.stage = DBStage(
        assembly=request.assembly,
        type_=stage['type'])
    
    # update values
    request.stage.title = stage['title']
    request.stage.group = stage['group']
    request.stage.custom_data = stage['custom_data']
    request.stage.info = stage['info']
    request.stage.disabled = stage['disabled']
    # request.stage.icon = stage['icon']
    request.stage.date_end = arrow.get(stage['date_end']) if stage['date_end'] else None
    request.stage.date_start = arrow.get(stage['date_start']) if stage['date_start'] else None
    request.stage.order_position = stage['order_position']
    request.dbsession.add(request.stage)

    # flush
    request.dbsession.flush()

    # update order position if needed
    request.dbsession.refresh(request.assembly)

    request.assembly.stages.insert(stage['order_position'], request.stage)
    request.assembly.stages.reorder()

    # report also new ordered list of stages
    # and report also stage progressions
    request.assembly.include_extra_data = True
    stages = request.assembly.get_stages_with_view_permission(request)

    # assembly remains untouched
    return({
        'stages': stages,
        'assembly': request.assembly
    })
