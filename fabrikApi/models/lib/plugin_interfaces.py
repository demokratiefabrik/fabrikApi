"""
Here are the patches defined to customize assemblies / contenttree / content and stage types).

Patching is a more flexible alternative to SQLALACHEMY Model Inheritance. The latter
requires numerous Database tables.

__all__ list contains all the plugins within this directory.
Plugins may offer patches for stages, containertypes and contenttypes.
Patches are applied by the patch method.E.g:

> self.patch()

https://stackoverflow.com/questions/38485123/monkey-patching-bound-methods-in-python
https://stackoverflow.com/questions/972/adding-a-method-to-an-existing-object-instance

TODO: use Interfaces
"""

import glob
from os.path import isfile, join, split
from sqlalchemy import Column
from pathlib import Path

from fabrikApi import plugins
from fabrikApi.models.mixins import ChoiceType

plugin_folder = join(Path(__file__).parent.parent.parent, 'plugins')


def get_installed_plugins() -> Path:
    installed_plugins_folders = glob.glob(join(plugin_folder, "*"))
    return list(split(f)[1] for f in installed_plugins_folders if not isfile(f) and not split(f)[1].startswith('_'))


INSTALLED_PLUGIN_NAMES = get_installed_plugins()
PLUGIN_MODULES = {'STAGE': {}, 'CONTENT': {}, 'CONTENTTREE': {}, 'ASSEMBLY': {}, 'MONITOR': {}}

# STAGE_MODULES/ CONTENTTREE MODULES / CONTENT_MODULES / MONITOR_MODULES
# Create Indexes of all installed Plugin-Modules (Without loading them)
# e.g. {module_name: installed_plugin_name}
# TODO: how to deal with duplicates module duplicates (across plugins)...: => prevent duplicate names!!!
for plugin in INSTALLED_PLUGIN_NAMES:
    stagemodules = glob.glob(join(plugin_folder, plugin, "stagetypes/*.py"))
    stagemodules = dict((split(f)[1][:-3], plugin) for f in stagemodules if isfile(f) and not split(f)[1].startswith('_'))
    PLUGIN_MODULES['STAGE'].update(stagemodules)
    contentmodules = glob.glob(join(plugin_folder, plugin, "contenttypes/*.py"))
    contentmodules = dict((split(f)[1][:-3], plugin) for f in contentmodules if isfile(f) and not split(f)[1].startswith('_'))
    PLUGIN_MODULES['CONTENT'].update(contentmodules)
    contenttreemodules = glob.glob(join(plugin_folder, plugin, "contenttreetypes/*.py"))
    contenttreemodules = dict((split(f)[1][:-3], plugin) for f in contenttreemodules if isfile(f) and not split(f)[1].startswith('_'))
    PLUGIN_MODULES['CONTENTTREE'].update(contenttreemodules)
    assemblymodules = glob.glob(join(plugin_folder, plugin, "assemblytypes/*.py"))
    assemblymodules = dict((split(f)[1][:-3], plugin) for f in assemblymodules if isfile(f) and not split(f)[1].startswith('_'))
    PLUGIN_MODULES['ASSEMBLY'].update(assemblymodules)
    monitormodules = glob.glob(join(plugin_folder, plugin, "monitors/*.py"))
    monitormodules = dict((split(f)[1][:-3], plugin) for f in monitormodules if isfile(f) and not split(f)[1].startswith('_'))
    PLUGIN_MODULES['MONITOR'].update(monitormodules)


__all__ = ['ContentTreePluginInterface', 'ContentPluginInterface', 'StagePluginInterface',
           'PLUGIN_MODULES']
# __all__ += INSTALLED_PLUGIN_NAMES
# TODO: is INSTALLED_PLUGIN_NAMES used here?


