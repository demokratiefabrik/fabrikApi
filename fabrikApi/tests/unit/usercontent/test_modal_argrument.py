from fabrikApi import models as models

def test_content_default():
    user = models.DBUser(phone="0796069985")
    content = models.DBContent("text", "title", "pro", 1, user, parent_id=None,
                 parent_type=None, order=None, locked=False)
    assert content.title == 'title'
