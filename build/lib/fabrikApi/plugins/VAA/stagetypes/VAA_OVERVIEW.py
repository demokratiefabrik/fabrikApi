#!/usr/bin/env python
"""
Compose a VAA_OVERVIEW section.
"""

__all__ = ['patch', __doc__]


def patch(target):
    """ These methods are appended to DBStages with type FAQ"""

    target.DEFAULT_ICON = 'mdi-frequently-asked-questions'

    pass
