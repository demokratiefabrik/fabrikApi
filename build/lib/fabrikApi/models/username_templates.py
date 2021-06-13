## -*- coding: utf-8 -*-
# flake8: noqa

"""
A list of available usernames. New Users randomly draw a username from this list. 

"""

import logging

from sqlalchemy import Boolean, Column, Integer, Unicode, or_, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import JSON
from sqlalchemy_utils import ArrowType

from fabrikApi.models.meta import Base
from fabrikApi.models.mixins import BaseDefaultObject

logger = logging.getLogger(__name__)

__all__ = ['DBUsernameTemplates']


class DBUsernameTemplates(Base):

    """
    Contains a List of all available usernames
    """

    # Table Definition
    __tablename__ = "username_templates"

    # primaries & uniques
    id = Column(Integer, primary_key=True)
    username = Column(Unicode(150), nullable=False)
    custom_data = Column(JSON, nullable=True)

    def __init__(self, username, custom_data):
        assert username, "invalid username"
        self.custom_data = custom_data
        self.username = username

    def __str__(self):
        return "User: %s [%s/%s (username: %s)]" % (self.id, self.username, self.custom_data)

    def __json__(self):
        # TODO: what information is revealed in the app?
        return "User: %s [%s/%s]" % (self.id, self.username, self.custom_data)
