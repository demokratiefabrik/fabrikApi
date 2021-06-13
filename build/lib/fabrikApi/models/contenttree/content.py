import datetime
import logging
import random
import arrow
from pyramid.security import Allow, Deny, Everyone
from fabrikApi.util import cache

from sqlalchemy import Boolean, Column, ForeignKey, Integer, UnicodeText
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql.schema import Index
from sqlalchemy.sql.sqltypes import Float

from fabrikApi.util.authorization import getDefaultObjectACLs
from fabrikApi.models.lib.core import get_or_create_progression
from fabrikApi.models.lib.plugin_interfaces import ContentPluginInterface
from fabrikApi.models.meta import Base
from fabrikApi.models.mixins import BaseDefaultObject, BaseProgressionObject

from .mixins import EditableEntityMixin, RateableEntityMixin, ReadableEntityMixin

from sqlalchemy_continuum import make_versioned

__all__ = ['DBContent', 'DBContentProgression',
           'get_content_progression_of_current_user',
           'reorder_branches',
           ]

logger = logging.getLogger(__name__)

make_versioned(user_cls=None)

def get_content_progression_of_current_user(request, auto_create=True, content=None):
    """ Loads content-specific user-data.
    Method requires an authenticated user and loaded request.assembly. 
    """
    if not content:
        content = request.content

    assert request.local_userid, "localuser_id must not be empty"
    #  or not request.content

    # Get AssemblyProgression
    content_progression = get_or_create_progression(
        request,
        DBContentProgression,
        auto_create=auto_create,
        user_id=request.local_userid,
        content_id=content.id)

    # never ever retrieve a content of somebody else...
    assert content_progression.user_id == request.local_userid, "invlaid user_id"
    return(content_progression)


def reorder_branches(content, contenttree):
    """
    After content modification/insert/delete the branch must be reordered.
    And this only if order of child-content is fixed (and not random)
    """

    if content.is_in_random_order:
        # Reorder is not necessary for random branches
        return (None)

    if content.db_parent:
        content.db_parent.db_ordered_children.reorder()
    else:
        contenttree.db_ordered_children.reorder()





