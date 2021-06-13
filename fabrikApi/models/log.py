## -*- coding: utf-8 -*-
# flake8: noqa

"""
Tracks all User acitivities. The main purpose of this is scientifically. 
It enables easy evaluation of what has happened on the platform.

"""

import logging
from sqlalchemy.sql.sqltypes import JSON
from sqlalchemy_utils import ArrowType
import arrow

from sqlalchemy import Column, Integer, String, Unicode

from fabrikApi.models.meta import Base

logger = logging.getLogger(__name__)    # pylint: disable-msg=C0103

__all__ = ['DBLog']

# NO_EMAIL_NOTIFICATION = 0
# RARE_EMAIL_NOTIFICATION = 1
# FULL_EMAIL_NOTIFICATION = 3

class DBLog(Base):

    """
    Table to log changes on Contents.
    """

    # table definitions
    __tablename__ = "log"
    __table_args__ = ()

    # primary
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer) # , ForeignKey('user.id')
    assembly_id = Column(Integer) # , ForeignKey('assembly.id')
    stage_id = Column(Integer)
    contenttree_id = Column(Integer)
    content_id = Column(Integer)
    peerreview_id = Column(Integer)
    action = Column('action', String(150), nullable=False, index=True)
    value = Column(Unicode(3000), default=u"")
    date_created = Column(ArrowType, default=arrow.utcnow)
    ip = Column(String(150))
    extra = Column(JSON)

    def __init__(self, action, user_id=None, value=None, 
                 assembly_id=None, ip=None):
        assert action, "empty action"
        self.action = action
        self.assembly_id = assembly_id
        self.value = value
        self.ip = ip
        self.user_id = user_id

    @staticmethod
    def create_from_json(action, user_id, value=None, assembly_id=None, contenttree_id=None, 
            stage_id=None, content_id=None, peerreview_id=None, date_created=None, ip=None):
        assert action, "empty action"

        elog = DBLog(action=action)
        elog.assembly_id=assembly_id
        elog.stage_id=stage_id
        elog.peerreview_id=peerreview_id
        elog.content_id=content_id
        elog.contenttree_id=contenttree_id
        elog.user_id=user_id
        elog.value=value
        elog.ip=ip
        elog.date_created=date_created

        return elog
