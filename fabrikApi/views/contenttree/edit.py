""" ContentTree (Full-Content Views): """

import logging
import arrow
import dateutil.parser

from fabrikApi.views.contenttree.meta import service_contenttree_id, contenttree_schema,\
                                           contenttree_validator

logger = logging.getLogger(__name__)


@service_contenttree_id.post(
    schema=contenttree_schema, validators=(contenttree_validator,), permission='manage',
    content_type="application/json")
def contenttree_edit(request):
    """Edits a content."""

    assert request.assembly, "invalid assembly"
    assert request.contenttree, "invalid contenttree"

    # get dictionary of all fields that have been validated
    contenttree = request.json_body['contenttree']
    assert request.contenttree.id == contenttree['id'], "invalid contenttree id"
    contenttree = { attr: contenttree[attr] for attr in contenttree_schema['properties'].keys()}

    # NOTE: type_ cannot be modified after creation
    assert "type" not in contenttree.keys(), "invalid contenttree type"

    # new_order_position = request.contenttree.order_position != contenttree['order_position']

    # update values
    request.contenttree.title = contenttree['title']
    request.contenttree.info = contenttree['info']
    request.contenttree.disabled = contenttree['disabled']
    request.contenttree.icon = contenttree['icon']
    request.contenttree.date_end = arrow.get(contenttree['date_end']) if contenttree['date_end'] else None
    request.contenttree.date_start = arrow.get(contenttree['date_start']) if contenttree['date_start'] else None
    # request.contenttree.order_position = contenttree['order_position']

    # update order position if needed
    # TODO move it to model in event listener (onchange)
    # if new_order_position:
    #     # The list of contenttrees attached to the assembly becomes rewritten
    #     # respecting the new order-position.
    #     request.dbsession.refresh(request.assembly)
    #     request.assembly.contenttrees.reorder()

    # enforce mdi-icon format
    # TODO move it to model in icon setter (onchange)
    # if request.contenttree.icon is not None and len(request.contenttree.icon) > 0:
    #     if not request.contenttree.icon.startswith('mdi-'):
    #         request.contenttree.icon = "mdi-%s" % request.contenttree.icon

    # report also new ordered list of contenttrees
    # and report also contenttree progressions
    # if new_order_position:
    #     request.assembly.include_extra_data = True
    #     return({'contenttree': request.contenttree,
    #             'assembly': request.assembly})

    # assembly remains untouched
    return({'contenttree': request.contenttree})
