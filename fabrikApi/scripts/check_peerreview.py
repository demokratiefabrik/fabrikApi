# import csv
from sqlalchemy.sql.elements import and_, not_
from sqlalchemy.sql.expression import case
from sqlalchemy.sql.functions import func
from fabrikApi.models.contenttree.content_peerreview import DBContentPeerReview, DBContentPeerReviewProgression
# import os
import sys

import transaction
from pyramid import testing
from pyramid.paster import get_appsettings, setup_logging
# from pyramid.scripts.common import parse_vars

from fabrikApi.models import get_engine, get_session_factory, get_tm_session
# from fabrikApi.models.meta import Base
# from fabrikApi.models.stage import DBStage
# from datetime import timedelta
# import arrow
import logging

logger = logging.getLogger(__name__)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    # options = parse_vars(argv[2:])
    setup_logging(config_uri)
    # settings = get_appsettings(config_uri, options=options)
    settings = get_appsettings(config_uri)

    engine = get_engine(settings)

    session_factory = get_session_factory(engine)

    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)

        request = testing.DummyRequest()
        request.dbsession = dbsession


        # CHECK OPEN PEERREVIEWS
        open_peerreviews = request.dbsession.query(DBContentPeerReview).filter(
            and_(
                not_(DBContentPeerReview.approved),
                not_(DBContentPeerReview.rejected)
            )).all()
        open_peerreview_ids = list(map(lambda peerreview: peerreview.id, open_peerreviews))
        open_peerreviews_dict = {
            value.id: value for value in open_peerreviews
        }

        logger.info("CRON: Currently Open Peerreviews: %s" % len(open_peerreviews))

        peerreview_responses = request.dbsession\
            .query(
                DBContentPeerReviewProgression.content_peerreview_id.label("content_peerreview_id"),
                func.count(DBContentPeerReviewProgression.content_peerreview_id).label("nof_invited"),
                func.sum(DBContentPeerReviewProgression.response is not None).label("nof_responded"),
                func.sum(case([(DBContentPeerReviewProgression.response, 1)])).label("nof_approved"),
                func.sum(case([(DBContentPeerReviewProgression.response, 0)])).label("nof_rejected"),
                func.sum(DBContentPeerReviewProgression.criteria_accept1).label("nof_criteria_accept1"),
                func.sum(DBContentPeerReviewProgression.criteria_accept2).label("nof_criteria_accept2"),
                func.sum(DBContentPeerReviewProgression.criteria_accept3).label("nof_criteria_accept3")) \
            .group_by(DBContentPeerReviewProgression.content_peerreview_id)\
            .filter(DBContentPeerReviewProgression.content_peerreview_id.in_(open_peerreview_ids)) \
            .all()

        for response in peerreview_responses:
            peerreview = open_peerreviews_dict[response.content_peerreview_id]
            peerreview.nof_responded = int(response.nof_responded)
            peerreview.nof_invited = int(response.nof_invited) if response.nof_invited is not None else 0
            peerreview.nof_approved = int(response.nof_approved) if response.nof_approved is not None else 0
            peerreview.nof_rejected = int(response.nof_rejected) if response.nof_rejected is not None else 0
            # try:
            #     peerreview.nof_invited = int(response.nof_invited)
            # except TypeError:
            #     peerreview.nof_invited = 0  # or whatever you want to do
            # try:
            #     peerreview.nof_approved = int(response.nof_approved)
            # except TypeError:
            #     peerreview.nof_approved = 0  # or whatever you want to do
            # try:
            #     peerreview.nof_rejected = int(response.nof_rejected)
            # except TypeError:
            #     peerreview.nof_rejected = 0  # or whatever you want to do
            peerreview.nof_criteria_accept1 = response.nof_criteria_accept1
            peerreview.nof_criteria_accept2 = response.nof_criteria_accept2
            peerreview.nof_criteria_accept3 = response.nof_criteria_accept3
            peerreview.check(request)

        # TODO: SEND EMAIL WITH CURRENTLY ONGOING PEERREVIEWS...
        request.dbsession.flush()
        transaction.commit()