class AssemblyPluginInterface(object):
    """
    Augment an hierarchical object having "parent" and "type_" attributes.

    TODO: All the plugin parameters should be overwritteable within Asssembly Configuration.
    => maximum assembly level customization...
    """

    # Properties to be replaces by AssemblyType Patches
    # --------------------------------------------------

    MAX_DAILY_USER_COMMENTS = None
    MAX_DAILY_USER_PROPOSALS = None

    ASSEMBLYTYPES = []

    # Plugin Specification
    type_ = Column(
        "type",
        ChoiceType(PLUGIN_MODULES['ASSEMBLY'].keys()),
        nullable=False)

    def patch(self):
        """ Extend this class/instance by custom contenttree-type configuration """

        # Patch only once...
        if self.patched:
            return True

        plugin_name = PLUGIN_MODULES['ASSEMBLY'][self.type_]
        plugin = plugins.__dict__[plugin_name]
        module = plugin.__dict__['assemblytypes'].__dict__[self.type_]
        module.patch(self)
        self.__doc__ = module.__doc__
        self.patched = True

    @property
    def patched(self):
        """ marks when this contenttree has been patched by contenttree type specific patch."""
        return self._patched

    @patched.setter
    def patched(self, value):
        assert value is True, "object should be patched here.."
        self._patched = value

    _patched = False


class ContentTreePluginInterface(object):
    """
    Augment an hierarchical object having "parent" and "type_" attributes.

    TODO: All the plugin parameters should be overwritteable within Asssembly Configuration.
    => maximum assembly level customization...
    """

    # Properties to be replaces by ContentTreeType Patches
    # --------------------------------------------------

    # Which Content types are allowed in this contenttree:
    CONTENTTYPES = []

    DEFAULT_CONTENT_TEXT_MAX_LENGTH = 3000
    CONTENT_TEXT_MAX_LENGTH_BY_TYPES = {
        'COMMENT': 650,
        'FOLDER': 300,
    }

    DEFAULT_CONTENT_TITLE_MAX_LENGTH = 100
    CONTENT_TITLE_MAX_LENGTH_BY_TYPES = {
    }

    # Specify the default content type (used when type_ indication is missing):
    DEFAULT_CONTENT_TYPE = None

    # Define the hierarchical relationship of the Content types within this contenttree:
    # {'PRO': ['COMMENT', 'QUESTION'], None: ['PRO', 'COMMENT']}
    ONTOLOGY = None

    # specify the content types that are priate property (can only be edited by owners)
    # all other content is common property and subject to peer review
    PRIVATE_PROPERTY_CONTENT = ['COMMENT', 'QUESTION']
    COMMON_PROPERTY_CONTENT = []
    GIVEN_PROPERTY_CONTENT = ['FOLDER', 'UPDATEPROPOSAL']

    # CUSTOM ACLs: Which content types cand be apppend/rate child content to this contenttree:
    # {'ContentType': ['User-Role1','User-Role2'] }
    # Note: Define an empty list [] if nobody can rate/edit this content.
    # Note: There is not much meaning in adding managers and administrators to these list. T
    # contenttree belongs to citizens. Yet, due to legal reasons, managers can always edit any kind of content.
    # Note: if the PRIVATE_PROPERTY_CONTENT is enabled: nobody can delete/edit content of others.
    # Only own content, if it is allowed by ACLs
    # ACL_RATE_CONTENT = {'DEFAULT': ['add']}
    # ACL_EDIT_CONTENT = {'DEFAULT': ['modify']}
    # # same as above: but optional: if None ACL_EDIT_CONTENT is used.
    # ACL_DELETE_CONTENT = None
    # ACL_APPEND_CONTENT = None

    # A Vessel for contenttree-type-specific configurations / data:
    CUSTOM_DATA = {}

    # Plugin Specification
    type_ = Column(
        "type",
        ChoiceType(PLUGIN_MODULES['CONTENTTREE'].keys()),
        # default=stagetypes.StageConfiguration.StageTypes['DEFAULT'],
        nullable=False)

    # def is_valid_child_type(self, type_, parent=None):
    #     assert type_, "Content Type specification is missing"
    #     if parent:
    #         return(type_ in self.ONTOLOGY[parent.type_])
    #     else:
    #         return(type_ in self.ONTOLOGY[None])

    # def get_default_type(self, parent=None):
    #     """ get default type for this content (if available) """

    #     if parent:
    #         return parent.DEFAULT_CONTENT_TYPE or self.DEFAULT_CONTENT_TYPE
    #     else:
    #         return self.DEFAULT_CONTENT_TYPE

    def get_configuration(self, request): 
        return {
            'ONTOLOGY': self.ONTOLOGY,
            'CUSTOM_DATA': self.CUSTOM_DATA,
            'CONTENT_TEXT_MAX_LENGTH_BY_TYPES': self.CONTENT_TEXT_MAX_LENGTH_BY_TYPES,
            'DEFAULT_CONTENT_TEXT_MAX_LENGTH': self.DEFAULT_CONTENT_TEXT_MAX_LENGTH,
            'CONTENT_TITLE_MAX_LENGTH_BY_TYPES': self.CONTENT_TITLE_MAX_LENGTH_BY_TYPES,
            'DEFAULT_CONTENT_TITLE_MAX_LENGTH': self.DEFAULT_CONTENT_TITLE_MAX_LENGTH,            
            'CONTENTTYPES': self.CONTENTTYPES,
            'ALLOWED_CONTENT_TYPES_TO_ADD': self.allowed_content_types_to_add(request),
            'PRIVATE_PROPERTY_CONTENT': self.PRIVATE_PROPERTY_CONTENT,
            'COMMON_PROPERTY_CONTENT': self.COMMON_PROPERTY_CONTENT,
            'GIVEN_PROPERTY_CONTENT': self.GIVEN_PROPERTY_CONTENT
        }

    def patch(self):
        """ Extend this class/instance by custom contenttree-type configuration """

        # Patch only once...
        if self.patched:
            return True

        plugin_name = PLUGIN_MODULES['CONTENTTREE'][self.type_]
        plugin = plugins.__dict__[plugin_name]
        module = plugin.__dict__['contenttreetypes'].__dict__[self.type_]
        module.patch(self)
        self.__doc__ = module.__doc__
        self.patched = True

    @property
    def patched(self):
        """ marks when this contenttree has been patched by contenttree type specific patch."""
        return self._patched

    @patched.setter
    def patched(self, value):
        assert value is True, "object should be patched here"
        self._patched = value

    _patched = False


