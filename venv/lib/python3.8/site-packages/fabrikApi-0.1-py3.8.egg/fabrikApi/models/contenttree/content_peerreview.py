import logging
import arrow

from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Index
from sqlalchemy.sql.sqltypes import Float
from sqlalchemy.types import JSON
from sqlalchemy_utils.types.arrow import ArrowType
from sqlalchemy import text

from fabrikApi.models.meta import Base
from fabrikApi.models.mixins import ChoiceType
from fabrikApi.util.events import EventPeerReviewApproved, EventPeerReviewRejected
# , EventPeerReviewResubmit

__all__ = ['DBContentPeerReview', 'DBContentPeerReviewProgression', 'initiate_peer_review']

logger = logging.getLogger(__name__)


class DBContentPeerReview(Base):
    """ lead proposals through the peer-review."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"

    OperationTypes = {
        INSERT: "INSERT",
        UPDATE: "UPDATE"
    }

    # Pyramid Object authorization
    __roles__ = None
    __parent__ = None
    __name__ = None


    # table definition
    __tablename__ = "content_peerreview"
    __table_args__ = (
        # Index('default_search', "contenttree_id", "title", "text"),
        # Ensure unique progression for each user:
        # Index("uq_contentprogression_contentid_userid_unique", "content_id", "user_id", unique=True),
        # Index("ix_contentprogression_contentid_userid_modifieddate", "content_id", "user_id", "date_modified"),
    )

    # primary key
    id = Column(Integer, primary_key=True)

    # relationships
    content_id = Column(Integer, ForeignKey('content.id'), nullable=False)
    content = relationship("DBContent", foreign_keys=[content_id])
    # content = relationship("DBContent", ForeignKey('content.id'), back_populates="content_peerreviews")
    contenttree_id = Column(Integer, ForeignKey('contenttree.id'))
    contenttree = relationship("DBContentTree", back_populates="content_peerreviews")
    user_created_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship("DBUser", backref="content_proposals")
    content_peerreview_progressions = relationship(
        "DBContentPeerReviewProgression", 
        back_populates="content_peerreview")

    # operations
    operation = Column(ChoiceType(OperationTypes), nullable=False)
    # data_to_apply_on_success
    data_to_apply_on_success = Column(JSON, nullable=False)
    # # comment
    # comment = Column(Unicode(255), default=0)

    # Settings
    responded_quorum = Column(Integer, default=None)    # miminum number of responders
    # quorum: the minimum number of respondends to reach before the propsal becomes accepted/rejected.
    approving_rate = Column(Integer, default=None)
    # the rate required the propsal becomes accepted:

    disabled = Column(Boolean, default=False)
    date_created = Column(ArrowType, default=arrow.utcnow)
    date_modified = Column(
        ArrowType,
        server_default=text('CURRENT_TIMESTAMP')
    )
    date_approved = Column(ArrowType)
    date_rejected = Column(ArrowType)

    # PeerReview Status
    nof_invited = Column(Integer)
    nof_responded = Column(Integer)
    nof_approved = Column(Integer)
    nof_rejected = Column(Integer)
    nof_criteria_accept1 = Column(Float)
    nof_criteria_accept2 = Column(Float)
    nof_criteria_accept3 = Column(Float)

    # Result
    approved = Column(Boolean, default=False)
    rejected = Column(Boolean, default=False)

    # not required: for allowing to discuss this proposal in the forum
    discussion_content_id = Column(Integer, ForeignKey('content.id'))
    discussion_content = relationship("DBContent", foreign_keys=[discussion_content_id])

    # branches_to_reorder=[],
    def __init__(self, user_created_id, content, operation, data_to_apply_on_success):
        """ Initialize a modification proposal:

        Note:
        responded_quorum = 3  # at least three respondents
        approving_rate = 50  # 50 percent reject respective  acceptance required
        """

        assert user_created_id, "Invalid user_id"
        assert content, "invalid content"
        assert operation is not None and operation in self.OperationTypes, "invalid operation type..."

        self.user_created_id = user_created_id
        self.content = content
        self.contenttree_id = content.contenttree_id
        self.operation = operation
        self.data_to_apply_on_success = data_to_apply_on_success  # data needed to apply the proposal

        quorum, rate = self.content.get_approving_conditions(peerreview=self)
        self.responded_quorum = quorum
        self.approving_rate = rate

    def __repr__(self):
        return "Propsal - Arg: %s Usr: %s Operation: %s Rejected: %s Approved: %s" % (
            self.content, self.user_created_id, self.operation, self.rejected, self.approved)

    def __json__(self, request):

        return {
            'id': self.id,
            'content_id': self.content_id,
            'discussion_content_id': self.discussion_content_id,
            'contenttree_id': self.contenttree_id,
            'operation': self.operation,
            'data_to_apply_on_success': self.data_to_apply_on_success,
            'approved': self.approved,
            'rejected': self.rejected,
            'user_created_id': self.user_created_id,
            'responded_quorum': self.responded_quorum,
            'approving_rate': self.approving_rate,
            'date_created': self.date_created,
            'date_approved': self.date_approved,
            'date_rejected': self.date_rejected,
            'nof_invited': self.nof_invited,
            'nof_responded': self.nof_responded,
            'nof_approved': self.nof_approved,
            'nof_rejected': self.nof_rejected,
            'nof_criteria_accept1': self.nof_criteria_accept1,
            'nof_criteria_accept2': self.nof_criteria_accept2,
            'nof_criteria_accept3': self.nof_criteria_accept3
        }

    def setup_lineage(self, request):
        if self.__roles__ is not None:
            return None

        # already setup
        self.__name__ = 'peerreview'
        self.__parent__ = self.content
        self.__local_userid__ = request.local_userid
        self.__assembly_identifier__ = self.contenttree.assembly.identifier
        # self.patch()
        self.__parent__.setup_lineage(request)
        self.__roles__ = request.get_auth_roles(self)


    @property
    def nof_approvals_required_to_pass(self):
        # => dont ask more participants, if already six (with a quorum of ten) responded positive
        return self.responded_quorum/100 * self.approving_rate
    @property
    def nof_rejects_required_to_fail(self):
        # => dont ask more participants, if already five (with a quorum of ten) responded negative
        return self.responded_quorum/100*(100-self.approving_rate)

    def update_response_numbers(self):
        
        # dont change anything, if 
        assert not self.approved
        assert not self.rejected
        
        progressions = self.content_peerreview_progressions
        self.nof_approved = 0
        self.nof_rejected = 0
        self.nof_responded = 0
        self.nof_invited = 0
        self.nof_criteria_accept1 = 0
        self.nof_criteria_accept2 = 0
        self.nof_criteria_accept3 = 0
        
        for progression in progressions:
            self.nof_invited += 1
            self.nof_responded += int(progression.response is not None)
            self.nof_approved += int(progression.response is True)
            self.nof_rejected += int(progression.response is False)
            self.nof_criteria_accept1 += 1 if progression.criteria_accept1 is True else 0
            self.nof_criteria_accept2 += 1 if progression.criteria_accept2 is True else 0
            self.nof_criteria_accept3 += 1 if progression.criteria_accept3 is True else 0



    def check(self, request):
        """ Does the peer review came to an end? And which end? """


        # already closed?
        if self.approved or self.rejected:
            return None

        # Update numbers
        self.update_response_numbers()

        # Accept proposal as soon as minimum approving number is reached
        if float(self.nof_approved) > self.nof_approvals_required_to_pass:
            self.approve(request)
            return True

        # Accept proposal as soon as minimum approving number is reached
        if self.nof_rejected >= self.nof_rejects_required_to_fail:
            self.reject(request)
            return False

    def approve(self, request):
        """ The proposal succeeded in the peer Review:
        Now, write all data stored in the data json column to the content object.
        """

        # apply modifications...
        for prop in self.data_to_apply_on_success:
            setattr(
                self.content,
                prop,
                self.data_to_apply_on_success[prop]
            )
        self.approved = True
        self.date_approved = arrow.utcnow()
        
        if self.operation == self.INSERT:
            assert self.content
            self.content.pending_peerreview_for_insert = False
            self.content.rejected_peerreview_for_insert = False
            self.content.completed_peerreview_for_insert = True

        if self.operation == self.UPDATE:
            assert self.content
            self.content.pending_peerreview_for_update = False

        event = EventPeerReviewApproved(request=request, content=self.content, peerreview=self)
        request.registry.notify(event)

    def reject(self, request):
        self.rejected = True
        self.date_rejected = arrow.utcnow()
        
        if self.operation == self.INSERT:
            assert self.content
            self.content.pending_peerreview_for_insert = False
            self.content.rejected_peerreview_for_insert = True

        if self.operation == self.UPDATE:
            assert self.content
            self.content.pending_peerreview_for_update = False

        event = EventPeerReviewRejected(request=request, content=self.content, peerreview=self)
        request.registry.notify(event)


class DBContentPeerReviewProgression(Base):
    """ store all user-specified data e.g. reception of contents
    (ratings, salience indications, read, view, etc.)
    """

    # table definition
    __tablename__ = "content_peerreview_progression"
    __table_args__ = (
        # # SEARCH CONTENT
        # Index('default_search', "contenttree_id", "title", "text"),

        # Ensure unique progression for each user:
        Index("uq_peerreview_userid_unique", "content_peerreview_id", "user_id", unique=True),
        # Index("ix_contentprogression_contentid_userid_modifieddate", "content_id", "user_id", "date_modified"),
    )

    # primary key
    id = Column(Integer, primary_key=True)

    # relationships
    content_peerreview_id = Column(Integer, ForeignKey('content_peerreview.id'), nullable=False)
    content_peerreview = relationship("DBContentPeerReview", back_populates="content_peerreview_progressions")
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship("DBUser", backref="content_peerreview_progressions")
    response = Column(Boolean)
    criteria_accept1 = Column(Boolean)
    criteria_accept2 = Column(Boolean)
    criteria_accept3 = Column(Boolean)

    date_created = Column(ArrowType, default=arrow.utcnow)
    date_responded = Column(ArrowType)

    def __init__(self, user_id, content_peerreview_id=None, content_peerreview=None):
        assert content_peerreview or content_peerreview_id, "invalid peerreview"
        if not content_peerreview_id:
            content_peerreview_id = content_peerreview.id
            
        self.user_id = user_id
        self.content_peerreview_id = content_peerreview_id

    def __json__(self, request):

        # NEVER EVER EXPORT progressions of other users...
        assert request.local_userid == self.user_id, "invalid user data"

        return {
            # 'user_id': self.user_id,
            'response': self.response,
            'date_responded': self.date_responded,
            'criteria_accept1': self.criteria_accept1,
            'criteria_accept2': self.criteria_accept2,
            'criteria_accept3': self.criteria_accept3
        }   

    def set_response(self, response, criteria_accept1, criteria_accept2, criteria_accept3):
        """
        Update approved state
        """

        assert not self.content_peerreview.approved and not self.content_peerreview.rejected
        assert response is False or response is True
        assert criteria_accept1 is False or criteria_accept1 is True
        assert criteria_accept2 is False or criteria_accept2 is True
        assert criteria_accept3 is False or criteria_accept3 is True

        self.date_responded = arrow.utcnow()
        
        self.response = response
        self.criteria_accept1 = criteria_accept1
        self.criteria_accept2 = criteria_accept2
        self.criteria_accept3 = criteria_accept3

        return (True)


def initiate_peer_review(request, operation, content, user_created_id, data_to_apply_on_success={},
                         manually_add_to_the_session=False):
    new_proposal = DBContentPeerReview(
        operation=operation,
        content=content,
        user_created_id=user_created_id,
        data_to_apply_on_success=data_to_apply_on_success
    )

    if not manually_add_to_the_session:
        request.dbsession.add(new_proposal)
        request.dbsession.flush()
        # new_proposal.check(request)
        
    return(new_proposal)
