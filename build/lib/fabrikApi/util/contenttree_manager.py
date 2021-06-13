# -*- coding: utf-8 -*-

import logging
import time
# from datetime import datetime
# from functools import reduce
from collections import namedtuple

from sqlalchemy import and_
from sqlalchemy_filters.filters import apply_filters

from fabrikApi.models import DBContent, DBContentProgression
from fabrikApi.models.mixins import arrow
from fabrikApi.models.user import DBUser

logger = logging.getLogger(__name__)


class ContentTreeManager(object):

    """
    Store, verify, correct and manage the content tree and related contenttree
    data (This class works also as cache to save SQL resource)

    """
    user = None
    request = None
    contenttree = None
    contenttree_progression = None
    contents = None

    def __init__(self, request, contenttree=None):
        assert request is not None, "empty request...."

        self.request = request
        if contenttree:
            self.contenttree = contenttree
        self.load_user_data = not request.has_administrate_permission

    def load_toppic_contents(self, contenttree_id, ignoring_list=[]):
        """ Query all root content entries within one contentree"""

        # Check indices
        filter_spec = [
            {'model': 'DBContent', 'field': 'contenttree_id', 'op': '==',
             'value': contenttree_id},
            {'model': 'DBContent', 'field': 'id', 'op': 'not_in', 'value': ignoring_list},
            {'model': 'DBContent', 'field': 'parent_id', 'op': '==', 'value': None},
            {'model': 'DBContent', 'field': 'deleted', 'op': '==', 'value': False},
            {'model': 'DBContent', 'field': 'disabled', 'op': '==', 'value': False}
        ]

        # Load Contents: Which contents shall be loaded:
        query = self.request.dbsession.query(DBContent)
        query = apply_filters(query, filter_spec)
        contents = query.all()
        
        # Prepare Object for Json Response
        for content in contents:
            # PERMISSION and lineage Setup
            content.setup_lineage(self.request)
            self.request.has_permission('observe', content)

        return contents

    def load_content(self):
        """ get contenttree.."""

        assert self.request, "empty request...."
        assert self.contenttree, "empty contenttree...."

        logger.debug("load contenttree (nested contents)")

        # proper Setup? Assert SQL indicies
        name = "ix_contenttreeid_deleted_disabled_parentid_orderposition"
        assert name in list(map(lambda x: x.name, DBContent.__table_args__)), "invalid DBIndex name. => not prepared, right?"
        # name = "ix_contentprogression_contentid_userid_modifieddate"
        # assert name in list(map(lambda x: x.name, DBContentProgression.__table_args__))

        # # Load Contents: Which contents shall be loaded:
        start_time = time.time()

        content_tuples = self._load_content_tuples()

        # NESTED STRUCTURE
        self._setup_nested_structure(content_tuples)
        end_time = time.time()
        logger.debug("...loading time for nested tree {}".format(end_time-start_time))

        return ({
            'id': self.contenttree.id,
            # 'date_last_tree_modification': self.contenttree.date_last_tree_modification,
            'rootElementIds': self.contenttree.rootElementIds,
            'entries': content_tuples,
            'acl': self.request.get_auth_roles(context=self.contenttree),
            'access_date': arrow.utcnow(),
            'update_date': arrow.utcnow(),
            'access_sub': self.request.authenticated_userid})

    def load_modified_content(self, modificationDate):
        """ get contenttree.."""

        assert self.request, "Invalid request"
        assert self.contenttree, "invalid contenttree"

        logger.debug("load contenttree (modified contents)")

        return self._load_content_tuples(withOrder=False, modificationDate=modificationDate)

    def _load_content_tuples(self, withOrder=True, modificationDate=None):
        """ Query data from the DB and return list of {content, progression} tuples """

        # Check indices
        filter_spec = [
            {'model': 'DBContent', 'field': 'contenttree_id', 'op': '==',
             'value': self.contenttree.id},
            {'model': 'DBContent', 'field': 'deleted', 'op': '==', 'value': False},
            {'model': 'DBContent', 'field': 'disabled', 'op': '==', 'value': False}
        ]
        
        if modificationDate:
            filter_spec.append(
                {'model': 'DBContent', 'field': 'date_modified', 'op': '>=', 'value': modificationDate}
            )

        # Load Contents: Which contents shall be loaded:
        if self.load_user_data:
            # TODO: only for delgagates and contributors.
            query = self.request.dbsession.query(DBContent, DBContentProgression)
        else:
            query = self.request.dbsession.query(DBContent)
        query = apply_filters(query, filter_spec)

        # load also progression data:
        if self.load_user_data:
            query = query.outerjoin(
                DBContentProgression,
                and_(
                    DBContent.id == DBContentProgression.content_id,
                    DBContentProgression.user_id == self.request.local_userid
                )
            )

        # Order contents
        if withOrder:
            # Note: parent_id ordering is done because of the nested_tree-composition method used later.
            query = query.order_by(DBContent.parent_id, DBContent.order_position)
        contents = query.all()

        # Managers
        if not self.load_user_data:
            ContentTuple = namedtuple('ContentTuple', 'DBContent DBContentProgression')
            contents = list(map(
                lambda content: ContentTuple(DBContent=content, DBContentProgression=None),
                contents))


        # Load Usernames!
        creator_ids = {v.DBContent.user_created_id: True for k, v in enumerate(contents)}
        usernames = self.request.dbsession.query(DBUser.id, DBUser).filter(DBUser.id.in_(creator_ids)).all()
        creator_usernames = {k: v for k, v in usernames}
        
        # Prepare Object for Json Response
        for content in contents:
            # PERMISSION and lineage Setup
            content.DBContent.setup_lineage(self.request)
            content.DBContent.patch()

        # PERMISSION Check
        contents = list(filter(lambda content: self.request.has_permission('observe', content.DBContent), contents))

        # Re-Arrange
        content_tuples = {  
            k.DBContent.id: {
                'content': k.DBContent,
                'path': None,
                'progression': k.DBContentProgression,
                'creator': creator_usernames[k.DBContent.user_created_id]}\
            for v, k in enumerate(contents)
        }

        return content_tuples

    # contenttree_structure_nested
    def _setup_nested_structure(self, content_tuples):

        # prepare needed variables
        self.contenttree._rootElementIds = []
        # base_random_seed = self.request.get_user_specific_random_seed() + self.contenttree.id

        # performance shortcuts:
        all_content_ids = []
        append_to_all_content_ids = all_content_ids.append
        append_to_rootChildren = self.contenttree._rootElementIds.append

        # seed = random.seed

        # Loop through tree by levels (starting at top level).
        level = 1
        same_level_items = list(filter(lambda x: x['content'].parent_id is None, content_tuples.values()))
        previous_parent_id = None
        while len(same_level_items) > 0:

            # set new level/branches for all objects on the same level
            new_ids = []
            append_ids = new_ids.append

            # loop through entries on the given level
            for content_tuple in same_level_items:
                content = content_tuple['content']
                content_id = content.id
                content.setup_lineage(self.request)
                append_ids(content_id)
                append_to_all_content_ids(content_id)

                # Parent-Child Relationship
                content_parent_id = content.parent_id
                # is_in_random_order = content.is_in_random_order

                if not content_parent_id:
                    # ROOT ELEMENTS
                    content._path = [content_id]
                    append_to_rootChildren(content_id)
                    # if is_in_random_order:
                    #   seed(base_random_seed)

                else:

                    # CHILD ELEMENTS
                    # Performance: cache parent objects
                    if previous_parent_id != content_parent_id:
                        previous_parent_id = content_parent_id
                        content_parent = content_tuples[content_parent_id]['content']
                        content_parent_path = content_parent._path
                        # if is_in_random_order:
                        #     seed(base_random_seed * content_parent_id)

                    # Update this PATH
                    content._path = content_parent_path + [content_id]

                    # if is_in_random_order:
                    #     content_tuple['progression']._random_order_position = 
                content_tuple['path'] = content.path
                
            # load contents on next level...
            level += 1
            same_level_items = list(
                filter(lambda content_tuple: content_tuple['content'].parent_id in new_ids,
                       content_tuples.values()))

        # remove not structured content
        allkeys = set(content_tuples.keys())
        if len(all_content_ids) < len(allkeys):
            keys_to_remove = [value for value in allkeys if value not in all_content_ids]
            for k in keys_to_remove:
                content_tuples.pop(k, None)
