# -*- coding: utf-8 -*-

from pyramid.decorator import reify
from pyramid.httpexceptions import exception_response
from sqlalchemy.sql.sqltypes import JSON
from fabrikApi.models.lib.plugin_interfaces import AssemblyPluginInterface
import logging
from sqlalchemy_utils import ArrowType

from pyramid.security import Allow, DENY_ALL, Everyone
from sqlalchemy import Column, ForeignKey, Index, Integer, Unicode, UnicodeText, UniqueConstraint, \
    and_
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship
from sqlalchemy.types import Boolean

from fabrikApi.util import cache
from fabrikApi.models import DBUser
from fabrikApi.models.lib.core import get_or_create_progression
from fabrikApi.models.meta import Base
from fabrikApi.models.mixins import BaseDefaultObject, BaseProgressionObject
from fabrikApi.models.stage import DBStageProgression
from fabrikApi.util.events import EventAssemblyVisit, EventFirstAssemblyVisit, EventStageVisit

__all__ = ['DBAssembly', 'DBAssemblyProgression', 'get_assembly_by_identifier',
           'get_assembly_progression_of_current_user', 'extend_stages_with_progression_entries']

logger = logging.getLogger(__name__)


def get_assembly_by_identifier(request, assembly_identifier):
    """ Return assembly object by assembly_identifier """
    assert assembly_identifier, "empty identifier"

    assembly = request.dbsession.query(DBAssembly)\
        .filter(DBAssembly.identifier == assembly_identifier).one()
    return(assembly)


def get_assembly_progression_of_current_user(request, auto_create=True, events=True):
    """ Loads assembly-specific user-data.
    Method requires an authenticated user and loaded request.assembly.
    """
    assert request.local_userid, "empty user"
    assert request.assembly, "empty assembly"

    # Get AssemblyProgression
    assembly_progression = get_or_create_progression(
        request,
        DBAssemblyProgression,
        auto_create=auto_create,
        event_when_creating_entry=EventFirstAssemblyVisit if events else None,
        event_when_reusing_entry=EventAssemblyVisit if events else None,
        user_id=request.local_userid,
        assembly=request.assembly)

    return(assembly_progression)


def extend_stages_with_progression_entries(stages, request, auto_create=False):
    """
    not existing progression entries are created
    returns list of dictionary: {'stage': DBStage, 'progression': DBStageProgression}
    """

    # Retrieve list of all existing progression instances...
    stage_ids = list(map(lambda stage: stage.id, stages))
    # TODO: index on user_id and stage-id for stage progressions?
    stage_progressions = request.dbsession.query(
        DBStageProgression).filter(and_(
            DBStageProgression.stage_id.in_(stage_ids),
            DBStageProgression.user_id == request.local_userid)).all()
    stage_progressions = {v.stage_id: v for v in stage_progressions}

    # Match stages and progression instances (if available)
    # If not available: create a new progression instance.
    stage_dicts = {}
    for stage in stages:
        stage.patch()
        # stage.setup_lineage(request)
        stage_dict = {'stage': stage, 'progression': None}
        if stage.id in stage_progressions:
            progression = stage_progressions[stage.id]
            stage_dict['progression'] = progression
            event = EventStageVisit(request=request, progression=progression, stage=stage)
            request.registry.notify(event)

        stage_dicts[stage.id] = stage_dict
    return (stage_dicts)


