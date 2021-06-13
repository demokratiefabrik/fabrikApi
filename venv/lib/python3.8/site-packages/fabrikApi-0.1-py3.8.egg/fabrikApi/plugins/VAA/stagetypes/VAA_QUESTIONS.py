#!/usr/bin/env python
"""
Compose a VAA_QUESTIONS section.
"""

__all__ = ['patch', __doc__]


def patch(target):
    """ These methods are appended to DBStages with type VAA_QUESTIONS"""

    target.DEFAULT_ICON = 'mdi-frequently-asked-questions'

    pass
