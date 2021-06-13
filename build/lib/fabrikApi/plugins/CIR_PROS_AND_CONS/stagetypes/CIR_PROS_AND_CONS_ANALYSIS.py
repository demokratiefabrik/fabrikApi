#!/usr/bin/env python
"""
Juxtaposing CIR-Pros and Cons Analysis, and allowing for asynch. discussions.
"""
import random
import ipaddress


__all__ = ['patch', __doc__]


def patch(target):
    """ These methods are appended to DBStages with type PROS_AND_CONS.
    # see __init__.py for detailed explanation.

    """

    target.DEFAULT_ICON = 'mdi-plus-minus-box-outline'
    # target.DEFAULT_CONTENT_TYPE = 'COMMENT'

    # Add a random number for assinging pros/cons on left resp. right side...
    def constant_random_number(db_stage, request):
        """ Returns a user-constant random number: either 0 or 1"""

        # user_seed = request.local_userid
        # if not user_seed:
        #     user_seed = int(ipaddress.IPv4Address(request.remote_addr))
        contenttree_seed = db_stage.contenttree_id if db_stage.contenttree_id is not None else 345
        user_seed = request.get_user_specific_random_seed()
        random.seed(1034 * user_seed * contenttree_seed)
        population = [0, 1]
        
        return(random.choice(population))

    target.CUSTOM_DATA = {'RANDOM_LEFTRIGHT_ASSIGNMENT': constant_random_number}
