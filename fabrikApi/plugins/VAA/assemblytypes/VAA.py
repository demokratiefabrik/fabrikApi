#!/usr/bin/env python
"""
Assembly to compose a VAA.
"""

__all__ = ['patch', __doc__]


def patch(target):
    """ These methods/property are appended to DBAssembly with type VAA """

    target.MAX_DAILY_USER_COMMENTS = 7
    target.MAX_DAILY_USER_PROPOSALS = 3
    target.MAX_OVERALL_USER_PROPOSALS = 15

    # When following overall threshold is reached, the daily limit is set to 1.
    target.TROTTLE_THRESHOLD_FOR_OVERALL_USER_PROPOSALS = 10

    pass
