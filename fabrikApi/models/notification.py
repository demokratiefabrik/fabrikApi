## -*- coding: utf-8 -*-
# flake8: noqa

"""
Tracks all User acitivities. The main purpose of this is scientifically. 
It enables easy evaluation of what has happened on the platform.

"""

import logging
from sqlalchemy.sql.schema import Index
from sqlalchemy.sql.sqltypes import JSON
from sqlalchemy_utils import ArrowType
import arrow

from sqlalchemy import Boolean, Column, Integer, String

from fabrikApi.models.meta import Base
from fabrikApi.models import DBAssembly

# TODO: indexes

logger = logging.getLogger(__name__)

__all__ = ['DBNotification']


class DBNotification(Base):

    """
    Table to store user notifications.
    """

    # table definitions
    __tablename__ = "notification"
    __table_args__ = (
        Index("uq_notification_created_userid", "date_created", "user_id"),
    )

    # primary
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer) # , ForeignKey('user.id')
    assembly_id = Column(Integer) # , ForeignKey('assembly.id')
    stage_id = Column(Integer)
    peerreview_id = Column(Integer)
    contenttree_id = Column(Integer)
    content_id = Column(Integer)
    value = Column(JSON)
    action = Column('action', String(150), nullable=False, index=True)
    is_read = Column(Boolean, default=False)
    date_created = Column(ArrowType, default=arrow.utcnow)
    date_last_interaction = Column(ArrowType, default=arrow.utcnow)

    def __init__(self, action, user_id):
        assert action, "empty action"
        self.action = action
        self.user_id = user_id


    def __json__(self, request):

        # Check permission 
        assert self.user_id == request.local_userid

        assembly = request.dbsession.query(DBAssembly).get(self.assembly_id)

        return {
            'id': self.id,
            'assembly_identifier': assembly.identifier,
            'date_created': self.date_created,
            'user_id': self.user_id,
            'is_read': self.is_read,
            'stage_id': self.stage_id,
            'value': self.value,
            'peerreview_id': self.peerreview_id,
            'content_id': self.content_id,
            'contenttree_id': self.contenttree_id,
            'action': self.action
        }

    def set_read(self):
        self.is_read = True

def initiate_notification(
        request, action, user_id, assembly, stage=None, peerreview=None, 
        contenttree=None, contenttree_id=None, content=None, value=None
    ):
    
    new_notification = DBNotification(
        action=action,
        user_id=user_id
    )

    if stage:
        new_notification.stage_id = stage.id
    if contenttree:
        new_notification.contenttree_id = contenttree.id
    if contenttree_id:
        new_notification.contenttree_id = contenttree_id
    if content:
        new_notification.content_id = content.id
    if stage:
        new_notification.stage_id = stage.id
    if assembly:
        new_notification.assembly_id = assembly.id
    if peerreview:
        new_notification.peerreview_id = peerreview.id
    new_notification.value = value
        
    request.dbsession.add(new_notification)
    request.dbsession.flush()

    return new_notification
