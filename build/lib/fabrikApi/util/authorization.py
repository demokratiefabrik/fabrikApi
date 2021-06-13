from get_docker_secret import get_docker_secret
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import ALL_PERMISSIONS, Allow, Authenticated, Deny, Everyone
from pyramid_jwt import set_jwt_authentication_policy
from pyramid_jwt.policy import PyramidJSONEncoderFactory

json_encoder_factory = PyramidJSONEncoderFactory(None)


class RootACL(object):
    """ Default group permissions:
    (System-)Administrator/(Event-)Manager/(Event-)Moderator/(Event-)Contributor/
    (Self-)Authenticated/Unauthenticated

    PS: These ACLs are ignored when an AssemblyService-Page is requested. (see AssemblyFactory)????????

    Hard-rules:
    - Some tasks are reserved for citizens and cannot be excerted by Managers or Administrators.
    - Any active contributions requires login.

    LIST OF AVAILABLE ROLES:
    .   administrator
    -   manager
    -   delegate
    -   contributor
    -   expert',
    -   authenticated'
    -   everyone'

    LIST OF AVAILABLE PERMISSIONS:
    -   administrate (App owner)
    -   manage (event manager)
    -   delegate (act as delegate => e.g. peer-reviewing)
    -   propose_modify (propose to modify ...)
    -   propose_add (propose to add ...)
    -   add (add own contribution)
    -   append (append child element)
    -   saliencing (add salience to contribution)
    -   rating (add rating to contribution)
    -   modify  (modify/delete contibution)
    -   observe (read assembly content)
    -   public (read public content)
    
    ...
    """

    __acl__ = [
        (Allow, 'administrator', ['administrate', 'manage', 'observe', 'public']),
        # (Allow, 'manager', ['manage', 'observe', 'public']),
        # (Allow, 'delegate', ['delegate', 'add', 'observe', 'public']),
        # (Allow, 'contributor', ['add', 'observe', 'public']),
        # (Allow, 'expert', ['add', 'observe', 'public']),
        (Allow, Authenticated, ['observe', 'public']),
        (Allow, Everyone, ['public', ])
    ]

    def __init__(self, request):
        pass


def convert_jwt_roles_to_principals(user_id, request):
    """
    Retrieve roles from JWT.
    Notice: all roles (except administrator) are attached to an assembly: 
    Format: <role>@<assembly_identifier>
    """

    return(['%s' % role for role in request.jwt_claims.get('roles', [])])


def getDefaultObjectACLs(context):

    # In case of deleted objects: Deny anybody... (except administrators)
    acls = []
    assert context.__assembly_identifier__, "empty assemblyIdentifier in this context..."
    if context.deleted:
        acls.extend([
            (Deny, 'manager@' + context.__assembly_identifier__, ALL_PERMISSIONS)
        ])

    # In case of deleted objects: Deny everybody else... (except administrators)
    # Note: "Not authenticated people" are handled in assembly_acls

    if context.deleted or not context.is_active:
        acls.extend([
            (Deny, 'contributor@' + context.__assembly_identifier__, ALL_PERMISSIONS),
            (Deny, 'delegate@' + context.__assembly_identifier__, ALL_PERMISSIONS),
            (Deny, 'expert@' + context.__assembly_identifier__, ALL_PERMISSIONS),
        ])

    return acls


def includeme(config):

    # JWT-Token authentication
    config.set_root_factory(RootACL)
    config.set_authorization_policy(ACLAuthorizationPolicy())
    
    # Disabled March, 2021. 
    # json_encoder_factory.registry = config.registry
    
    config.add_directive(
        "set_jwt_authentication_policy",
        set_jwt_authentication_policy,
        action_wrap=True)

    config.set_jwt_authentication_policy(
        get_docker_secret('oauth_secret_id', default=''),
        callback=convert_jwt_roles_to_principals,
        http_header='Authorization',
        auth_type='JWT',
        expiration=-1,  # expiration date is indicated within jwt!
        algorithm=get_docker_secret('oauth_algoritm', default=''),
        )
        # audience=get_docker_secret('oauth_audience', default='') # audience not required...
