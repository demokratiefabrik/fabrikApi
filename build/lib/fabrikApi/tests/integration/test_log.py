from fabrikApi import models
from fabrikApi.tests.lib.makers import makeAssembly, makeLog, makeUser


class Test_integration_log:
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
        # action, old_value, value, user_id,
        #          assembly=None, ip=None, comment=u""

        # create user and assembly
        user = makeUser("1")
        assembly = makeAssembly("1")
        dbsession.add_all([assembly, user])
        dbsession.flush()

        assert assembly.id is not None
        assert user.id is not None

        # Save Log file...
        log = makeLog("1", user=user, assembly=assembly)
        dbsession.add_all([log])
        dbsession.flush()
        assert log.id is not None

        # access log via assembly.logs.
        assert len(assembly.logs) == 1
