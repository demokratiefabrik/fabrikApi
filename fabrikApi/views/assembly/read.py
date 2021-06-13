""" Assembly Read. """

import logging
import arrow
from cornice.service import Service
from fabrikApi.models.assembly import get_assembly_progression_of_current_user
from fabrikApi.views.lib.factories import AssemblyFactory
from fabrikApi.models.lib.plugin_interfaces import PLUGIN_MODULES

logger = logging.getLogger(__name__)


# SERVICES
assembly = Service(cors_origins=('*',), 
    name='assembly', description='Read/List/Manage Assemblies.',
    path='/assembly/{assemby_identifier}',
    traverse='/{assemby_identifier}',
    factory=AssemblyFactory)


@assembly.get(permission='observe')
def get_assembly(request):
    """Returns the public and user-specific information about an **assembly**.
    """

    # Check if assembly is already loaded by cornice factory
    # TODO: wrong place here. (do it in the factory...)
    assert request.has_observe_permission(request.assembly), "no observe permission for this assembly."

    # Load progression
    if request.local_userid:
        if not request.assembly.__progression__:
            # __progression__ should have been populated in setup_lineage (view factories))
            # Hencce: create a new entry... (AUTOCREATE iS set to True by default...)
            request.assembly.__progression__ = get_assembly_progression_of_current_user(request)

    stages = request.assembly.get_stages_with_view_permission(request)
    
    # Load available contenttree configurations
    configuration = None
    if request.has_administrate_permission or request.assembly.is_manager:
        configuration = {
            'STAGE_TYPES': PLUGIN_MODULES['STAGE'],
            'MAX_DAILY_USER_COMMENTS': request.assembly.MAX_DAILY_USER_COMMENTS,
            'MAX_DAILY_USER_PROPOSALS': request.assembly.MAX_DAILY_USER_PROPOSALS
        }
    else:
        configuration = {
            'MAX_DAILY_USER_COMMENTS': request.assembly.MAX_DAILY_USER_COMMENTS,
            'MAX_DAILY_USER_PROPOSALS': request.assembly.MAX_DAILY_USER_PROPOSALS
        }

    return({'assembly': request.assembly,
            'stages': stages,
            'progression': request.assembly.__progression__,
            'configuration': configuration,
            'access_date': arrow.utcnow(),
            'access_sub': request.authenticated_userid
            })
