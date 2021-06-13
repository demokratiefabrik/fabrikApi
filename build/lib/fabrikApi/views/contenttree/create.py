""" ContentTree Create  Views """

import copy
import logging
import arrow
import dateutil.parser

from fabrikApi.models import DBContentTree
from fabrikApi.views.contenttree.meta import service_contenttree, contenttree_schema, contenttree_validator


logger = logging.getLogger(__name__)


contenttree_schema_create = copy.deepcopy(contenttree_schema)
contenttree_schema_create["properties"]["type"] = {"type": "string"}

@service_contenttree.post(
    schema=contenttree_schema_create, validators=(contenttree_validator,),
    content_type="application/json", permission='manage')
def create_contenttree(request):
    """Creates new contenttree """

    assert request.assembly, "invalid assembly"

    contenttree = request.json_body['contenttree']
    contenttree = { attr: contenttree[attr] for attr in contenttree_schema['properties'].keys()}

    # Create a new Continer Entry
    request.contenttree = DBContentTree(
        assembly=request.assembly,
        type_=contenttree['type'])
    request.dbsession.add(request.contenttree)
    
    # update values
    request.contenttree.title = contenttree['title']
    request.contenttree.info = contenttree['info']
    request.contenttree.disabled = contenttree['disabled']
    request.contenttree.icon = contenttree['icon']
    request.contenttree.date_end = arrow.get(contenttree['date_end']) if contenttree['date_end'] else None
    request.contenttree.date_start = arrow.get(contenttree['date_start']) if contenttree['date_start'] else None
    # request.contenttree.order_position = contenttree['order_position']

    # flush
    request.dbsession.flush()

    # enforce mdi-icon format
    # TODO move it to model in icon setter (onchange)
    # if request.contenttree.icon is not None and len(request.contenttree.icon) > 0:
    #     if not request.contenttree.icon.startswith('mdi-'):
    #         request.contenttree.icon = "mdi-%s" % request.contenttree.icon

    # report also new ordered list of contenttrees
    # and report also contenttree progressions
    request.assembly.include_extra_data = True
    return({'contenttree': request.contenttree,
            'assembly': request.assembly})
