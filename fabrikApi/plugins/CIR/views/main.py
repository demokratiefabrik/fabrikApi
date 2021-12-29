""" Assemblies List View. """

import logging
from datetime import datetime

from cornice.service import Service

from fabrikApi.models.assembly import DBAssembly
from fabrikApi.models.mixins import arrow
# from fabrikApi.plugins.CIR.views.plots.beeplot import beeplot
from fabrikApi.plugins.CIR.views.plots.compassplot import compassplot
# from fabrikApi.util.cors import CORS_LOCATION, CORS_MAX_AGE

logger = logging.getLogger(__name__)


# SERVICES
cirplot = Service(
    cors_origins=('*',),
    name='cirplot', 
    renderer='string',
    # cors_policy={
    #     'Access-Control-Allow-Origin': '*',
    #     'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
    #     'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
    #     'Access-Control-Allow-Credentials': 'true',
    #     'Access-Control-Max-Age': '1728000',
    #     },
    # # content_disposition= 'File Transfer',
    # cors_enabled=True,
    # cors_origins="*",
    content_type='image/svg+xml',
    description='Show Assembly Plot.', 
    path='/cirplot')

# , headers={'Content-Disposition': 'File Transfer', 'Content-Type': 'application/force-download'})
@cirplot.get(permission='public')
def cir(request):
    """
    Return current cirplot
    """

    # request.response.headers.update({
    #     'Access-Control-Allow-Origin': '*',
    #     'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
    #     'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
    #     'Access-Control-Allow-Credentials': 'true',
    #     'Access-Control-Max-Age': '1728000',
    #     })
    # return beeplot()
    return compassplot()

#     return """<svg width="100" height="100">
#   <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" />
# </svg>"""