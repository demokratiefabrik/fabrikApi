from fabrikApi.models.contenttree.content import DBContent
import logging
from pyramid.decorator import reify
from pyramid.security import ALL_PERMISSIONS, Deny, Everyone
from sqlalchemy import Column, ForeignKey, Integer, Unicode
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship
from sqlalchemy_utils.types.arrow import ArrowType

from fabrikApi.util.authorization import getDefaultObjectACLs
from fabrikApi.models.meta import Base
from fabrikApi.models.mixins import BaseDefaultObject, arrow
from fabrikApi.models.lib.plugin_interfaces import ContentTreePluginInterface


logger = logging.getLogger(__name__)

__all__ = ['DBContentTree',]

class DBContentTree(BaseDefaultObject, ContentTreePluginInterface, Base):

    # Object authorization
    __roles__ = None
    __parent__ = None
    __name__ = None

    # SqlALchemy Table definition
    __tablename__ = "contenttree"

    # JSON Output
    _rootElementIds = None

    # CUSTOM_DATA = {}
    # CONTENTTYPES = []
    # DEFAULT_CONTENT_TYPE = None

    # primary
    id = Column(Integer, primary_key=True)

    # relationships (using backref only for linking from plugins to modules in main package)
    # logs = relationship("DBLog", backref="contenttree")
    # contenttree_progressions = relationship("DBContentTreeProgression", back_populates="contenttree")
    contents = relationship("DBContent", back_populates="contenttree")
    content_peerreviews = relationship("DBContentPeerReview", back_populates="contenttree")

    # SOME CONTENT CHILDREN ARE IN RANDOM ORDER AND SOME ARE IN FIXED ORDER
    # this ordering_list allows to automatically order fixed order content.
    db_ordered_children = relationship(
        "DBContent",
        primaryjoin="and_(DBContentTree.id==DBContent.contenttree_id, DBContent.parent_id == None, DBContent._is_in_random_order == False)",
        order_by="DBContent.order_position",
        collection_class=ordering_list('order_position', count_from=1))

    # In which assembly is this contenttree part of?
    assembly_id = Column(Integer, ForeignKey("assembly.id"), nullable=False)
    assembly = relationship("DBAssembly", back_populates="contenttrees")

    stages = relationship("DBStage", back_populates="contenttree")

    # Generic Foreign Key: Refers to the primary key of a discriminator_type.table. This could refer to any table.
    # inheriting from the "HasAttachedContentTreeMixin" class.
    # The discriminater_type refers to the type of discriminator_type table object: can be "assembly".
    # https://docs.sqlalchemy.org/en/13/_modules/examples/generic_associations/generic_fk.html
    # discriminator_id = Column(Integer)
    # discriminator_type = Column(String(200))

    # content attributes

    # date_last_tree_modification = Column(TIMESTAMP, default=datetime.utcnow)
    # date_last_tree_modification = Column(ArrowType, default=arrow.utcnow)
    title = Column(Unicode(100))

    def __init__(self, assembly, type_, title=""):
        """ Initialize a Content-ContentTree Instance"""

        assert type_ in plugins.ContentTreeTypes, "invalid type"

        self.title = title
        self.assembly_id = assembly
        self.type_ = type_
    
        assembly.contenttrees.append(self)

    """ Custom authorization ACLS for contenttree objects..."""
    @reify
    def __acl__(self):
        """ IMPORTANT! use "Allow" only on root object ALSs. (NEVEVER EVERY here, or any other child.)
        # The question to ask: Is there any object-related reason, why the actual request should be denied!
        # By default: this is only the case for Disabled / Deleted / inactive objects
        """
        
        # acl = self.assembly.__acl__()
        acl = []

        # assembly = find_root(self)
        acl.extend(getDefaultObjectACLs(self))

        # TODO: "append" permission? 
        # - rigth to append anywhere in the tree?
        # - right to append on the root level?

        return(acl)

    def setup_lineage(self, request):
        if self.__roles__ is not None:
            return None

        # already setup
        self.__name__ = 'contenttree'
        self.__parent__ = self.assembly
        self.__local_userid__ = request.local_userid
        self.__assembly_identifier__ = self.assembly.identifier
        self.patch()
        # self.__parent__.patch()
        self.__parent__.setup_lineage(request)
        self.__roles__ = request.get_auth_roles(self)

    def __str__(self):
        # For debugging (nice instance prints)
        return "DBContentTreessembly: %s - %s" % (self.id, self.title)

    def __json__(self, request):

        assert self.patched, "contenttree should be patched here."
        
        response = self.get_response_json(request)
        response.update({
            'title': self.title,
            'type': self.type_,
            # 'acl': request.get_auth_roles(context=self),
            # 'date_last_tree_modification': self.date_last_tree_modification,
            # 'append_permission': self.has_append_permission(request),
            # 'allowed_content_types_to_add': self.allowed_content_types_to_add(self, request)
        })

        # DELETED: only admins see deleted stages
        if self.deleted:
            response["deleted"] = self.deleted
            assert request.has_administrate_permission, "no administrate persmission."
        # DISABLED: only managers and admins see disabled stages
        if self.disabled:
            response["deleted"] = self.disabled
            assert request.has_administrate_permission or request.assembly.is_manager, "administrate or manage permission."

        # if self.CUSTOM_DATA:
        #     for key, value in self.CUSTOM_DATA.items():
        #         response.update({key: value(self, request)})

        return(response)

    @property
    def rootElementIds(self):
        """ This is the place where we temporarily store the hierarchical structure path,
        just before the object is converted to the XHR-HTTP-Response.
        """
        if self._rootElementIds:
            return self._rootElementIds

        return []

    def allowed_content_types_to_add(self, request, parent_type=None):
        """
        this methods returns a list of all children types, that can be inserted by the given user.
        - check ACLs, which user roles are able to append which content.
        """

        assert self.patched, "The contenttree object has not been patched."

        # Which types are theoretically possible to add for this user..?
        allowed_types = self.CONTENTTYPES

        def append_permission_by_content_type(type_):
            temp_content = DBContent(text='TEMP', title='TEMP', type_=type_, contenttree_id=self.id, user_id=request.local_userid)
            temp_content.contenttree = self
            temp_content.setup_lineage(request)
            response = 'add' in temp_content.__roles__
            del temp_content
            return response
        
        request.dbsession.begin_nested()  # establish a savepoint (to simulate modifications)
        types_ = list(filter(lambda type_: append_permission_by_content_type(type_), allowed_types))
        request.dbsession.rollback()  # rolls back simulation

        # request.dbsession.remove(temp_content)
        return types_