class DBAssembly(BaseDefaultObject, AssemblyPluginInterface, Base):
    """
    Citizen Assemblies Table.
    """
    # Object authorization
    __roles__ = None
    __parent__ = None
    __name__ = None
    __progression__ = None

    # SQLAlchemy
    __tablename__ = "assembly"
    __table_args__ = (UniqueConstraint("identifier"),)

    SEARCHABLE_FIELDS = ['title', 'caption', 'identifier', 'info']
    DEFAULT_JSON_RESPONSE_FIELDS = ['id', 'identifier', 'title', 'caption']

    # primary key
    id = Column(Integer, primary_key=True)

    # relationships
    assembly_progressions = relationship("DBAssemblyProgression", back_populates="assembly")
    contenttrees = relationship("DBContentTree", back_populates="assembly")
    stages = relationship(
        "DBStage",
        order_by="DBStage.order_position",
        collection_class=ordering_list('order_position', count_from=1))

    # main attributes
    is_public = Column("is_public", Boolean, default=False)
    identifier = Column(Unicode(45), nullable=False)  # identifier used in URLS /koeniz2020/home
    title = Column(Unicode(100), nullable=False)  #Short title: e.g. Könizer Parlamentswahlen 2020
    caption = Column(Unicode(450))  # full sentence: what is that about
    # location = Column(Unicode(100))  # public
    image = Column(Unicode(100))  # public
    info = Column(UnicodeText())  # full description of the meaning of the assembly.
    text_background = Column(UnicodeText(), default=u"")


    def __init__(self, type_, title="", info="",
                 identifier="", caption="", image=None):

        self.title = title
        self.caption = caption
        self.info = info
        self.image = image
        self.identifier = identifier
        # self.location = location
        self.type_ = type_
        assert type_ in plugins.AssemblyTypes, "invalid assembly type"


    """ Note: keep in sync with fabrikClient/src/util/oauth/oauthstore/assembly_acls."""
    @reify
    def __acl__(self):

        # RELEVANT QUESTION: is there any case, a user with the corresponding role requires this privileges?
        assembly_identifier = self.identifier

        acl = []

        # ADMIN EXCEPTION can do everything (except specific user roles: add/delegate/expert)!
        # No need to handly administrator permissions is child objects.
        acl.extend([
            (Allow, 'administrator', [
                'administrate', 'manage', 'append', 'add',
                'modify', 'observe', 'public'])
        ])
        # TODO: why are progressions and contenttrees loaded here????
        # In case of deleted assembly: Deny anybody... (admin is an exception handled above)
        if self.deleted:
            acl.extend([DENY_ALL])

        # Manager EXCEPTION: they can do everything (again, except specific user roles: add/delegate/expert)!
        # No need to handly manager permissions in child objects.
        acl.extend([
            # Generally, Deny Managers only if assembly is deleted.
            (Allow,  'manager@' + assembly_identifier, [
                'manage', 'append', 'add', 'modify', 'observe', 'public'])
        ])

        # In case of disabled assembly ( or not yet active content)
        # Deny anybody... (admin/manager is an exception handled above)
        if not self.is_active:
            acl.extend([DENY_ALL])

        acl.extend([
            (Allow, 'delegate@' + assembly_identifier, [
                'delegate', 'append', 'modify', 'rating', 'saliencing', 'observe', 'public']),
            (Allow, 'contributor@' + assembly_identifier, [
                'modify', 'rating', 'saliencing', 'observe', 'public']),
            (Allow, 'expert@' + assembly_identifier, [
                'modify', 'observe', 'public']),
            (Allow, Everyone, ['public']),
        ])

        # Considering Contribution limits...
        # For contribution, assembly_progression must be loaded...
        if self.__progression__:
            if self.MAX_DAILY_USER_COMMENTS > self.__progression__.number_of_comments_today:
                acl.extend([
                    (Allow, 'delegate@' + assembly_identifier, ['add', 'append']),
                    (Allow, 'contributor@' + assembly_identifier,  ['add', 'append']),
                    (Allow, 'expert@' + assembly_identifier, ['add', 'append']),
                ])

            if self.MAX_DAILY_USER_PROPOSALS > self.__progression__.number_of_proposals_today:
                acl.extend([
                    (Allow, 'delegate@' + assembly_identifier, ['propose_add', 'propose_modify']),
                    (Allow, 'contributor@' + assembly_identifier,  ['propose_add', 'propose_modify']),
                ])

        return(acl)

    def setup_lineage(self, request):
        if self.__roles__ is not None:
            return None

        self.__name__ = ''  # leave empty, doc said. but why? (lineage root object),
        self.__parent__ = None
        self.__local_userid__ = request.local_userid
        self.__assembly_identifier__ = self.identifier
        # self.__progression__ = get_assembly_progression_of_current_user(request, auto_create=False, events=False)

        # Get AssemblyProgression
        request.assembly = self

        if not self.__progression__ and request.local_userid:

            self.__progression__ = get_or_create_progression(
                request,
                DBAssemblyProgression,
                auto_create=True,
                user_id=request.local_userid,
                assembly=self)

        self.patch()
        self.__roles__ = request.get_auth_roles(self)

    def __str__(self):
        # For debugging (nice instance prints)
        return "DBAssembly: %s - %s" % (self.id, self.title)


    @cache.CachedAttribute
    def is_manager(self):
        # Assembly Manager

        assert self.__roles__ is not None, "__roles__ are empty"
        return "manage" in self.__roles__

    def is_participant(self, request):
        # Everybody with read permission but not admin/managers

        assert self.__roles__ is not None, "__roles__ are empty"
        return (not self.is_manager and not request.has_administrate_permission)

    def label(self):
        """ public label (for participants)"""
        return self.title

    def __json__(self, request):

        # extend default ACLs with assembly-specific permissions.
        # Keep in sync with fabrikAuth Readme
        response = self.get_response_json(request)
        response.update({
            'title': self.title,
            'caption': self.caption,
            'info': self.info,
            'background': self.text_background,
            'type': self.type_,
            'identifier': self.identifier,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'is_active': self.is_active,
            'is_public': self.is_public,
            # 'status': self.status,
            # 'image': self.image,
            'acl': self.__roles__
            # 'acl': request.get_auth_roles(context=self),
            # Variables used only by Artificial Moderators
            # does the user plays a specific role within this assembly
            # 'accessible': len(roles) > 0
        })


        # DELETED: only admins see deleted stages
        if request.has_administrate_permission:
            response["deleted"] = self.deleted
            assert request.has_administrate_permission, "no administrate permission"
        # DISABLED: only managers and admins see disabled stages
        if request.has_administrate_permission or self.is_manager:
            response["disabled"] = self.disabled

        return(response)

    def get_stages_with_view_permission(self, request):
        # Add also assembly's stages
        stages = request.assembly.stages

        # add lineage for acl calculations...
        for stage in stages:
            # stage.patch()
            stage.setup_lineage(request)
       
        stages = list(filter(
            lambda stage: request.has_observe_permission(stage),
            stages))

        # extend progression (for none managers...)
        stages = extend_stages_with_progression_entries(stages, request)

        # remove completed assemblies

        if request.assembly.is_participant(request):
            stages = {
                key: value for (key, value) in stages.items() if not value['progression'] or value['progression'].is_active
            }

        return stages


