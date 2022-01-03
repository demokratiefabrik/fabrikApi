""" Assemblies List View. """

import logging

from cornice.service import Service
import numpy as np

from fabrikApi.models.assembly import DBAssembly
from fabrikApi.models.mixins import arrow
# from fabrikApi.plugins.CIR.views.plots.beeplot import beeplot
from fabrikApi.plugins.CIR.views.plots.compassplot import Compass
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
    # cors_enabled=False,
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

    outery = request.GET.get('outery') 
    if not outery:
        outery = 27

    config={"innery": 2, "outery": int(outery), "forceJustification": True}


    compass = Compass(config)

    # Populate the plot
    try:
        # Capacity: uniform: 500
        for i in np.random.rand(500):
            # print(i, "ll")
            compass.add(round(i*100))
    except Exception as e:
        print("Plot is full: Cannot place more dots meaningfully. The rest is skipped. (Make sure, the data is in random order.)")
        pass

    return compass.plot()

