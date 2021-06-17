# from fabrikApi.models.assembly import get_assembly_progression_of_current_user
from fabrikApi.models.notification import initiate_notification
from fabrikApi.util.constants import MONITOR_ACTION_COMPLETE_STAGE, MONITOR_ACTION_CREATE_CONTENT, MONITOR_ACTION_DELETE_CONTENT, \
    MONITOR_ACTION_EDIT_CONTENT, MONITOR_ACTION_FOCUS_CONTENT, MONITOR_ACTION_INIT_PEERREVIEW, MONITOR_ACTION_MOVE_CONTENT, \
    MONITOR_ACTION_NEW_DAY_SESSION, MONITOR_ACTION_UNALERT_STAGE, NOTIFICATION_ACTION_DELETE_CONTENT, \
    NOTIFICATION_ACTION_EDIT_CONTENT, NOTIFICATION_ACTION_MOVE_CONTENT, NOTIFICATION_ACTION_PEERREVIEW_APPROVED, NOTIFICATION_ACTION_PEERREVIEW_ASSIGNED, NOTIFICATION_ACTION_PEERREVIEW_INIT_UPDATE, NOTIFICATION_ACTION_PEERREVIEW_INIT_INSERT, NOTIFICATION_ACTION_PEERREVIEW_REJECTED, \
    NOTIFICATION_ACTION_RESPONSE_TO_CONTENT
from fabrikApi.models.contenttree.content import DBContentProgression
from fabrikApi.models.lib.core import get_or_create_progression
import logging
from fabrikApi.util.peerreview_manager import PeerreviewManager
from fabrikApi.util.lib import number_of_days_passed
import arrow
import datetime
from pyramid.events import subscriber
from fabrikApi.util.events import EventAssemblyVisit, EventContentCreated, EventContentDeleted, \
    EventContentEdited, EventContentMoved, EventContentRead, EventFirstAssemblyVisit,  \
    EventFirstStageVisit, EventPeerReviewApproved, EventPeerReviewInitialized, EventPeerReviewRejected, EventSetContentAsDiscussed, EventStageCompleted, \
    EventStageUnalert, EventStageVisit, \
    EventStageFocusContent
from fabrikApi.util.events import EventContentRated, EventContentSalienced, \
    EventFirstContentVisit, EventContentVisit
from fabrikApi.models.log import DBLog

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
    is_manager = event.request.has_manage_permission(event.assembly.identifier)
    if not is_manager:
        event.progression.assert_distinct_ip_limit(event.request)
        
    # UPDATE LAST DAY SESSION!
    # Reset daily data: if last session has been before today
    last_session = event.progression.date_last_day_session
    if last_session and (number_of_days_passed(last_session) < 1):
        return None

    # Its time to reschedule the stage!
    # Put on schedule every new date!!!
    if event.progression.number_of_day_sessions is None:
        event.progression.number_of_day_sessions = 0    
    event.progression.number_of_day_sessions += 1
    event.progression.date_last_day_session = arrow.utcnow()
    event.progression.number_of_proposals_today = 0
    event.progression.number_of_comments_today = 0
    event.progression.todays_ips = [event.request.client_addr, ]

    # add entry to monitor table
    elog = DBLog.create_from_json(
        user_id=event.request.local_userid,
        assembly_id=event.assembly.id,
        action=MONITOR_ACTION_NEW_DAY_SESSION,
        date_created=arrow.utcnow())
    event.request.dbsession.add(elog)


@subscriber(EventStageCompleted)
def notified_after_a_stage_has_been_completed(event):

    assert event.request, "request is missing ---."
    assert event.stage, "stage is missing"
    assert event.progression, "stage progression is missing---."

    event.progression.complete()

    # add entry to monitor table
    elog = DBLog.create_from_json(
        user_id=event.request.local_userid,
        assembly_id=event.request.assembly.id,
        stage_id=event.stage.id,
        action=MONITOR_ACTION_COMPLETE_STAGE,
        date_created=arrow.utcnow())
    event.request.dbsession.add(elog)