class ContentPluginInterface(object):

    # DB Backend
    # ContentTypes = {}

    # does the content belongs to the collective (and not to the creater?)
    # TODO: move to contenttree property, only.
    # common_property = True

    # many content should come in random order. However, some content (e.g. TEXTSHEET) requires
    # fixed ordered position
    is_in_random_order = True

    # A Vessel for content-type-specific configurations / data:
    CUSTOM_DATA = {}

    # PROPERTY OWNERSHIP
    COMMON_PROPERTY_CONTENT = False
    GIVEN_PROPERTY_CONTENT = False
    PRIVATE_PROPERTY_CONTENT = True

    # wich is the default child content type
    # Note: set to None if default value of contenttree should be used, instead.
    DEFAULT_CONTENT_TYPE = None

    # Rating Scale Range
    RATING_RANGE = range(0, 101)  # Note: upper limit not included
    # Salience Scale Range
    SALIENCE_RANGE = range(0, 101)  # Note: upper limit not included

    # Possibility to extend content acls...
    CUSTOMIZED_ACLS = []
    # NOT IMPLEMENTED

    # def get_approving_conditions(self, peerreview):
    #     """ What is peerreview criteria are to apply for this specific operation.
    #     This method returns the default values. The method can be overwritten by methods
    #     within the specific content type extensions.

    #     # examples of criteria:
    #     peerreview: e.g. operation type....
    #     content: e.g. nof_mofications...
    #     """

    #     assert peerreview, "peerreview is empty"
    #     assert self.COMMON_PROPERTY_CONTENT

    #     quorum = 3  # at least 3 respondents
    #     rate = 50  # at least 50% approvals

    #     return(quorum, rate)

    def acl_extension_by_content_plugins(self, acl):
        acl.extend(self.CUSTOMIZED_ACLS)

    @property
    def is_common_property_content(self):
        return self.COMMON_PROPERTY_CONTENT

    @property
    def is_given_property_content(self):
        return self.GIVEN_PROPERTY_CONTENT

    @property
    def is_private_property_content(self):
        return self.PRIVATE_PROPERTY_CONTENT

    # Plugin Specification
    type_ = Column(
        "type",
        ChoiceType(PLUGIN_MODULES['CONTENT'].keys()),
        # default=stagetypes.StageConfiguration.StageTypes['DEFAULT'],
        nullable=False)

    def patch(self):
        """ Extend this class/instance by content_type specific methods """

        # TODO: is this right, at this position? Why?
        self._is_in_random_order = self.is_in_random_order

        # Patch only once...
        if self.patched:
            return True

        # plugin_name = CONTENT_MODULES[self.type_]
        plugin_name = PLUGIN_MODULES['CONTENT'][self.type_]
        plugin = plugins.__dict__[plugin_name]
        module = plugin.__dict__['contenttypes'].__dict__[self.type_]
        module.patch(self)
        self.__doc__ = module.__doc__
        self.patched = True

    @property
    def patched(self):
        """ marks when this contenttree has been patched by contenttree type specific patch."""
        return self._patched
    @patched.setter
    def patched(self, value):
        assert value is True, "object should be patched here"
        self._patched = value

    _patched = False


