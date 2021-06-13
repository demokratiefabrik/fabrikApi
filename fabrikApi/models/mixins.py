
import logging
import arrow
import sqlalchemy.types as types
from sqlalchemy import Boolean, Column, ForeignKey, Integer, text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import ArrowType

logger = logging.getLogger(__name__)


class BaseDefaultObject(object):
    """
    Extend SqlAlchemy Base class by custom methods that can be used in every model.
    """

    # relationships
    @declared_attr
    def user_created_id(self):
        return Column(Integer, ForeignKey('user.id'))

    @declared_attr
    def user_modified_id(self):
        return Column(Integer, ForeignKey('user.id'))

    # content
    date_start = Column(ArrowType)
    date_end = Column(ArrowType)
    disabled = Column(Boolean, default=False)
    deleted = Column(Boolean, default=False)
    date_created = Column(ArrowType, default=arrow.utcnow)
    date_modified = Column(
        ArrowType,
        server_default=text('CURRENT_TIMESTAMP')
    )
    
    # TODO: modified date is probably not utc

    def disable(self):
        """ method to disable assembly """
        self.disabled = True

    def enable(self):
        """ method to enable assembly """
        self.disabled = False

    def delete(self):
        """ method to disable assembly """
        self.deleted = True

    def get_response_json(self, request):
        """ Attach the json values to all json responses."""

        response = {
            'id': self.id,
            'date_modified': self.date_modified,
            'date_created': self.date_created
        }
        return (response)

    @property
    def is_active(self):
        too_early = self.date_start and arrow.utcnow() < self.date_start
        too_late = self.date_end and arrow.utcnow() > self.date_end
        return not self.deleted and not self.disabled and not too_early and not too_late

    _include_extra_data = False

    @property
    def include_extra_data(self):
        """ By this flag one can clarify, that related extra-data shall be included in the json
        responses (see __json__ methods). Extra-data might be plugin-data or user-progression-data.
        Typically: in get reqests the extra data is loaded; but not in collection requests.
        """
        return self._include_extra_data

    @include_extra_data.setter
    def include_extra_data(self, value):
        assert bool(value) in (True, False), "invalid boolean type, hmm???"
        self._include_extra_data = bool(value)


class BaseProgressionObject(object):
    """
    Extend SqlAlchemy Base class by custom methods that can be used in every model.
    """

    by_manager = Column(Boolean, default=False)
    alerted = Column(Boolean, default=False)
    date_created = Column(ArrowType, default=arrow.utcnow)
    date_last_interaction = Column(ArrowType)

    def alert(self):
        """ very important task => alerting user for this stage """
        self.alerted = True

    def get_response_json(self, request):
        """ Attach the json values to all json responses."""

        response = {
            'user_id': self.user_id,
            'date_created': self.date_created,
            # 'status': self.status,
            # 'access_sub': request.authenticated_userid,
            'access_date': arrow.utcnow(),

        }
        return (response)


class ChoiceType(types.TypeDecorator):

    impl = types.String(100)

    def __init__(self, choices, **kw):
        self.choices = dict(zip(choices, choices))
        super(ChoiceType, self).__init__(**kw)

    def process_bind_param(self, value, dialect):
        return [v for k, v in self.choices.items() if k == value][0]

    def process_result_value(self, value, dialect):
        assert value in self.choices, "%s is not element of %s" % (value, self.choices)
        return self.choices[value]
