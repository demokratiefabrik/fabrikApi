# -*- coding: utf-8 -*-
"""
See README.md
"""

__title__ = 'fabrikApi'
__version__ = '0.1'
__author__ = 'Dominik Wyss'
__license__ = 'GNU'
__copyright__ = 'Copyright 2020-2022 Dominik Wyss'


import logging
import arrow
from cornice.renderer import CorniceRenderer
from pyramid.config import Configurator
from fabrikApi.util.request import MoxRequest

logger = logging.getLogger(__name__)


class ExtendedCorniceRenderer(CorniceRenderer):
    def __init__(self, *args, **kwargs):
        """Adds a `arrow` adapter by default."""
        super(ExtendedCorniceRenderer, self).__init__(*args, **kwargs)

        def datetime_adapter(obj, request):
            return obj.for_json()
        self.add_adapter(arrow.Arrow, datetime_adapter)


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """

    config = Configurator(
        settings=settings,
        request_factory=MoxRequest  # Custom Request Object
    )

    # JWT (Authorization) Handling
    config.include('.util.authorization')

    # Cornice (restfull apis, incl. routes)
    config.include("cornice")
    config.add_renderer('cornicejson', ExtendedCorniceRenderer())
    config.add_settings(handle_exceptions=False)

    # Setup Basis-DB Models at the end (it finalizes relationships using configure_mappers)
    config.include('.models')

    # Start Server
    config.scan()
    return config.make_wsgi_app()
