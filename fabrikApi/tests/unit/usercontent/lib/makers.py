from fabrikApi import models


def makeContentTree(suffix, **kwargs):
    return models.DBUser(username='name' + suffix, **kwargs)


def makeContent(suffix, **kwargs):
    return models.DBAssembly(title='name' + suffix, identifier='name' + suffix, **kwargs)