class DBContent(BaseDefaultObject, ContentPluginInterface, Base):
    """
    Contents-Objects, hirarchical structured (main ingredients of ContentTrees).
    """

    # POLICY LENGTH: MUST BE LOWER THAN THE TECHNICAL DB-LENGHT, DUE TO MERGEING FUNCTIONALITY
    MAX_TEXT_LENGTH = 1000

    # SQLAlchemy Table Definition
    __versioned__ = {}
    __tablename__ = "content"
    __table_args__ = (
        # FOR TREE MANAGER
        Index("ix_contenttreeid_deleted_disabled_parentid_orderposition",
              "contenttree_id", "deleted", "disabled", "parent_id", "order_position"),
        # TODO: is this still used?
        Index("ix_contenttreeid_deleted_disabled_modifieddate", "contenttree_id", "deleted",
              "disabled", "date_modified")
    )

    # Pyramid Object authorization
    __roles__ = None
    __parent__ = None
    __name__ = None

    # JSON Output
    # prepare temporary storage
    _structure = None
    # _branch = None
    _path = None
    # _children = None

    # Primary key
    id = Column(Integer, primary_key=True)

    # Relationships (using backref for linking from plugins to modules in main package)
    contenttree_id = Column(Integer, ForeignKey('contenttree.id'))
    contenttree = relationship("DBContentTree", back_populates="contents")
    parent_id = Column(Integer, ForeignKey('content.id', ondelete='CASCADE'))
    db_parent = relationship(
        'DBContent', remote_side=[id], backref=backref('db_children'), uselist=False)
    db_ordered_children = relationship(
        "DBContent",
        primaryjoin="and_(DBContent.id==remote(DBContent.parent_id), remote(DBContent._is_in_random_order) == False)",
        order_by="DBContent.order_position",
        collection_class=ordering_list('order_position', count_from=1))
    content_progressions = relationship("DBContentProgression", back_populates="content")
    # logs = relationship("DBLog", backref="content")
    # content_peerreviews = relationship("DBContentPeerReview", back_populates="content", foreign_keys='DBContentPeerReview.content_id')
    # content_peerreview_discussions = relationship("DBContentPeerReview", back_populates="discussion_content", foreign_keys='DBContentPeerReview.discussion_content_id')
    # contents = relationship("DBContent", back_populates="contenttree")

    # content_peerreview_discussions = relationship("DBContentPeerReview", back_populates="discussion_content")
    
    # last_peerreview_id = Column(Integer, ForeignKey('content_peerreview.id', ondelete='CASCADE'))
    # last_peerreview = relationship("DBContentPeerReview", back_populates="contents")

    # content
    title = Column(UnicodeText(200), nullable=False)

    # order position: e.g. for TEXTSHEET Text Content
    order_position = Column(Integer, nullable=True)
    _is_in_random_order = Column("is_in_random_order", Boolean, default=True)

    # type_ = Column('type', ChoiceType(plugins.ContentTypes), nullable=False)
    # type_ = Column("type", String(50), nullable=False)

    text = Column(UnicodeText(3000), default=u"")
    # to lock contents (non-editable)
    # locked = Column(Boolean, default=False)
    pending_peerreview_for_update = Column(Boolean, default=False)
    pending_peerreview_for_insert = Column(Boolean, default=False)
    rejected_peerreview_for_insert = Column(Boolean, default=None)
    completed_peerreview_for_insert = Column(Boolean, default=None)

    # by manager...#TODO rename
    reviewed = Column(Boolean, default=False)

    # How deletion took place: 1) Direct-Delete, 2) Inherited-Delete,  3) Merged  4) Splitted
    deleted_detail = Column(Integer, default=0)
    # overwrites random order of content children (see. content_progression)
    custom_order = Column(Integer)

    # Aggregates: Rating (mean and count)
    agg_progression_count = Column(Integer)
    agg_rating_avg = Column(Float)
    agg_rating_count = Column(Integer)
    agg_salience_avg = Column(Float)
    agg_salience_count = Column(Integer)

    def __init__(self, text, title, type_, contenttree_id, user_id, parent_id=None, locked=False):

        # TODO validate type etc...
        # assert type_ in self.ARGUMENT_TYPES, "invalid content type"
        assert len(title) > 0, "invalid title.."

        self.text = text
        self.title = title
        self.type_ = type_
        self.contenttree_id = contenttree_id
        self.user_created_id = user_id
        # Fixed order for some branches is not implemented yet.
        # self.order = order
        # self.locked = locked
        self.parent_id = parent_id

        # add content-type specific intelligence
        self.patch()

        # Next steps: 
        # To  prevent circular parent-children relationships use "validate_parent_and_type_data"
        # To proper check acls, first call "setup_lineage"


    """ Custom authorization ACLS for contenttree objects..."""
    @cache.CachedAttribute
    def __acl__(self):
        
        # acl = self.assembly.__acl__()
        assert self.patched, "Cannot estimate acls for unpatched content."
        acl = []

        # IMPORTANT! use "Allow" only on root object ACLs. (NEVEVER EVERY here, or any other child.)
        # The question to ask: Is there any object-related reason, why the actual request should be denied!
        # By default: this is only the case for Disabled / Deleted / inactive objects
        # assembly = find_root(self)
        acl.extend(getDefaultObjectACLs(self))

        # SPECIAL CASE PERMISSIONS
        ownership = self.user_created_id == self.__local_userid__ and  self.is_private_property_content

        # GLOBAL PERMISSIONS
        if ownership:
            # property cannot be salienced and rated when its the own property
            acl.extend([
                (Deny, Everyone, ['saliencing', 'rating']),
            ])

        if self.is_given_property_content or self.is_common_property_content:
            # MANAGER EXCLUSIVENESS
            # non-managers cannot add or modify content that is not private
            acl.extend([
                (Deny, 'contributor@' + self.__assembly_identifier__, ['add', 'modify']),
                (Deny, 'delegate@' + self.__assembly_identifier__, ['add', 'modify']),
                (Deny, 'expert@' + self.__assembly_identifier__, ['add', 'modify'])
            ])
            
            # # TODO: THIS SHOULD BE A PLUGIN LEVEL SETTING: Can rate only private content, right?
            # acl.extend([
            #     (Deny, Everyone, ['rating']),
            # ])

        # OWNERSHIP
        if not ownership:
            # cannot modify other peoples private property.
            acl.extend([
                (Deny, 'contributor@' + self.__assembly_identifier__, ['modify']),
                (Deny, 'delegate@' + self.__assembly_identifier__, ['modify']),
                (Deny, 'expert@' + self.__assembly_identifier__, ['modify'])
            ])

        # PROPOSE PERMISSION
        # nur Peer Review Proposals are only possible with common goods. 
        if not self.is_common_property_content:
            acl.extend([
                (Deny, 'contributor@' + self.__assembly_identifier__, ['propose_add', 'propose_modify']),
                (Deny, 'delegate@' + self.__assembly_identifier__, ['propose_add', 'propose_modify']),
                (Deny, 'expert@' + self.__assembly_identifier__, ['propose_add', 'propose_modify'])
            ])

        # TODO: Who is allowed to add append a contribution?
        # Everybody, except: day limit / level limit / no addable content type at this position, etc.....

        # EXTEND ACLs by Content Plugins
        self.acl_extension_by_content_plugins(acl)

        return(acl)

    def setup_lineage(self, request):
        if self.__roles__ is not None:
            return None

        # already setup
        self.__name__ = 'content'
        self.__parent__ = self.contenttree
        self.__local_userid__ = request.local_userid
        self.__assembly_identifier__ = self.contenttree.assembly.identifier
        self.patch()
        # self.__parent__.patch()
        self.__parent__.setup_lineage(request)
        self.__roles__ = request.get_auth_roles(self)

    def validate_parent_and_type_data(self):
        """ Validate parent: Is it a valid type of the (new) parent object? """
        
        assert self.contenttree.patched, "contenttree is not yet patched..."
        
        # VALID PARENT
        parent_type = None
        if self.parent_id:
            self.db_parent.patch()
            parent_type = self.db_parent.type_
        allowed_types = self.contenttree.ONTOLOGY[parent_type]
        assert self.type_ in allowed_types, "invalid type"

        # NO CIRUCLAR HIERARCHIES
        # create path array list
        self._path = [self.id, ]
        antecedent = self.db_parent
        while antecedent:
            assert antecedent.id is not self.id, "Circular Hierarchies!"
            self._path.insert(0, antecedent.id)
            antecedent = antecedent.db_parent

        # SAME CONTENTTREE
        if self.db_parent:
            self.db_parent.contenttree_id == self.contenttree_id

        return True

    
    @property
    def path(self):
        """ This is the place where we temporarily store the hierarchical structure path,
        just before the object is converted to the XHR-HTTP-Response.
        """
        if self._path:
            return self._path

        if self._structure:
            # TODO: is this used?
            return self._structure['path']

    @property
    def statistics(self):
        return ({
            'PC': self.agg_progression_count,
            'RA': self.agg_rating_avg,
            'RC': self.agg_rating_count,
            'SA': self.agg_salience_avg,
            'SC': self.agg_salience_count
        })

    def __json__(self, request):

        self.patch()

        if not request.contenttree or request.contenttree.id is not self.contenttree_id:
            # load it from DB (for instance, used for monitors)
            request.contenttree = self.contenttree
            assert request.contenttree.patched, "contenttree should be patched here"

        response = self.get_response_json(request)

        # PUBLIC META VALUES
        response.update({
            'parent_id': self.parent_id,
            'contenttree_id': self.contenttree_id,
            'type': self.type_,
            'order_position': self.get_order_position(request),
            'common_property': self.is_common_property_content,
            'given_property': self.is_given_property_content,
            'private_property': self.is_private_property_content,
            'disabled': self.disabled or self.deleted,
            'acl': request.get_auth_roles(context=self)
        })

        if self.is_common_property_content:
            response.update({
                'pending_peerreview_for_update': self.pending_peerreview_for_update,
                'pending_peerreview_for_insert': self.pending_peerreview_for_insert,
                'rejected': self.rejected_peerreview_for_insert,
                'peerreviewed': self.completed_peerreview_for_insert
            })

        if not self.is_private_property_content:
            response.update({
                'S': {
                        'PC': self.agg_progression_count,
                        'RA': self.agg_rating_avg,
                        'RC': self.agg_rating_count,
                        'SA': self.agg_salience_avg,
                        'SC': self.agg_salience_count
                    }
                })

        # ONLY VISIBLE WHEN NOT DISABED/DELETED
        if (self.disabled or self.deleted) and not request.has_administrate_permission and not self.contenttree.assembly.is_manager:
            response.update({
                'title': 'Gelöschter Inhalt',
                'text': '....',
            })
        else:
            response.update({
                'title': self.title,
                'text': self.text,
            })

        if request.has_administrate_permission or self.contenttree.assembly.is_manager:
            response["reviewed"] = self.reviewed
        if request.has_administrate_permission:
            response["deleted"] = self.deleted

        if self.CUSTOM_DATA:
            for key, value in self.CUSTOM_DATA.items():
                response.update({key: value(self, request)})

        return response

    def get_order_position(self, request):
        if self.is_in_random_order:

            # generate random order int
            base_random_seed = request.get_user_specific_random_seed + self.contenttree_id
            random.seed(base_random_seed * self.id)

            # Allow fixed content ordering  before and after random range... 
            return random.randint(20, 80)

        else:

            return self.order_position

    def set_reviewed(self):
        """
        Update "reviewed" flag by a manger (contribution has been authorized)
        """

        assert self.contenttree.assembly.is_manager, "only for managers..."

        if self.reviewed:
            return False

        # logger.debug("set discussed %s" % self)
        self.reviewed = True

        return (True)


