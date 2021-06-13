#!/usr/bin/env python
"""
Compose a VAA-QUESTIONNAIRE.
"""

__all__ = ['patch', __doc__]


def patch(target):
    """ These methods are appended to DBContentTrees with type FAQ"""

    target.CONTENTTYPES = ['COMMENT', 'FOLDER', 'VAA_TOPIC', 'VAA_QUESTION']

    """ DEFINE Hierarchical Relations: What children types are allowed?  """
    target.ONTOLOGY = {
        None: ['VAA_TOPIC',],
        'COMMENT': ['COMMENT', 'FOLDER'],
        'VAA_QUESTION': ['COMMENT', 'FOLDER', 'UPDATEPROPOSAL'],
        'VAA_TOPIC': ['VAA_QUESTION', 'COMMENT', 'FOLDER'],
        'FOLDER': ['COMMENT', 'FOLDER'],
        'UPDATEPROPOSAL': ['COMMENT', 'FOLDER']
        }

    # specify the content types that are priate property (can only be edited by owners)
    # all other content is common property and subject to peer review
    target.PRIVATE_PROPERTY_CONTENT = ['COMMENT']
    target.COMMON_PROPERTY_CONTENT = ['VAA_QUESTION']
    target.GIVEN_PROPERTY_CONTENT = ['VAA_TOPIC', 'FOLDER', 'UPDATEPROPOSAL']

    # Custom title length
    target.CONTENT_TITLE_MAX_LENGTH_BY_TYPES.update({
        'VAA_QUESTION': 300,
    })