@subscriber(EventStageUnalert)
def notified_after_a_stage_has_been_unalerted(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is missing ---."
    assert event.stage, "stage is missing"
    assert event.progression, "stage progression is missing---."

    event.progression.setUnalert()

    # One-Time-Stges have to be marked as completed, right now...
    if event.stage.ONE_TIME_STAGE:
        raiseEvent = EventStageCompleted(
            request=event.request,
            stage=event.stage,
            progression=event.progression)
        event.request.registry.notify(raiseEvent)

    # add entry to monitor table
    # elog = DBLog.create_from_json(
    #     user_id=event.request.local_userid,
    #     assembly_id=event.request.assembly.id,
    #     stage_id=event.stage.id,
    #     action=MONITOR_ACTION_UNALERT_STAGE,
    #     date_created=arrow.utcnow())
    # event.request.dbsession.add(elog)


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

    # continue only for delegates
    if not event.request.has_delegate_permission(event.request.assembly.identifier):
        return None
   
    # Assign Open Peerreviews to the user...
    peerreview_manager = PeerreviewManager(event.request, contenttree=event.stage.contenttree)
    nof_new_peerreviews = peerreview_manager.assign_open_peerreviews(event.stage, event.progression, event.content)

    # add notification
    if nof_new_peerreviews > 0:
        notification = initiate_notification(
            request=event.request,
            action=NOTIFICATION_ACTION_PEERREVIEW_ASSIGNED,
            user_id=event.request.local_userid,
            assembly=event.request.assembly,
            stage=event.stage,
            contenttree_id=event.stage.contenttree_id,
            value=nof_new_peerreviews)

        # straight forward: return to user...
        if event.response:
            if not event.response.get('notifications'):
                event.response['notifications'] = {}
            event.response['notifications'][notification.id] = notification


    # add entry to monitor table
    elog = DBLog.create_from_json(
        user_id=event.request.local_userid,
        assembly_id=event.request.assembly.id,
        stage_id=event.stage.id,
        content_id=event.content.id,
        action=MONITOR_ACTION_FOCUS_CONTENT,
        date_created=arrow.utcnow())
    event.request.dbsession.add(elog)



@subscriber(EventFirstStageVisit)
def notified_after_a_stage_has_been_entered_for_the_first_time(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is missing ---."
    assert event.stage, "stage is missing"
    assert event.progression, "progression is missing---."

    # patched required.
    event.stage.patch()

    # UPDATE LAST ACTIVITY!
    event.progression.date_last_interaction = arrow.utcnow()

    # Is it time to re-schedule stage (set in alert state?)
    # if last session has been before -days, then set alerted flag
    # UPDATE LAST DAY SESSION!
    # Update date of last session: if last session has been before today, => set alerted flag
    event.progression.number_of_day_sessions = 1
    event.progression.date_last_day_session = arrow.utcnow()
    # if event.progression.date_last_day_session:   
    # Reset focused content every day....
    event.progression.focused_content_id = None

    # Update alert flag:
    if event.request.has_delegate_permission(event.request.assembly.identifier):
        event.progression.alerted = True


@subscriber(EventStageVisit)
def notified_after_a_stage_has_been_reentered(event):

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
    event.stage.title
    if last_session and (number_of_days_passed(last_session) < event.stage.SCHEDULE_ALERT_FREQUENCY_IN_DAYS):
        return None

    if event.progression.completed:
        return None

    logger.info("RESET STAGE %s" % event.stage.title)
    # Update date of last session
    if event.progression.number_of_day_sessions is None:
        event.progression.number_of_day_sessions = 0    
    event.progression.number_of_day_sessions += 1
    event.progression.date_last_day_session = arrow.utcnow()
    
    # Reset focused content every day....
    event.progression.focused_content_id = None

    # alerted flag (only for delegates):
    if event.request.has_delegate_permission(event.request.assembly.identifier):
        event.progression.alerted = True


# CONTENT SUBSRIBERS
@subscriber(EventContentRated)
def notified_after_a_content_has_been_rated(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is not transmitted"
    assert event.content, "content is not transmitted"
    assert event.progression, "progression is not transmitted"

    # event.progression.complete()
    event.progression.date_last_interaction = arrow.utcnow()
    if event.prior is None:
        if event.request.current_user.content_rating_count is None:
            event.request.current_user.content_rating_count = 0    
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
        if event.request.current_user.content_salience_count is None:
            event.request.current_user.content_salience_count = 0    
        event.request.current_user.content_salience_count += 1


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


@subscriber(EventContentRead)
def notified_after_a_content_has_been_read(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is not transmitted"
    assert event.progression, "progression is not transmitted"

    event.progression.set_read()     


@subscriber(EventContentCreated)
def notified_after_a_content_has_been_created(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is not transmitted"
    assert event.content, "content is not transmitted"
    assert event.progression, "progression is not transmitted"

    # event.progression.setUnalert()
    event.progression.date_last_interaction = arrow.utcnow()
    if event.request.current_user.content_created_count is None:
        event.request.current_user.content_created_count = 0    
    event.request.current_user.content_created_count += 1

    assert event.request.assembly.__progression__
    if event.request.assembly.__progression__.number_of_comments is None:
        event.request.assembly.__progression__.number_of_comments = 0    
    if event.request.assembly.__progression__.number_of_comments_today is None:
        event.request.assembly.__progression__.number_of_comments_today = 0    
    event.request.assembly.__progression__.number_of_comments += 1
    event.request.assembly.__progression__.number_of_comments_today += 1

    # add entry to monitor table
    elog = DBLog.create_from_json(
        user_id=event.request.local_userid,
        assembly_id=event.request.assembly.id,
        content_id=event.content.id,
        action=MONITOR_ACTION_CREATE_CONTENT,
        date_created=arrow.utcnow())
    event.request.dbsession.add(elog)

    # add notification
    if event.content.db_parent and event.content.db_parent.user_created_id != event.request.local_userid:
        initiate_notification(
            request=event.request,
            action=NOTIFICATION_ACTION_RESPONSE_TO_CONTENT,
            user_id=event.content.db_parent.user_created_id,
            assembly=event.request.assembly,
            content=event.content.db_parent,
            contenttree=event.content.contenttree,
            value=event.request.current_user.username)


@subscriber(EventContentDeleted)
def notified_after_a_content_has_been_deleted(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is not transmitted"
    assert event.content, "content is not transmitted"
    assert event.progression, "progression is not transmitted"
    
    # event.progression.setUnalert()
    event.progression.date_last_interaction = arrow.utcnow()
    event.request.current_user.content_created_count -= 1

    assert event.request.assembly.__progression__
    event.request.assembly.__progression__.number_of_comments -= 1
    event.request.assembly.__progression__.number_of_comments_today -= 1
    if event.request.assembly.__progression__.number_of_comments_today < 0:
        event.request.assembly.__progression__.number_of_comments_today = 0
    if event.request.assembly.__progression__.number_of_comments < 0:
        event.request.assembly.__progression__.number_of_comments = 0
        
    # add entry to monitor table
    elog = DBLog.create_from_json(
        user_id=event.request.local_userid,
        assembly_id=event.request.assembly.id,
        content_id=event.content.id,
        action=MONITOR_ACTION_DELETE_CONTENT,
        date_created=arrow.utcnow())
    event.request.dbsession.add(elog)

    # add notification
    if event.content.user_created_id != event.request.local_userid:
        initiate_notification(
            request=event.request,
            action=NOTIFICATION_ACTION_DELETE_CONTENT,
            user_id=event.content.user_created_id,
            assembly=event.request.assembly,
            content=event.content,
            contenttree=event.content.contenttree,
            value=event.content.title)
        # assert notification
        # event.response['notifications'] = {notification.id: notification}



@subscriber(EventContentEdited)
def notified_after_a_content_has_been_edited(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is not transmitted"
    assert event.content, "content is not transmitted"
    assert event.progression, "progression is not transmitted"
    

    # event.progression.setUnalert()
    event.progression.date_last_interaction = arrow.utcnow()
    # event.request.current_user.content_created_count += 1

    assert event.request.assembly.__progression__
    if event.request.assembly.__progression__.number_of_comments is None:
        event.request.assembly.__progression__.number_of_comments = 0    
    if event.request.assembly.__progression__.number_of_comments_today is None:
        event.request.assembly.__progression__.number_of_comments_today = 0    
    event.request.assembly.__progression__.number_of_comments += 1
    event.request.assembly.__progression__.number_of_comments_today += 1

    # add entry to monitor table
    elog = DBLog.create_from_json(
        user_id=event.request.local_userid,
        assembly_id=event.request.assembly.id,
        content_id=event.content.id,
        action=MONITOR_ACTION_EDIT_CONTENT,
        date_created=arrow.utcnow())
    event.request.dbsession.add(elog)

    # add notification
    if event.content.user_created_id != event.request.local_userid:
        initiate_notification(
            request=event.request,
            action=NOTIFICATION_ACTION_EDIT_CONTENT,
            user_id=event.content.user_created_id,
            assembly=event.request.assembly,
            content=event.content,
            contenttree=event.content.contenttree,
            value=event.content.title)
        # assert notification
        # event.response['notifications'] = {notification.id: notification}


@subscriber(EventContentMoved)
def notified_after_a_content_has_been_moved(event):

    # reorder of siblings if this is random-order content.
    assert event.request, "request is not transmitted"
    assert event.content, "content is not transmitted"
    assert event.progression, "progression is not transmitted"
    

    # event.progression.setUnalert()
    event.progression.date_last_interaction = arrow.utcnow()
    # event.request.current_user.content_created_count += 1

    # TODO: REmove this except (delete and create)
    assert event.request.assembly.__progression__
    if event.request.assembly.__progression__.number_of_comments is None:
        event.request.assembly.__progression__.number_of_comments = 0    
    if event.request.assembly.__progression__.number_of_comments_today is None:
        event.request.assembly.__progression__.number_of_comments_today = 0    
    event.request.assembly.__progression__.number_of_comments += 1
    event.request.assembly.__progression__.number_of_comments_today += 1

    # add entry to monitor table
    elog = DBLog.create_from_json(
        user_id=event.request.local_userid,
        assembly_id=event.request.assembly.id,
        content_id=event.content.id,
        action=MONITOR_ACTION_MOVE_CONTENT,
        date_created=arrow.utcnow())
    event.request.dbsession.add(elog)

    # add notification
    if event.content.user_created_id != event.request.local_userid:
        initiate_notification(
            request=event.request,
            action=NOTIFICATION_ACTION_MOVE_CONTENT,
            user_id=event.content.user_created_id,
            assembly=event.request.assembly,
            content=event.content,
            contenttree=event.content.contenttree,
            value=event.content.title)
        # assert notification
        # event.response['notifications'] = {notification.id: notification}


@subscriber(EventPeerReviewInitialized)
def notified_after_peerreview_init(event):

    # reorder of siblings if this is random-order content.
    assert event.content, "content is missing"
    assert event.response, "response is missing"
    assert event.request.assembly, "assembly is missing"

    if event.request.assembly.__progression__.number_of_proposals is None:
        event.request.assembly.__progression__.number_of_proposals = 0    
    if event.request.assembly.__progression__.number_of_proposals_today is None:
        event.request.assembly.__progression__.number_of_proposals_today = 0
    event.request.assembly.__progression__.number_of_proposals += 1
    event.request.assembly.__progression__.number_of_proposals_today += 1

    # add entry to monitor table
    elog = DBLog.create_from_json(
        user_id=event.request.local_userid,
        assembly_id=event.request.assembly.id,
        content_id=event.content.id,
        value=event.peerreview.id,
        action=MONITOR_ACTION_INIT_PEERREVIEW,
        date_created=arrow.utcnow())
    event.request.dbsession.add(elog)

    # add notification
    notification = initiate_notification(
        request=event.request,
        action=NOTIFICATION_ACTION_PEERREVIEW_INIT_INSERT if event.peerreview.operation == 'INSERT' else NOTIFICATION_ACTION_PEERREVIEW_INIT_UPDATE,
        user_id=event.request.local_userid,
        assembly=event.request.assembly,
        content=event.content,
        value=event.content.title,
        contenttree_id=event.peerreview.contenttree_id,
        peerreview=event.peerreview)

    assert notification
    if not event.response.get('notifications'):
        event.response['notifications'] = {}
    event.response['notifications'][notification.id] = notification


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

    # add notification
    initiate_notification(
        request=event.request,
        action=NOTIFICATION_ACTION_PEERREVIEW_APPROVED,
        user_id=event.peerreview.user_created_id,
        assembly=event.request.assembly,
        content=event.content,
        value=event.content.title,
        contenttree_id=event.content.contenttree_id,    
        peerreview=event.peerreview)


@subscriber(EventPeerReviewRejected)
def notified_after_rejected_peerreview(event):

    # reorder of siblings if this is random-order content.
    assert event.content, "content is missing"
    # assert event.request.contenttree, "contenttree is missing"

    # add notification
    initiate_notification(
        request=event.request,
        action=NOTIFICATION_ACTION_PEERREVIEW_REJECTED,
        user_id=event.peerreview.user_created_id,
        assembly=event.request.assembly,
        content=event.content,
        value=event.content.title,
        contenttree_id=event.content.contenttree_id,
        peerreview=event.peerreview)
