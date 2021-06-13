#!/usr/bin/env python
"""
Questions: Asks for further explanations regarding its parent. (common property)
"""

__all__ = ['patch', '__doc__']


def patch(target):
    """ These methods are appended to DBContent with type <modulename>"""

    # it comes in fixed order: column: <order_position>
    target.is_in_random_order = True

    # PROPERTY OWNERSHIP
    target.COMMON_PROPERTY_CONTENT = False
    target.GIVEN_PROPERTY_CONTENT = True
    target.PRIVATE_PROPERTY_CONTENT = False
    
    pass
