from fabrikApi import models


def makeUser(suffix, **kwargs):
    return models.DBUser(username='name' + suffix, **kwargs)


def makeAssembly(suffix, **kwargs):
    return models.DBAssembly(title='name' + suffix, identifier='name' + suffix, **kwargs)


def makeLog(action, user, **kwargs):
    return models.DBLog(action=action, user=user, **kwargs)
