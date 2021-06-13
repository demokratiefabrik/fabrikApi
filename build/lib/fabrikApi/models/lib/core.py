from  sqlalchemy.sql.expression import func
import random
import string

from sqlalchemy.sql.operators import is_

from fabrikApi.models.username_templates import DBUsernameTemplates
from fabrikApi.models.user import DBUser


def get_or_create_progression(request, model, auto_create=True, event_when_creating_entry=None,
                              event_when_reusing_entry=None, is_manager=None, **kwargs):
    """ Creates a new DB entry, if an entry with ***kwargs does not exists."""
    assert request.assembly, "please indicate first request.assembly attribute..."
    progression = request.dbsession.query(model).filter_by(**kwargs).first()
    if progression:
        if event_when_reusing_entry:
            event = event_when_reusing_entry(request=request, progression=progression, **kwargs)
            request.registry.notify(event)
        return progression
    elif auto_create:
        is_manager = request.has_manage_permission(request.assembly.identifier)
        progression = model(**kwargs)
        progression.by_manager = is_manager
        request.dbsession.add(progression)
        request.dbsession.flush()
        if event_when_creating_entry:
            event = event_when_creating_entry(request=request, progression=progression, **kwargs)
            request.registry.notify(event)
        return progression


def get_random_color():
    """ Generates a random Hex color with a minimum level of preceived brightness
    see https://stackoverflow.com/questions/12043187/how-to-check-if-hex-color-is-too-black
    """

    maxThreshold = 220
    minThreshold = 30
    luma = 0
    while luma >= maxThreshold or luma <= minThreshold:
        # random value weithed by specic brightness values
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        luma = 0.2126 * r + 0.7152 * g + 0.0722 * b # // per ITU-R BT.709

    return ('#%02x%02x%02x' % (r, g, b))


def get_or_create_user(request, auto_create=True, event_when_creating_entry=None,
                              event_when_reusing_entry=None, **kwargs):
    """ Creates a new DB entry, if an entry with ***kwargs does not exists."""
    user = request.dbsession.query(DBUser).filter_by(**kwargs).first()
    if user:
        if event_when_reusing_entry:
            event = event_when_reusing_entry(request=request, **kwargs)
            request.registry.notify(event)
        return user
    elif auto_create:

        # Get RANDOM COLOR
        color = get_random_color()
        # Get Random User
        template = request.dbsession.query(DBUsernameTemplates).order_by(func.rand()).first() # for MySQL
        # Get Random initial Letter (firstname)
        letter = random.choice(string.ascii_uppercase)
        username = "%s. %s" % (letter, template.username)
        custom = template.custom_data
        custom['COLOR'] = color
        
        user = DBUser(**kwargs)
        user.custom_data = custom
        user.username = username
        request.dbsession.add(user)
        request.dbsession.flush()
        if event_when_creating_entry:
            event = event_when_creating_entry(request=request, user=user, **kwargs)
            request.registry.notify(event)
        return user