class DBAssemblyProgression(BaseProgressionObject, Base):
    """
    FOR ALL USERS WHO ATTENDED THE ASSEMBLY
    ALL OF THEM GET AN ENTRY AS SOON AS THEY ATTEND THE assembly THE FIRST TIME.
    """

    __tablename__ = 'assembly_progression'
    __table_args__ = (
        # Ensure unique progression for each user:
        Index("uq_assemblyprogression_assemblyid_userid", "assembly_id", "user_id", unique=True),
    )

    # primary
    id = Column(Integer, primary_key=True)

    # relationships
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(DBUser, backref="assembly_progressions")
    assembly_id = Column(Integer, ForeignKey('assembly.id'), nullable=False)
    assembly = relationship("DBAssembly", back_populates="assembly_progressions")

    # data....
    date_last_day_session = Column(ArrowType)
    number_of_day_sessions = Column(Integer, default=0)
    number_of_proposals = Column(Integer, default=0)
    number_of_comments = Column(Integer, default=0)
    number_of_proposals_today = Column(Integer, default=0)
    number_of_comments_today = Column(Integer, default=0)

    todays_ips = Column(JSON)

    def __init__(self, assembly, user=None, user_id=None):
        assert assembly, "empty assembly"
        assert user or user_id, "empty user"
        user_id = user_id or user.id

        self.assembly = assembly
        self.user_id = user_id

    def __str__(self):
        # For debugging (nice instance prints)
        return "Assembly Progression: %s: %s" % (self.id, self.assembly)

    def __json__(self, request=None):
        response = self.get_response_json(request)
        response.update({
            # 'locked': self.locked,
            'alerted': self.alerted,
            'number_of_day_sessions': self.number_of_day_sessions,
            'number_of_comments_today': self.number_of_comments_today,
            'number_of_proposals_today': self.number_of_proposals_today
        })
        return(response)

    # Record Client IP
    def assert_distinct_ip_limit(self, request):
        remote_add_ip = request.client_addr
        recent_ips = self.todays_ips
        if not recent_ips:
            recent_ips = []
        if remote_add_ip not in recent_ips:
            recent_ips.append(remote_add_ip)
        # not more than x ips a day!!
        if len(recent_ips) > 5:
            raise exception_response(429)  #  raises an HTTPTooManyRequests exception.
