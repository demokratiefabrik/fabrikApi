# -*- coding: utf-8 -*-
"""
Library for custom events for fabrikApi assembly
"""

import logging

logger = logging.getLogger(__name__)


__all__ = [ "EventFirstPlatformVisit", "EventFirstAssemblyVisit", "EventAssemblyVisit", 
            "EventFirstStageVisit", "EventStageVisit", "EventFirstContentTreeVisit", 
            "EventContentTreeVisit"]


class EventFirstPlatformVisit(object):
    """ Event is raised when participant logs in for the first time.
    """

    request = None
    
    def __init__(self, request, **kwargs):
        logger.info("FIRST TIME VISIT TO THIS PLATTFORM")

        self.request = request


# ASSEMBLY EVENTS
#################################
class EventFirstAssemblyVisit(object):
    """
    Event is raised when user initialize an assembly procession.
    (only for first time participants)
    """

    request = None
    assembly = None
    progression = None

    def __init__(self, request, assembly, progression=None, **kwargs):
        logger.info("FIRST TIME ATEENDANCE: %s " % assembly.id)

        self.request = request
        self.progression = progression
        self.assembly = assembly


class EventAssemblyVisit(object):
    """
    Event is raised when user continues to visit an assembly.
    """

    # request = None
    # assembly = None
    # progression = None

    def __init__(self, request, assembly, progression=None, **kwargs):
        logger.info("ASSEMBLY ATEENDANCE: %s " % assembly.id)

        self.request = request
        self.progression = progression
        self.assembly = assembly


# STAGE EVENTS
#################################
class EventFirstStageVisit(object):
    """
    Event is raised when user enters a stage for the first time.
    """

    # request = None
    # stage = None
    # progression = None

    def __init__(self, request, stage, progression=None, **kwargs):
        logger.info("STAGE: FIRST TIME ATEENDANCE: %s " % stage.id)

        self.request = request
        self.progression = progression
        self.stage = stage


class EventStageVisit(object):
    """
    Event is raised when user continues to visit a Stage.
    """

    # request = None
    # stage = None
    # progression = None

    def __init__(self, request, stage, progression=None, **kwargs):
        logger.info("STAGE: ATEENDANCE: %s " % stage.id)

        self.request = request
        self.progression = progression
        self.stage = stage


class EventStageCompleted(object):
    """
    Event is raised when user completes a certain stage.
    """

    def __init__(self, request, stage, progression=None, **kwargs):
        self.request = request
        self.stage = stage
        self.progression = progression

        logger.info("STAGE: Completed: %s " % stage.id)


class EventStageUnalert(object):
    """
    Event is raised when user has visited a certain stage and abolved essential tasks
    """

    def __init__(self, request, stage, progression=None, **kwargs):
        self.request = request
        self.stage = stage
        self.progression = progression

        logger.info("STAGE: Unalerting: %s " % stage.id)


class EventStageFocusContent(object):
    """
    Event is raised when user has visited a certain stage and abolved essential tasks
    """

    def __init__(self, request, content, stage, progression, **kwargs):
        self.request = request
        self.content = content
        self.stage = stage
        self.progression = progression

        logger.info("STAGE: Set focused content of this stage...: %s " % content.id)


# CONTENT EVENTS
#################################
class EventFirstContentVisit(object):
    """
    Event is raised when user enters a content for the first time.
    """

    # request = None
    # content = None
    # progression = None

    def __init__(self, request, content, progression=None, **kwargs):
        logger.info("CONTENT: FIRST TIME ATEENDANCE: %s " % content.id)

        self.request = request
        self.progression = progression
        self.content = content


class EventContentVisit(object):
    """
    Event is raised when user continues to visit a Content.
    """

    # request = None
    # content = None
    # progression = None

    def __init__(self, request, content=None, progression=None, **kwargs):
        logger.info("CONTENT: ATEENDANCE")

        self.request = request
        self.progression = progression
        self.content = content


class EventContentSalienced(object):
    """
    Event is raised when user indicates salience of a content.
    """

    def __init__(self, request, content, progression=None, prior=None, **kwargs):
        self.request = request
        self.content = content
        self.progression = progression
        self.prior = prior

        logger.info("CONTENT: Completed: %s " % content.id)


class EventContentRated(object):
    """
    Event is raised when user rates a content
    """

    def __init__(self, request, content, progression=None, prior=None, **kwargs):
        self.request = request
        self.content = content
        self.prior = prior
        self.progression = progression

        logger.info("CONTENT: Rated: %s " % content.id)


