from fabrikApi import models


def test_contenttree_default():
    contenttree = models.DBContentTree(title='title', info='info')
    assert contenttree.title == 'title'
