from fabrikApi import models


def retrieveUser(user_id=None, **kwargs):
    return models.DBUser(username='name' + suffix, **kwargs)


def retrieveAssembly(suffix, **kwargs):
    return models.DBAssembly(title='name' + suffix, identifier='name' + suffix, **kwargs)


def retrieveLog(action, **kwargs):
    return models.DBLog(action=action, **kwargs)
