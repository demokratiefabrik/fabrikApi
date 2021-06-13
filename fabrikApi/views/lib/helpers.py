def remove_unvalidated_fields(jsoncontent, schema):
    # only use attributes that are specified in both, in jsoncontent data as well as in the schema
    attributes_in_both = schema.get('properties').keys() & jsoncontent.keys()
    jsoncontent = {ykey: jsoncontent[ykey] for ykey in attributes_in_both}
    return(jsoncontent)


def get_branches_to_reorder(request, uptodate_parent, uptodate_type, uptodate_order_position):
    # TODO: not sure if used!!
    """ reorder order_position: Do we have to reorder childs in some branches.
    # (only at content types with fixed position_order)
    # when parent_id changes: it may return both, the old and the new parent_id.
    # in all other cases it may return only the current parent_id.
    """

    modified_type = request.content and uptodate_type != request.content.type_
    modified_parent = request.content and uptodate_parent != request.content.db_parent
    modified_orderposition = request.content and uptodate_order_position != request.content.order_position

    branches_to_reorder = []

    # Do we have to reorder the actual branch?
    if (modified_parent and uptodate_order_position is not None) or modified_type or modified_orderposition:
        # reorder request.content.db_parent branch
        branches_to_reorder.append[uptodate_parent]

    # DO we have to update the older branch?
    if modified_parent:
        # then, reorder new and old content
        branches_to_reorder.append[request.content.parent_id]

    return (branches_to_reorder)
