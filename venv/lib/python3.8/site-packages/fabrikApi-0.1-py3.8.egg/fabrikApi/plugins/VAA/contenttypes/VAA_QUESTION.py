#!/usr/bin/env python
"""
A VAA-Question Item. Core Element Of VAA-Questionnaire.
"""

__all__ = ['patch', '__doc__']


# from pyramid.security import Deny
import types

from pyramid.security import Deny, Everyone

def patch(target):
    """ These methods are appended to DBContent with type <modulename>"""

    # PROPERTY OWNERSHIP
    target.COMMON_PROPERTY_CONTENT = True
    target.GIVEN_PROPERTY_CONTENT = False
    target.PRIVATE_PROPERTY_CONTENT = False

    def get_approving_conditions(self, peerreview):
        """ What is peerreview criteria are to apply for this specific operation.
        This method returns the default values. The method can be overwritten by methods
        within the specific content type extensions.

        # examples of criteria:
        - peerreview: e.g. operation type.... (modify vs. delete)
        - content: e.g. nof_mofications... (new entries vs. very old and multiple times confiremd entries..)
        - highly popular vs. unpopular entries.???
        """

        assert peerreview, "empty peerreview"
        assert target.COMMON_PROPERTY_CONTENT

        quorum = 2  # at least 3 respondents
        rate = 50  # at least 50% approvals

        return(quorum, rate)

    target.get_approving_conditions = types.MethodType(get_approving_conditions, target)

    # target.CUSTOMIZED_ACLS = [
    #     (Deny, Everyone, ['rating']),
    # ]

    pass
