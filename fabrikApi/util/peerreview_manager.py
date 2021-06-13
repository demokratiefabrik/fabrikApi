# -*- coding: utf-8 -*-
from fabrikApi.util.lib import date_with_midnightlag
import math
import random
from get_docker_secret import get_docker_secret
from fabrikApi.models.contenttree.content import DBContent
import logging
from collections import namedtuple

from sqlalchemy import and_
from sqlalchemy_filters.filters import apply_filters

from fabrikApi.models import DBContentPeerReview, DBContentPeerReviewProgression
from fabrikApi.models.mixins import arrow
from fabrikApi.models.user import DBUser

logger = logging.getLogger(__name__)


class PeerreviewManager(object):

    """
    List all peer reviews of current assembly

    """
    user = None
    request = None
    contenttree = None
    peerreviews = None

    def __init__(self, request, contenttree):
        assert request is not None, "empty request...."
        assert int(get_docker_secret('fabrikapi_peerreview_probability_for_non_random_topic', 10))

        self.request = request
        self.contenttree = contenttree
        self.load_user_data = not request.has_administrate_permission

    def load_peerreviews(self):
        """ get peerreviews.."""

        assert self.request, "empty request...."
        assert self.contenttree, "empty contenttree...."

        logger.debug("load contenttree")

        peerreview_tuples = self._load_peerreview_tuples()

        return ({
            # 'identifier': self.request.assembly.identifier,
            # 'date_last_tree_modification': self.contenttree.date_last_tree_modification,
            'entries': peerreview_tuples,
            'acl': self.request.get_auth_roles(context=self.contenttree),
            'access_date': arrow.utcnow(),
            'update_date': arrow.utcnow(),
            'access_sub': self.request.authenticated_userid})

    def load_modified_peerreviews(self, modificationDate):
        """ get contenttree.."""
        assert self.request, "Invalid request"
        assert self.contenttree, "invalid contenttree"
        logger.debug("load contenttree (modified contents)")
        return self._load_peerreview_tuples(modificationDate=modificationDate)
    
    def load_open_peerreviews(self):
        """ get contenttree.."""
        assert self.request, "Invalid request"
        assert self.contenttree, "invalid contenttree"
        logger.debug("load peerreviews (open only)")
        return self._load_peerreview_tuples(filter_open_only=True, not_in_json_format=True)
    
    def _load_peerreview_tuples(self, modificationDate=None, filter_open_only=False, not_in_json_format=False):
        """ Query data from the DB and return list of {content, progression} tuples """

        # Check indices
        filter_spec = [
            {'model': 'DBContentPeerReview', 'field': 'contenttree_id', 'op': '==', 'value': self.contenttree.id},
            {
                'or': [
                    {'model': 'DBContentPeerReview', 'field': 'disabled', 'op': 'is_null'},
                    {'model': 'DBContentPeerReview', 'field': 'disabled', 'op': '==', 'value': False}]
            },
            {'model': 'DBContent', 'field': 'deleted', 'op': '!=', 'value': True},
            {'model': 'DBContent', 'field': 'disabled', 'op': '!=', 'value': True}
        ]
        
        if modificationDate:
            filter_spec.append({
                'or': [
                    {'model': 'DBContentPeerReview', 'field': 'date_modified', 'op': '>=', 'value': modificationDate},
                    {'model': 'DBContentPeerReviewProgression', 'field': 'date_created', 'op': '>=', 'value': modificationDate}
                ]
            })

        if filter_open_only:
            filter_spec.append({
                'and': [
                    {'model': 'DBContentPeerReview', 'field': 'approved', 'op': '!=', 'value': True},
                    {'model': 'DBContentPeerReview', 'field': 'rejected', 'op': '!=', 'value': True}
                ]
            })

        # Load Contents: Which contents shall be loaded:
        if self.load_user_data:
            query = self.request.dbsession.query(DBContentPeerReview, DBContent, DBContentPeerReviewProgression)
        else:
            query = self.request.dbsession.query(DBContentPeerReview)
        query = query.join(DBContent, DBContent.id == DBContentPeerReview.content_id)
        query = apply_filters(query, filter_spec)

        # load also progression data:
        if self.load_user_data:
            query = query.outerjoin(
                DBContentPeerReviewProgression,
                and_(
                    DBContentPeerReview.id == DBContentPeerReviewProgression.content_peerreview_id,
                    DBContentPeerReviewProgression.user_id == self.request.local_userid
                )
            )
        peerreviews = query.all()

        # Managers
        if not self.load_user_data:
            PeerReviewTuple = namedtuple('DBContentPeerReviewTuple',
                'DBContentPeerReview DBContentPeerReviewProgression')
            peerreviews = list(map(
                lambda peerreview: PeerReviewTuple(DBContentPeerReview=peerreview, DBContentPeerReviewProgression=None),
                peerreviews))

        if not not_in_json_format:
            # Load Usernames!
            creator_ids = {v.DBContentPeerReview.user_created_id: True for k, v in enumerate(peerreviews)}
            usernames = self.request.dbsession.query(DBUser.id, DBUser).filter(DBUser.id.in_(creator_ids)).all()
            creator_usernames = {k: v for k, v in usernames}
        
        # Prepare Object for Json Response
        for content in peerreviews:
            # PERMISSION and lineage Setup
            content.DBContent.setup_lineage(self.request)
            self.request.has_permission('observe', content.DBContent)

        # Re-Arrange
        if not_in_json_format:
            return peerreviews
        else:
            peerreview_tuples = {  
                k.DBContentPeerReview.id: {
                    'content': k.DBContent,
                    'peerreview': k.DBContentPeerReview,
                    'progression': k.DBContentPeerReviewProgression,
                    'creator': creator_usernames[k.DBContentPeerReview.user_created_id]}\
                for v, k in enumerate(peerreviews)
            }

        return peerreview_tuples

    def assign_open_peerreviews(self, stage, stage_progression, focused_content):
        """ 
        A Method to assign open peerreviews to the user.
        Shall be ran only once a day!         
        Number of assigned peerreviews is strictly limited:,
        - by config value
        - by the number of days the user has visitied the stage (=> decreasing number)
        Try to assign mostly peerreviews of the currently focues stage.. (which has been randomly assigned)        
        """
        
        def calculate_number_of_peerreviews_to_assign(stage_progression):
            # number of new peerreviews a day...
            days = stage_progression.number_of_day_sessions
            nof_new_peerreviews = 0
            if days == 1:
                nof_new_peerreviews = 7
            elif days == 2:
                nof_new_peerreviews = 5
            elif days <= 5:
                nof_new_peerreviews = 3
            else:
                nof_new_peerreviews = 2
            return nof_new_peerreviews

        open_peerreviews = self.load_open_peerreviews()

        # assert that no new peerreviews were assigned today...
        today_assigned = list(filter(
            lambda tuple:
                (tuple.DBContentPeerReviewProgression is not None) and \
                (tuple.DBContentPeerReviewProgression.date_created.date() == date_with_midnightlag()),
            open_peerreviews)
        )

        assert len(today_assigned) == 0

        # Collect all unassigned peerreviews... (and not created by the user...)
        unassigned = list(filter(
            lambda tuple: \
                (tuple.DBContentPeerReview.user_created_id != self.request.local_userid) and \
                (not tuple.DBContentPeerReviewProgression), \
            open_peerreviews))

        # still_open
        unassigned_in_random_focus_topic = list(filter(
            lambda tuple: tuple.DBContent.parent_id == focused_content.id, unassigned
        ))
        unassigned_elsewhere = list(filter(
            lambda tuple: tuple.DBContent.parent_id != focused_content.id, unassigned
        ))
        assert len(unassigned_elsewhere) + len(unassigned_in_random_focus_topic) == len(unassigned)
        
        # There is a certain number of peerrewviews to be assigned for each user each day.
        # most of them are the peerreviews within the randomly drawn focus topic.
        # the minority is  drawn (with a certain probability) from the rest 
        # in case there are too few in one of the groups => the free space is moved to the other group....
        nof_new_peerreviews = calculate_number_of_peerreviews_to_assign(stage_progression)
        assert nof_new_peerreviews
        # 80% are drawn in the focus topic
        nof_new_peerreviews_in_focus_topic = math.ceil(nof_new_peerreviews / 100 * 80)
        assert nof_new_peerreviews_in_focus_topic
        # draw more peerreviews from elsehere  (wheren there are too few in the focus topic)
        nof_new_peerreviews_in_focus_topic = min(nof_new_peerreviews_in_focus_topic, len(unassigned_in_random_focus_topic))
        nof_new_peerreviews_elsewhere = nof_new_peerreviews - nof_new_peerreviews_in_focus_topic
        if nof_new_peerreviews_elsewhere > len(unassigned_elsewhere):
            # take more of the focus topic (in case there are too few elsewhere)
            nof_new_peerreviews_in_focus_topic += nof_new_peerreviews_elsewhere - len(unassigned_elsewhere)
            nof_new_peerreviews_elsewhere =len(unassigned_elsewhere)        
        assert (nof_new_peerreviews_in_focus_topic + nof_new_peerreviews_elsewhere) == nof_new_peerreviews

        # sample peerreview in focus topic
        selected_peerreviews_in_focus_topic = random.sample(
            unassigned_in_random_focus_topic,
            min(nof_new_peerreviews_in_focus_topic, len(unassigned_in_random_focus_topic)))

        # sample peerreviews elsewhere (in non-randomly selected topics)
        # The chance to be selected for each peerreview shall be 1:10: / however, consider the maximum number of peerreviews
        probability = int(get_docker_secret('fabrikapi_peerreview_probability_for_non_random_topic', 10))
        selected_peerreviews_elsewhere = []
        if nof_new_peerreviews_elsewhere:
            selected_peerreviews_elsewhere = list(filter(
                lambda peerreview: random.random() <= (probability/100),
                unassigned_elsewhere)
            )
            if nof_new_peerreviews_elsewhere < len(selected_peerreviews_elsewhere):
                selected_peerreviews_elsewhere = random.sample(
                    selected_peerreviews_elsewhere,
                    nof_new_peerreviews_elsewhere)

        # finalization: create progression entries for all the selected peerreviews
        selected_peerreviews = selected_peerreviews_elsewhere + selected_peerreviews_in_focus_topic
        assert len(selected_peerreviews) <= nof_new_peerreviews
       
        for peerreview in selected_peerreviews:
            assert peerreview.DBContentPeerReviewProgression is None
            progression = DBContentPeerReviewProgression(
                user_id=self.request.local_userid, 
                content_peerreview=peerreview.DBContentPeerReview)
            self.request.dbsession.add(progression)

        return len(selected_peerreviews)
