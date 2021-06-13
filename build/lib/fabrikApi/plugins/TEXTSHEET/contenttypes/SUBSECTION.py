#!/usr/bin/env python
"""
Sub-SECTION featuring the header and a short description of the subsection.
"""

__all__ = ['patch', '__doc__']


def patch(target):
    """ These methods are appended to DBContent with type <modulename>"""
    
    # does the content belongs to the collective (and not to the creater?)
    # target.common_property = False

    # it comes in fixed order: column: <order_position>
    target.is_in_random_order = False

    # PROPERTY OWNERSHIP
    target.COMMON_PROPERTY_CONTENT = False
    target.GIVEN_PROPERTY_CONTENT = True
    target.PRIVATE_PROPERTY_CONTENT = False

    pass