class EventContentRead(object):
    """
    Event is raised when user rates a content
    """

    def __init__(self, request, content, progression=None, **kwargs):
        self.request = request
        self.content = content
        self.progression = progression

        logger.info("CONTENT: Read: %s " % content.id)


class EventSetContentAsDiscussed(object):
    """
    Event is raised when user rates a content
    """

    def __init__(self, request, content, progression=None, topic_progression=None, **kwargs):
        self.request = request
        self.content = content
        self.topic_progression = topic_progression
        self.progression = progression

        logger.info("CONTENT: SET AS DISCUSSED: %s" % (content.id))


# class EventContentDiscussed(object):
#     """
#     Event is raised when user has discssued (intensifly engaged with) a content
#     """

#     def __init__(self, request, content, progression=None, **kwargs):
#         self.request = request
#         self.content = content
#         self.progression = progression

#         logger.info("CONTENT: Discussed: %s " % content.id)


class EventContentCreated(object):
    """
    Event is raised when user created a new content.
    """

    def __init__(self, request, content, progression=None, **kwargs):
        self.request = request
        self.content = content
        self.progression = progression

        logger.info("CONTENT: Created: %s " % content.id)


class EventContentInteract(object):
    """
    Event is raised when user interacted with a new content.
    """

    def __init__(self, request, content, progression=None, **kwargs):
        self.request = request
        self.content = content
        self.progression = progression

        logger.info("CONTENT: Interacted: %s " % content.id)


# CONTENT TREE EVENTS
#################################

class EventFirstContentTreeVisit(object):
    """
    Event is raised when user loads a contenttree for the first time.
    """

    # request = None
    # progression = None

    def __init__(self, request, progression=None, **kwargs):
        logger.info("CONTENTTREE: FIRST TIME ATEENDANCE: %s " % progression.id)

        self.request = request
        self.progression = progression

class EventContentTreeVisit(object):
    """
    Event is raised when user loads a ContentTree.
    """

    request = None
    progression = None


    def __init__(self, request, progression=None, **kwargs):
        logger.info("CONTENTTREE: FIRST ATEENDANCE: %s " % progression.id)

        self.request = request
        self.progression = progression





# PEER REVIEW EVENTS
#################################
class EventPeerReviewInitialized(object):
    """
    Event is raised when a user initizalized a new peer review
    e.g. when altering, deleting, or creating common property content.

    """
    
    request = None
    content = None
    peerreview = None

    def __init__(self, request, content, peerreview):
        logger.info("Peer Review Initialized: %s:  %s" % (content, peerreview))

        self.request = request
        self.content = content
        self.peerreview = peerreview


class EventPeerReviewApproved(object):
    """
    Event is raised when a content modification has been approved
    """

    request = None
    content = None
    peerreview = None

    def __init__(self, request, content, peerreview):
        self.request = request
        self.content = content
        self.peerreview = peerreview
        logger.info("Peer Review Successfull / Approved: %s:  %s" % (content, peerreview))


class EventPeerReviewRejected(object):
    """
    Event is raised when a content modification has been rejected
    """
    request = None
    content = None
    peerreview = None

    def __init__(self, request, content, peerreview):
        logger.info("Peer Review Unsucessfull / Rejected: %s:  %s" % (content, peerreview))

        self.request = request
        self.content = content
        self.peerreview = peerreview


class EventFirstPeerReviewVisit(object):
    """
    Event is raised when user enters a peerreview for the first time.
    """

    # request = None
    # content = None
    # progression = None

    def __init__(self, request, content_peerreview, progression=None, **kwargs):
        logger.info("PEERREVIEW: FIRST TIME ATEENDANCE: %s " % content_peerreview.id)

        self.request = request
        self.progression = progression
        self.content_peerreview = content_peerreview


class EventPeerReviewVisit(object):
    """
    Event is raised when user continues to visit a Peerreview.
    """

    # request = None
    # content = None
    # progression = None

    def __init__(self, request, content_peerreview, progression=None, **kwargs):
        logger.info("CONTENT: ATEENDANCE: %s " % content_peerreview.id)

        self.request = request
        self.progression = progression
        self.content_peerreview = content_peerreview


# class EventPeerReviewResubmit(object):
#     """
#     Event is raised when a resubmit is offered for a content modification
#     """

#     request = None
#     content = None
#     peerreview = None

#     def __init__(self, request, content, peerreview):
#         logger.info("Peer Review Offered Resubmit: %s:  %s" % (content, peerreview))

#         self.request = request
#         self.content = content
#         self.peerreview = peerreview
