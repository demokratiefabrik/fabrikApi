#!/usr/bin/env python
"""
Compose a Textsheet structured by sections, subsections, paragraphs images, questions and answers.
"""
import logging

logger = logging.getLogger(__name__)

__all__ = ['patch', __doc__]


def patch(target):
    """ These methods are appended to DBStages with type TEXTSHEET"""

    target.DEFAULT_ICON = 'mdi-newspaper-variant-outline'
    # target.DEFAULT_CONTENT_TYPE = 'PARAGRAPH'

    # Shall the Stage be a one-timer?
    # True: The stage is set as completed, as soon it has been unalerted once.
    # False: The stage stays accessible forever.
    target.ONE_TIME_STAGE = True

    pass
