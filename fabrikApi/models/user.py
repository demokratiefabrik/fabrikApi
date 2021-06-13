## -*- coding: utf-8 -*-
# flake8: noqa

"""
Register all users. (saves all data that has been transferred from oAUth servers)
Like username, email etc..

"""

from fabrikApi.util.lib import number_of_days_passed
import logging
import arrow

from sqlalchemy import Column, Integer, Unicode, or_, Index, Float, JSON
from sqlalchemy_utils import ArrowType

from fabrikApi.models.meta import Base
from fabrikApi.models.mixins import BaseDefaultObject

logger = logging.getLogger(__name__)

__all__ = ['DBUser']

NO_EMAIL_NOTIFICATION = 0
RARE_EMAIL_NOTIFICATION = 1
SOME_EMAIL_NOTIFICATION = 2
FULL_EMAIL_NOTIFICATION = 3

# BaseDefaultObject
# TODO: not sure if user_created/modified is a good idea...
class DBUser(BaseDefaultObject, Base):

    """
    STORES ALL PARTICIPANTS; ADMINISTRATORS AND MODERATORS
    """

    # Table Definition
    __tablename__ = "user"
    __table_args__ = (
        # Ensure unique progression for each user:
        Index("uq_user_oauth2userid_oauth2provider", "oauth2_user_id", "oauth2_provider", 
        unique=True),
    )

    # primaries & uniques
    id = Column(Integer, primary_key=True)
    oauth2_provider = Column(Unicode(150), nullable=False)
    oauth2_user_id = Column(Integer, nullable=False)
    username = Column(Unicode(100), default=None)  # username
    custom_data = Column(JSON, nullable=True)

    # to show application tutorial at the firsttime
    # platform_introduction_passed = Column(Boolean, default=False)
    # artificial_moderation_enabled = Column(Boolean, default=True)
    notification_email_frequency = Column(Integer, default=SOME_EMAIL_NOTIFICATION)

    # STATS
    date_last_interaction = Column(ArrowType)  # assembly
    content_rating_count = Column(Integer, default=0)
    content_salience_count = Column(Integer, default=0)
    content_created_count = Column(Integer, default=0)
    agg_response_progression_count = Column(Integer)
    agg_response_salience_avg = Column(Float)
    agg_response_salience_count = Column(Integer)
    agg_response_rating_avg = Column(Float)
    agg_response_rating_count = Column(Integer)
    agg_assembly_number_of_day_sessions = Column(Integer)
    # agg_assembly_date_last_interaction = Column(ArrowType)


    def __init__(self, oauth2_provider, oauth2_user_id, username=None, custom_data={}):
        assert oauth2_user_id, "invalid oauth user_id"
        assert oauth2_provider, "invalid oauth2 provider"
        self.oauth2_user_id = oauth2_user_id
        self.oauth2_provider = oauth2_provider
        self.username = username
        self.custom_data = custom_data

    def __str__(self):
        return "User: %s [%s/%s (username: %s)]" % (self.id, self.oauth2_provider, self.oauth2_user_id, self.username)


    def __json__(self, request):
        # TODO: what information is publi
        response = self.get_response_json(request)        
        response.update({
            'U': self.username,
            'ALT': self.custom_data.get('ALTITUDE'),
            'FN': self.custom_data.get('FULLNAME'),
            'CA': self.custom_data.get('CANTON'),
            'CO': self.custom_data.get('COLOR')
        })

        # DELETED: only admins see deleted stages
        if self.deleted:
            response["deleted"] = self.deleted
            assert request.has_administrate_permission, "no administratte permission"
        
        return(response)

    @property
    def statistics(self):
        
        # days since last interactivity
        days_since_last_interactivity = 0
        last_session = self.date_last_interaction
        if self.date_last_interaction:
            days_since_last_interactivity = number_of_days_passed(self.date_last_interaction)

        return ({
            'DAYS': self.agg_assembly_number_of_day_sessions,
            'DLI': days_since_last_interactivity,
            'CRC': self.content_rating_and_salience_count,
            'CCC': self.content_created_count,
            'RSC': self.agg_response_salience_count,
            'RSA': self.agg_response_salience_avg
        })

    @property
    def content_rating_and_salience_count(self):
        return int(self.content_rating_count) + int(self.content_salience_count)
