""" Assembly Views. """
from fabrikApi.views.assembly.meta import assembly_validator, assembly_schema, service_assembly_form_id
from fabrikApi.views.lib.helpers import remove_unvalidated_fields
import arrow
import logging

logger = logging.getLogger(__name__)


@service_assembly_form_id.post(
    schema=assembly_schema, validators=(assembly_validator,), permission='manage',
    content_type="application/json")
def assembly_edit(request):
    """Edits a content."""

    assert request.assembly, "invalid assembly"

    # SANITIZE JSON DATA
    jsoncontent = request.json_body['assembly']
    assert request.assembly.id == jsoncontent['id'], "Invalid assembly_id"
    assembly = remove_unvalidated_fields(jsoncontent, assembly_schema)

    # update values
    request.assembly.title = assembly['title']
    request.assembly.text_background = assembly['background']
    request.assembly.info = assembly['info']
    request.assembly.type = assembly['type']
    request.assembly.date_modified = arrow.now()
    request.assembly.disabled = assembly['disabled']
    request.assembly.date_end = arrow.get(assembly['date_end']) if assembly['date_end'] else None
    request.assembly.date_start = arrow.get(assembly['date_end']) if assembly['date_start'] else None

    # assembly remains untouched
    return({
        'assembly': request.assembly
    })
