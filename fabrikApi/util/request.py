import ipaddress
import logging

from pyramid.request import Request

from fabrikApi.models.lib.core import get_or_create_user
from fabrikApi.util import cache
from fabrikApi.util.events import EventFirstPlatformVisit

logger = logging.getLogger(__name__)


class MoxRequest(Request):
    """
    See https://rollbar.com/blog/using-pyramid-request-factory-to-write-less-code/
    """

    # temporary storage
    # _roles = None
    assembly = None
    assembly_progression = None
    stage = None
    stage_progression = None
    contenttree = None
    contenttree_progression = None
    content = None
    content_progression = None
    processed_events = []


    @cache.CachedAttribute
    def current_user(self):
        """
        Add local_userid to request object.
        This method creates an new entry, if the user is not already registered.
        """

        user_id = self.authenticated_userid

        # Not authenticated (or public resource)
        if user_id is None:
            return None

        # GET USER FROM DB.
        current_user = get_or_create_user(
            self,
            oauth2_provider=self.jwt_claims.get('iss'),
            oauth2_user_id=user_id,
            event_when_creating_entry=EventFirstPlatformVisit)

        return(current_user)

     
    @cache.CachedAttribute
    def local_userid(self):
        """
        Add local_userid to request object.
        This method creates an new entry, if the user is not already registered.
        """
        
        if not self.current_user:
            return None

        return(self.current_user.id)

    @cache.CachedAttribute
    def has_administrate_permission(self):
        # Administrator Manager
        return len(self.jwt_claims) and 'administrator' in self.jwt_claims.get("roles")

    def has_manage_permission(self, assemblyIdentifier):
        # Administrator Manager
        return len(self.jwt_claims) and 'manager@%s' % assemblyIdentifier in self.jwt_claims.get("roles")
        # effective_principals

    def get_auth_roles(self, context):
        """ Get the acl roles of the curent user for the transmitted object"""

        # TODO: make sure it is only ran once... => move to object? so we can use as property...
        # @cache.CachedAttribute
        # @reify
        
        # update request shortcuts
        _roles = []
        if self.has_permission('delegate', context):
            _roles.append('delegate')
        if self.has_permission('add', context):
            _roles.append('add')
        if self.has_permission('append', context):
            _roles.append('append')
        if self.has_permission('propose_modify', context):
            _roles.append('propose_modify')
        if self.has_permission('propose_add', context):
            _roles.append('propose_add')
        if self.has_permission('rating', context):
            _roles.append('rating')
        if self.has_permission('saliencing', context):
            _roles.append('saliencing')
        if self.has_permission('modify', context):
            _roles.append('modify')
        if self.has_permission('observe', context):
            _roles.append('observe')
        if self.has_permission('administrate', context):
            _roles.append('administrate')
        if self.has_permission('manage', context):
            _roles.append('manage')

        # context.__roles__ = _roles
        return(_roles)

    def has_observe_permission(self, context):
        # Everybody with read permissions....

        # assert context.__roles__ is not None
        # return "observe" in context.__roles__
        return self.has_permission('observe', context)

    def has_public_permission(self, context):
        # Everybody with read permissions....
        return self.has_permission('public', context)

    @cache.CachedAttribute
    def get_user_specific_random_seed(self):
        """ The random seed is used for randomly order the branches of contenttrees.

        Requirements:
        - a random seed should be termporarily constant for each user. A refresh should not change
        the order of the content
        - the random seed should be differnt for each user.

        In case of registered user the random seed is derived by user.id.
        This is of course not possible for non-authenticated user.
        For them, the Client IP-address is used as random seed, which comes close to fullfill these
        requirements.
        """

        # convert IP to number
        if self.local_userid:
            seed = self.local_userid * 4242
        else:
            seed = int(ipaddress.IPv4Address(self.client_addr))
        return(seed)
