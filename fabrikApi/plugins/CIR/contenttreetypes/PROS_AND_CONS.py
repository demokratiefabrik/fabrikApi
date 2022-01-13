#!/usr/bin/env python
"""
Juxtaposing Pros and Cons Argument, and allowing for asynch. discussions.
"""

__all__ = ['patch', __doc__]


def patch(target):
    """ These methods are appended to DBContentTrees with type PROS_AND_CONS.
    # see __init__.py for detailed explanation.

    """

    target.CONTENTTYPES = ['COMMENT', 'CONTRA', 'PRO', 'QUESTION', 'ANSWER']
    # target.DEFAULT_ICON = 'mdi-plus-minus-box-outline'
    # target.DEFAULT_CONTENT_TYPE = 'COMMENT'

    """ Define hierarchical Relations: What children types are allowed? Who are alloed to add, rate, modify,  them?  """
    target.ONTOLOGY = {
        None: ['PRO', 'CONTRA'],
        'COMMENT': ['COMMENT', 'QUESTION'],
        'PRO': ['COMMENT', 'QUESTION'],
        'CONTRA': ['COMMENT', 'QUESTION'],
        'QUESTION': ['COMMENT', 'ANSWER'],
        'ANSWER': ['COMMENT', 'QUESTION']
        }

    # Add a random number for assinging pros/cons on left resp. right side...
    # def constant_random_number(db_contenttree, request):
    #     """ Returns a user-constant random number: either 0 or 1"""

    #     multiplier_id = db_contenttree.id if db_contenttree.id is not None else 345
    #     user_seed = request.local_userid
    #     if not user_seed:
    #         user_seed = int(ipaddress.IPv4Address(request.remote_addr))
    #     random.seed(1034 * user_seed * multiplier_id)
    #     population = [0, 1]
    #     return(random.choice(population))

    # target.CUSTOM_DATA = {'RANDOM_LEFTRIGHT_ASSIGNMENT': constant_random_number}
