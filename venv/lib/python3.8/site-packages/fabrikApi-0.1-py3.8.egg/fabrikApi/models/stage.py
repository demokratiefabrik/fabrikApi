from pyramid.security import ALL_PERMISSIONS
from fabrikApi.util.authorization import getDefaultObjectACLs
import logging

import arrow
from pyramid.decorator import reify
from sqlalchemy import JSON, Column, ForeignKey, Index, Integer, Unicode, UnicodeText, Boolean, Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ArrowType

from fabrikApi.models.lib.core import get_or_create_progression
from fabrikApi.models.meta import Base
from fabrikApi.models.mixins import BaseDefaultObject, BaseProgressionObject
from fabrikApi.models.lib.plugin_interfaces import PLUGIN_MODULES, StagePluginInterface
from fabrikApi.util.events import EventFirstStageVisit

logger = logging.getLogger(__name__)

__all__ = ['DBStage', 'DBStageProgression']


# def get_stage_progression_of_current_user(request, auto_create=True):
#     """ Loads stage-specific user-data.
#     Method requires an authenticated user and loaded request.stage.
#     """
#     assert request.local_userid, "invalid user"
#     assert request.stage, "invalid stage"

#     # Get AssemblyProgression
#     stage_progression = get_or_create_progression(
#         request,
#         DBStageProgression,
#         auto_create=auto_create,
#         event_when_creating_entry=EventFirstStageVisit,
#         user_id=request.local_userid,
#         stage=request.stage)

#     return(stage_progression)


class DBStage(BaseDefaultObject, StagePluginInterface, Base):

    # table definition
    __tablename__ = "stage"

    # CUSTOM_DATA = {}
    # CONTENTTYPES = []
    # DEFAULT_CONTENT_TYPE = None

    # primary
    id = Column(Integer, primary_key=True)

    # relationships (using backref only for linking from plugins to modules in main package)
    stage_progressions = relationship("DBStageProgression", back_populates="stage")

    # In which assembly is this stage part of?
    assembly_id = Column(Integer, ForeignKey("assembly.id"), nullable=False)
    assembly = relationship("DBAssembly", back_populates="stages")
    # assembly = relationship("DBAssembly", back_populates="contenttrees")

    # Which content-contenttree is attached to this stage.
    contenttree_id = Column(Integer, ForeignKey("contenttree.id"), nullable=True)
    contenttree = relationship("DBContentTree", back_populates="stages")

    order_position = Column(Integer, nullable=False)

    title = Column(Unicode(100))
    group = Column(Unicode(100))
    info = Column(UnicodeText())
    icon = Column(Unicode(100))
    custom_data = Column(JSON, nullable=True)

    def __init__(self, assembly, type_, title="", info="", icon=None, contenttree=None, custom_data=None):

        assert type_ in PLUGIN_MODULES['STAGE'], "invalid stage type"

        self.title = title
        self.info = info
        self.icon = icon
        self.assembly_id = assembly
        self.type_ = type_
        self.custom_data = custom_data

        # TOOD: is this needed?
        assembly.stages.append(self)
        if contenttree:
            contenttree.stages.append(self)


    """ Custom authorization ACLS for stage objects..."""
    @reify
    def __acl__(self):
        
        # acl = self.assembly.__acl__()
        acl = []

        # IMPORTANT! use "Allow" only on root object ALSs. (NEVEVER EVERY here, or any other child.)
        # The question to ask: Is there any object-related reason, why the actual request should be denied!
        # By default: this is only the case for Disabled / Deleted / inactive objects

        # assembly = find_root(self)
        acl.extend(getDefaultObjectACLs(self))

        # if self.deleted:
        #     acl.extend([
        #         (Deny, Everyone, ALL_PERMISSIONS)
        #     ])

        # if self.disable:
        #     acl.extend([
        #         (Deny, 'contributor@' + self.__assembly_identifier__, ALL_PERMISSIONS),
        #         (Deny, 'delegate@' + self.__assembly_identifier__, ALL_PERMISSIONS),
        #         (Deny, 'expert@' + self.__assembly_identifier__, ALL_PERMISSIONS),
        #         (Deny, 'public', ALL_PERMISSIONS)
        #     ])
        return(acl)

    def setup_lineage(self, request):
        self.__name__ = 'stage'
        self.__parent__ = self.assembly
        self.__local_userid__ = request.local_userid
        self.__assembly_identifier__ = self.assembly.identifier
        self.patch()
        # self.__parent__.patch()
        self.__parent__.setup_lineage(request)
        self.__roles__ = request.get_auth_roles(self)

    def __str__(self):
        # For debugging (nice instance prints)
        return "DBAssembly: %s - %s" % (self.id, self.title)

    def __json__(self, request):

        # if not self.patched:
        #     self.patch()
        assert self.patched, "stage is not yet patched..."

        response = self.get_response_json(request)
        response.update({
            'title': self.title,
            'info': self.info,
            'icon': self.icon,
            'type': self.type_,
            'group': self.group,
            'contenttree_id': self.contenttree_id,
            'order_position': self.order_position,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'acl': request.get_auth_roles(context=self),
            'custom_data': self.custom_data
        })

        # DELETED: only admins see deleted stages
        if request.has_administrate_permission:
            response["deleted"] = self.deleted
            assert request.has_administrate_permission, "no administrate permission"
        # DISABLED: only managers and admins see disabled stages
        if request.has_administrate_permission or self.assembly.is_manager:
            response["disabled"] = self.disabled
        
        if self.CUSTOM_DATA:
            for key, value in self.CUSTOM_DATA.items():
                response.update({key: value(self, request)})

        return(response)


