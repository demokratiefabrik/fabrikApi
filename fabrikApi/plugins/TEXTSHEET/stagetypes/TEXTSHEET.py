#!/usr/bin/env python
"""
Compose a Textsheet structured by sections, subsections, paragraphs images, questions and answers.
"""

__all__ = ['patch', __doc__]


def patch(target):
    """ These methods are appended to DBStages with type TEXTSHEET"""

    target.DEFAULT_ICON = 'mdi-newspaper-variant-outline'
    # target.DEFAULT_CONTENT_TYPE = 'PARAGRAPH'

    # 99 days the stage is sete to alert... (participants need to check the stage)
    target.SCHEDULE_ALERT_FREQUENCY_IN_DAYS = 99

    pass
