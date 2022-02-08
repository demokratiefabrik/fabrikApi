#!/usr/bin/env python
"""
Compose a CIR_VOICE section.
"""

__all__ = ['patch', __doc__]


def patch(target):
    """ These methods are appended to DBStages with type VOICE"""

    target.DEFAULT_ICON = 'mdi-frequently-asked-questions'

    pass
