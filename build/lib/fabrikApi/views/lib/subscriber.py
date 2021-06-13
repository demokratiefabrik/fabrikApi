# from fabrikApi.models.assembly import get_assembly_progression_of_current_user
from fabrikApi.models.contenttree.content import DBContentProgression
from fabrikApi.models.lib.core import get_or_create_progression
import logging
from fabrikApi.util.peerreview_manager import PeerreviewManager
from fabrikApi.util.lib import number_of_days_passed
import arrow
import datetime
from pyramid.httpexceptions import exception_response
from pyramid.events import subscriber
from fabrikApi.util.events import EventAssemblyVisit, EventContentCreated, EventFirstAssemblyVisit,  \
    EventFirstStageVisit, EventPeerReviewApproved, EventPeerReviewInitialized, EventSetContentAsDiscussed, EventStageCompleted, \
    EventStageUnalert, EventStageVisit, \
    EventStageFocusContent
from fabrikApi.util.events import EventContentRated, EventContentSalienced, \
    EventFirstContentVisit, EventContentVisit

logger = logging.getLogger(__name__)


@subscriber(EventAssemblyVisit, EventFirstAssemblyVisit)
def notified_after_an_assembly_has_been_entered(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is missing ---."
    assert event.assembly, "assembly is missing---."
    assert event.progression, "progression is missing---."
    
    # UPDATE LAST ACTIVITY!
    ago15minutes = arrow.utcnow() - datetime.timedelta(minutes=15)
    if not event.progression.date_last_interaction or event.progression.date_last_interaction < ago15minutes:
        event.progression.date_last_interaction = arrow.utcnow()

    # Record Client IP
    if not event.assembly.is_manager:
        event.progression.assert_distinct_ip_limit(event.request)

    # UPDATE LAST DAY SESSION!
    # Reset daily data: if last session has been before today
    last_session = event.progression.date_last_day_session
    if last_session and number_of_days_passed(last_session) <= 1:
        return None

    # Its time to reschedule the stage!
    # Put on schedule every new date!!!
    event.progression.number_of_day_sessions += 1
    event.progression.date_last_day_session = arrow.utcnow()
    event.progression.number_of_proposals_today = 0
    event.progression.number_of_comments_today = 0
    event.progression.todays_ips = [event.request.client_addr, ]


@subscriber(EventStageCompleted)
def notified_after_a_stage_has_been_completed(event):

    assert event.request, "request is missing ---."
    assert event.stage, "stage is missing"
    assert event.progression, "stage progression is missing---."

    event.progression.complete()


@subscriber(EventStageUnalert)
def notified_after_a_stage_has_been_unalerted(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is missing ---."
    assert event.stage, "stage is missing"
    assert event.progression, "stage progression is missing---."

    event.progression.setUnalert()

    # One-Time-Stges have to be marked as completed, right now...
    if event.stage.ONE_TIME_STAGE:
        raiseEvent = EventStageUnalert(**event)
        event.request.registry.notify(raiseEvent)

@subscriber(EventStageFocusContent)
def event_raised_when_new_focused_content_is_received(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is missing ---."
    assert event.stage, "stage is missing"
    assert event.content, "content is missing---."
    assert event.progression, "progression is missing---."

    # Update peerreview assignments....
    if not event.stage.custom_data or not event.stage.custom_data.get('RANDOM_FOCUS'):
        return None
   
    # Assign Open Peerreviews to the user...
    peerreview_manager = PeerreviewManager(event.request, contenttree=event.stage.contenttree)
    peerreview_manager.assign_open_peerreviews(event.stage, event.progression, event.content)


@subscriber(EventStageVisit, EventFirstStageVisit)
def notified_after_a_stage_has_been_entered(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is missing ---."
    assert event.stage, "stage is missing"
    assert event.progression, "progression is missing---."

    # patched required.
    event.stage.patch()

    # UPDATE LAST ACTIVITY!
    ago15minutes = arrow.utcnow() - datetime.timedelta(minutes=15)
    if not event.progression.date_last_interaction or event.progression.date_last_interaction < ago15minutes:
        event.progression.date_last_interaction = arrow.utcnow()

    # Is it time to re-schedule stage (set in alert state?)
    # if last session has been before -days, then set alerted flag
    # UPDATE LAST DAY SESSION!
    # Update date of last session: if last session has been before today, => set alerted flag
    last_session = event.progression.date_last_day_session
    if last_session and (number_of_days_passed(last_session) <= event.stage.SCHEDULE_ALERT_FREQUENCY_IN_DAYS):
        return None

    if event.progression.completed:
        return None

    logger.info("RESET STAGE %s" % event.stage.title)
    # Update date of last session:
    event.progression.alerted = True
    event.progression.date_last_day_session = arrow.utcnow()
    event.progression.number_of_day_sessions += 1
    
    # Reset focused content every day....
    event.progression.focused_content_id = None

# CONTENT SUBSRUIBERS

@subscriber(EventContentRated)
def notified_after_a_content_has_been_rated(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is not transmitted"
    assert event.content, "content is not transmitted"
    assert event.progression, "progression is not transmitted"

    # event.progression.complete()
    event.progression.date_last_interaction = arrow.utcnow()
    if event.prior is None:
        event.request.current_user.content_rating_count += 1


@subscriber(EventContentSalienced)
def notified_after_a_content_has_been_salienced(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is not transmitted"
    assert event.content, "content is not transmitted"
    assert event.progression, "progression is not transmitted"

    # event.progression.setUnalert()
    event.progression.date_last_interaction = arrow.utcnow()
    if event.prior is None:
        event.request.current_user.content_salience_count += 1
        # TODO: is this used?


@subscriber(EventSetContentAsDiscussed)
def notified_after_a_content_has_been_discussed(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is not transmitted"
    assert event.content, "content is not transmitted"

    # CONTENT ITSELF...
    # get progression where missing...    
    if not event.progression:
        
        # Get ContentProgression
        event.progression = get_or_create_progression(
            event.request,
            DBContentProgression,
            auto_create=True,
            event_when_creating_entry=EventFirstContentVisit,
            event_when_reusing_entry=EventContentVisit,
            user_id=event.request.local_userid,
            content=event.request.content,
            is_manager=event.request.assembly.is_manager,
            content_id=event.content.id)
    
    # set discussed flag
    assert event.progression
    event.progression.set_discussed()

    # TOPIC, if transmitted and if not identical...
    # get progression where missing...    
    if event.topic_progression:
        # set discussed flag
        assert event.topic_progression
        event.topic_progression.set_discussed()


@subscriber(EventContentVisit, EventFirstContentVisit)
def notified_after_a_content_has_been_entered(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is not transmitted"
    assert event.progression, "progression is not transmitted"

    # patched required.
    # assert event.content.patched, "should be patched here"


@subscriber(EventContentCreated)
def notified_after_a_content_has_been_created(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is not transmitted"
    assert event.content, "content is not transmitted"
    assert event.progression, "progression is not transmitted"

    # event.progression.setUnalert()
    event.progression.date_last_interaction = arrow.utcnow()
    event.request.current_user.content_created_count += 1

    assert event.request.assembly.__progression__
    event.request.assembly.__progression__.number_of_comments += 1
    event.request.assembly.__progression__.number_of_comments_today += 1


@subscriber(EventPeerReviewInitialized)
def notified_after_peerreview_init(event):

    # reorder of siblings if this is random-order content.
    assert event.content, "content is missing"
    assert event.request.assembly, "assembly is missing"

    event.request.assembly.__progression__.number_of_proposals += 1
    event.request.assembly.__progression__.number_of_proposals_today += 1


@subscriber(EventPeerReviewApproved)
def notified_after_approved_peerreview(event):

    # reorder of siblings if this is random-order content.
    assert event.content, "content is missing"
    # assert event.request.contenttree, "contenttree is missing"

    # TODO: reorder parent if necessary
    # is_in_random_order = request.content.is_in_random_order
    # reorder order_position: Do we have to reorder childs in some branches.
    # (only at content types with fixed position_order)
    # when parent_id changes: it may return both, the old and the new parent_id.
    # in all other cases it may return only the current parent_id.
    # branches_to_reorder = get_branches_to_reorder(request, uptodate_parent, uptodate_type, uptodate_order_position)
