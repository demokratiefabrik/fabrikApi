#!/usr/bin/env python
"""
User-generated and rather unspecified content (private property).
"""


__all__ = ['patch', '__doc__']


def patch(target):
    """ These methods are appended to DBContent with type <modulename>"""
    
    # does the content belongs to the collective (and not to the creater?)
    # target.common_property = False
    
    # target.DEFAULT_CONTENT_TYPE = 'COMMENT'

    pass
