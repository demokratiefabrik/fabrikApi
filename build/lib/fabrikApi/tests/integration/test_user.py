from fabrikApi import models
from fabrikApi.tests.lib.makers import makeUser


class Test_integration_user:
    def _callFUT(self, request):
        # from fabrikApi.views.default import view_page
        # return view_page(request)
        pass

    def _makeContext(self, page):
        # from tutorial.routes import PageResource
        # return PageResource(page)
        pass

    def test_it(self, dummy_request, dbsession):
        # add a page to the db
        user = makeUser("1")
        # page = makePage('IDoExist', 'Hello CruelWorld IDoExist', user)
        dbsession.add_all([user])
        dbsession.flush()

        assert user.id is not None
