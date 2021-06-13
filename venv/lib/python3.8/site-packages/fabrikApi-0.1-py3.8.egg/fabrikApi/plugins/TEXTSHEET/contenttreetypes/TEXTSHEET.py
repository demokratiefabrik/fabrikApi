#!/usr/bin/env python
"""
Compose a Textsheet structured by sections, subsections, paragraphs images, questions and answers.
"""

__all__ = ['patch', __doc__]


def patch(target):
    """ These methods are appended to DBContentTrees with type TEXTSHEET"""

    target.CONTENTTYPES = ['SECTION', 'SUBSECTION', 'PARAGRAPH', 'COMMENT', 'FOLDER']

    """ DEFINE Hierarchical Relations: What children types are allowed?  """
    target.ONTOLOGY = {
        None: ['SECTION',],
        'COMMENT': ['COMMENT', 'FOLDER'],
        'SECTION': ['COMMENT', 'FOLDER', 'SUBSECTION', 'PARAGRAPH', ],
        'SUBSECTION': ['COMMENT', 'FOLDER', 'PARAGRAPH'],
        'PARAGRAPH': ['COMMENT', 'FOLDER', 'PARAGRAPH'],
        'FOLDER': ['COMMENT','FOLDER']
        }

    # specify the content types that are priate property (can only be edited by owners)
    # given property (only managers can add and modify)
    # and common property (subject to peer review)
    target.PRIVATE_PROPERTY_CONTENT = ['COMMENT']
    target.GIVEN_PROPERTY_CONTENT = ['FOLDER']