class DBStageProgression(BaseProgressionObject, Base):
    """
    FOR USERS:
    ALL OF THEM GET AN ENTRY AS SOON AS THEY ATTEND THE stage THE FIRST TIME.
    """

    __tablename__ = 'stage_progression'
    __table_args__ = (
        # Ensure unique progression for each user:
        Index("uq_stageprogression_stageid_userid", "stage_id", "user_id", unique=True),
    )

    # primary
    id = Column(Integer, primary_key=True)

    skipped = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    alerted = Column(Boolean, default=False)
    date_created = Column(ArrowType, default=arrow.utcnow)
    date_completed = Column(ArrowType)
    focused_content_id = Column(Integer)  # used to give a focus to a certain topic/content

    # The following attributes are reseted once a day:
    date_last_day_session = Column(ArrowType)
    number_of_day_sessions = Column(Integer, default=0)

    # relationships
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship("DBUser", backref="stage_progressions")
    stage_id = Column(Integer, ForeignKey('stage.id'))
    stage = relationship("DBStage", back_populates="stage_progressions")

    def __init__(self, stage=None, stage_id=None, user_id=None):
        assert user_id, "empty user_id"
        assert stage or stage_id, "empty stage /stage_id"

        self.user_id = user_id

        if stage_id:
            self.stage_id = stage_id
        else:
            self.stage = stage

    def __str__(self):
        # For debugging (nice instance prints)
        return "stage Progression: %s: %s" % (
            self.id, self.stage) 

    def __json__(self, request):

        response = self.get_response_json(request)
        response.update({
            'completed': self.completed,
            'skipped': self.skipped,
            # 'locked': self.locked,
            'focused_content_id': self.focused_content_id,
            'alerted': self.alerted,
            'number_of_day_sessions': self.number_of_day_sessions
        })
        return(response)
    # last accesssed is not really used and generates a lot of db writings..
    # scan log files if needed.
    # date_modified = Column(ArrowType, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    def setUnalert(self):
        """ when a user leaves this assembly """
        self.alerted = False

    def setFocusedContent(self, content):
        """ when a user sets a new focused content for this stage. Note: this is not reversibe..."""
        assert content and content.id, "empty content / content_id"
        if self.focused_content_id == content.id:
            # Already set. 
            # For instance, when double clicking on some some buttons
            return False

        assert not self.focused_content_id, " focused_content_id should be empty, here..."
        self.focused_content_id = content.id

    def complete(self):
        """ when a user leaves this assembly """
        self.completed = True
        self.alerted = False
        self.date_completed = arrow.now()

    def alert(self):
        """ very important task => alerting user for this stage """
        self.alerted = True

    def skip(self):
        """ very important task => alerting user for this stage """
        self.skipped = True

    # def lock(self):
    #     """ troll-handling """
    #     self.locked = True
    #     self.date_locked = arrow.utcnow()


    @property
    def is_active(self):
        return not self.completed
        # self.locked and 