class StagePluginInterface(object):
    """ """

    # key: translation_code
    StageTypes = {}
    # "SURVEY": "SURVEY",
    # "CIR_PROS_AND_CONS": "CIR_PROS_AND_CONS",
    # "CIR_PROS_AND_CONS_ANALYSIS": "CIR_PROS_AND_CONS_ANALYSIS",
    # "VAA_QUESTIONS": "VAA_QUESTIONS",
    # "VAA_TOPICS": "VAA_TOPICS",
    # "VAA_CONCLUSION": "VAA_CONCLUSION",
    # "TEXTSHEET": "TEXTSHEET"}

    # Properties to be replaces by StageType Patches
    # --------------------------------------------------

    # Default icon for this type of stages:
    DEFAULT_ICON = 'mdi-head-cog-outline'

    # After how many days the stage should be scheduled (put in alert state) again...
    # (users have to visit the scheduled stages in order to continue... )
    # Tipp: Use a high value to show stage only once...
    SCHEDULE_ALERT_FREQUENCY_IN_DAYS = 1

    # Shall the Stage be a one-timer?
    # True: The stage is set as completed, as soon it has been unalerted once.
    # False: The stage stays accessible forever.
    ONE_TIME_STAGE = False

    # A Vessel for stage-type-specific configurations / data:
    CUSTOM_DATA = {}

    # Plugin Specification
    type_ = Column(
        "type",
        ChoiceType(PLUGIN_MODULES['STAGE'].keys()),
        # default=stagetypes.StageConfiguration.StageTypes['DEFAULT'],
        nullable=False)

    def patch(self):
        """ Extend this class/instance by custom stage-type configuration """

        # Patch only once...
        if self.patched:
            return True

        plugin_name = PLUGIN_MODULES['STAGE'][self.type_]
        plugin = plugins.__dict__[plugin_name]
        module = plugin.__dict__['stagetypes'].__dict__[self.type_]
        module.patch(self)

        self.__doc__ = module.__doc__
        self.patched = True

    @property
    def patched(self):
        """ marks when this stage has been patched by stage type specific patch."""
        return self._patched

    @patched.setter
    def patched(self, value):
        assert value is True, "object should be patched here"
        self._patched = value
    _patched = False
