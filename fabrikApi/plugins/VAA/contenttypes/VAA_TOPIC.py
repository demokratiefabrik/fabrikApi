#!/usr/bin/env python
"""
A VAA-Question Item. Core Element Of VAA-Questionnaire.
"""

__all__ = ['patch', '__doc__']


# from pyramid.security import Deny


def patch(target):
    """ These methods are appended to DBContent with type <modulename>"""

    # target.RATING_RANGE = range(-50, 51)  # Note: upper limit not included
    
    # PROPERTY OWNERSHIP
    target.COMMON_PROPERTY_CONTENT = False
    target.GIVEN_PROPERTY_CONTENT = True
    target.PRIVATE_PROPERTY_CONTENT = False

    # target.CUSTOMIZED_ACLS = [
    #     (Deny, 'contributor@' + target.__assembly_identifier__, ['adding']),
    #     (Deny, 'delegate@' + target.__assembly_identifier__, ['rating']),
    #     (Deny, 'expert@' + target.__assembly_identifier__, ['rating'])
    # ]

    pass
