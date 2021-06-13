from fabrikApi.models.stage import DBStage
from fabrikApi.models import DBContent, DBContentTree, get_assembly_by_identifier

""" Quasi: Entry points to access API Objects """


class AssemblyFactory(object):
           
    def __init__(self, request):
        """ This method loads assembly into the request-object
        and checks object-speciic ACL (including object inheritance)
        """
        self.request = request

    def __getitem__(self, key):
        # TODO: only use id instead of key...
        self.request.assembly = get_assembly_by_identifier(self.request, key)
        # self.request.assembly = self.request.dbsession.query(DBAssembly).get(key)
        # self.request.assembly.patch()
        self.request.assembly.setup_lineage(self.request)
        assert self.request.assembly, "invalid assembly specified."
        return(self.request.assembly)


class StageManagerFactory(object):

    def __init__(self, request):
        """ This method loads stage object into the request-object
        and checks object-specific ACLs (including object inheritance)
        """
        self.request = request

    def __getitem__(self, key):
        # TODO: only use id instead of key...
        stage = self.request.dbsession.query(DBStage).get(key)
        self.request.assembly = stage.assembly
        self.request.stage = stage
        # stage.patch()
        stage.setup_lineage(self.request)

        return self.request.stage


class ContentTreeManagerFactory(object):

    def __init__(self, request):
        """ This method loads contenttree object into the request-object
        and checks object-specific ACLs (including object inheritance)
        """
        self.request = request

    def __getitem__(self, key):
        contenttree = self.request.dbsession.query(DBContentTree).get(key)
        self.request.assembly = contenttree.assembly
        self.request.contenttree = contenttree
        # contenttree.patch()
        contenttree.setup_lineage(self.request)

        return self.request.contenttree


class ContentManagerFactory(object):

    def __init__(self, request):
        """ This method loads content object into the request-object
        and checks object-specific ACLs (including object inheritance)
        """
        self.request = request

    def __getitem__(self, key):
        content = self.request.dbsession.query(DBContent).get(key)
        self.request.assembly = content.contenttree.assembly
        self.request.contenttree = content.contenttree
        self.request.content = content
        # content.patch()
        content.setup_lineage(self.request)
        return content