class DBContentProgression(BaseProgressionObject, Base, ReadableEntityMixin, RateableEntityMixin,
                            EditableEntityMixin):
    """ store all user-specified data e.g. reception of contents
    (ratings, salience indications, read, view, etc.)
    """

    # table definition
    __tablename__ = "content_progression"
    __table_args__ = (
        # # SEARCH CONTENT
        # Index('default_search', "contenttree_id", "title", "text"),

        # Ensure unique progression for each user:
        Index("uq_contentprogression_contentid_userid_unique", "content_id", "user_id", unique=True),
        # Index("ix_contentprogression_contentid_userid_modifieddate", "content_id", "user_id", "date_modified"),
    )

    # primary key
    id = Column(Integer, primary_key=True)

    # relationships
    content_id = Column(Integer, ForeignKey('content.id'), nullable=False)
    content = relationship("DBContent", back_populates="content_progressions")
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship("DBUser", backref="content_progressions")
    discussed = Column(Boolean, default=False)

    def __init__(self, user_id, content_id=None, content=None):
        assert content_id or content, "invalid content"
        if not content_id:
            content_id = content.id
            
        self.user_id = user_id
        self.content_id = content_id
        # self.random_seed = random.randint(0, 9)

    def __repr__(self):
        return "Proarg - Arg: %s Usr: %s Rating: %s Salience: %s" % (
            self.content_id, self.user_id, self.rating, self.salience)

    def __json__(self, request):

        # NEVER EVER EXPORT progressions of other users...
        assert request.local_userid == self.user_id, "invalid user data"

        return {
            # 'order_position': self.get_order_position(request),
            'read': self.read,
            'discussed': self.discussed,
            'alerted': self.alerted,
            'salience': self.salience,
            # 'salienced': self.salienced,
            'last_interaction': self.date_last_interaction,
            'rating': self.rating
            # 'rated': self.is_rated
        }

    def set_discussed(self):
        """
        Update discussed status of progression_content
        """

        # set last discuss date. 
        ago15minutes = arrow.utcnow() - datetime.timedelta(minutes=10)
        if not self.date_last_interaction or self.date_last_interaction < ago15minutes:
            self.date_last_interaction = arrow.utcnow()

        if self.discussed:
            return False

        # logger.debug("set discussed %s" % self)
        self.discussed = True

        return (True)
