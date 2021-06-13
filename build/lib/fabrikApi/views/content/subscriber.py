import arrow
from pyramid.events import subscriber
from fabrikApi.util.events import EventContentCreated, EventContentRated, EventContentSalienced, \
    EventFirstContentVisit, EventContentVisit


@subscriber(EventContentRated)
def notified_after_a_content_has_been_rated(event):

    # reorder of siblings if this is random-order content.
    assert event.request
    assert event.content
    assert event.progression

    # event.progression.complete()
    event.progression.date_last_interaction = arrow.utcnow()
    if event.prior is None:
        event.request.current_user.content_rating_count += 1


@subscriber(EventContentSalienced)
def notified_after_a_content_has_been_salienced(event):

    # reorder of siblings if this is random-order content.
    assert event.request
    assert event.content
    assert event.progression

    # event.progression.setUnalert()
    event.progression.date_last_interaction = arrow.utcnow()
    if event.prior is None:
        event.request.current_user.content_salience_count += 1
    

@subscriber(EventContentCreated)
def notified_after_a_content_has_been_created(event):

    # reorder of siblings if this is random-order content.
    assert event.request
    assert event.content
    assert event.progression

    # event.progression.setUnalert()
    event.progression.date_last_interaction = arrow.utcnow()
    event.request.current_user.content_created_count += 1


@subscriber(EventContentVisit, EventFirstContentVisit)
def notified_after_a_content_has_been_entered(event):

    # reorder of siblings if this is random-order content.
    assert event.request
    assert event.content
    assert event.progression

    # patched required.
    assert event.content.patched
    
    # ITs time to reschedule the content!
    # Put on schedule every new date!!!
    event.progression.date_last_interaction = arrow.utcnow()
