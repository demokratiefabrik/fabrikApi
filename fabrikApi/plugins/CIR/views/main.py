""" Assemblies List View. """

from io import BytesIO
import logging
from scipy import stats
    
from cornice.service import Service
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from numpy import random

from fabrikApi.models.assembly import DBAssembly
from fabrikApi.models.mixins import arrow
# from fabrikApi.plugins.CIR.views.plots.beeplot import beeplot
from fabrikApi.plugins.CIR.views.plots.compassplot import Compass
# from fabrikApi.util.cors import CORS_LOCATION, CORS_MAX_AGE
import lxml.etree as ET


logger = logging.getLogger(__name__)


# SERVICES
cirplot = Service(
    cors_origins=('*',),
    name='cirplot', 
    renderer='string',
    content_type='image/svg+xml',
    description='Show Assembly Plot.', 
    path='/cirplot')

# , headers={'Content-Disposition': 'File Transfer', 'Content-Type': 'application/force-download'})
@cirplot.get(permission='public')
def cir(request):
    """
    Return current cirplot
    """

    config={"markerSizeFactor": float(request.GET.get('marker-size-factor', 1))}

    number = int(request.GET.get('number', 300))
    distribution = request.GET.get('distribution', 'uniform') 

    def uniform(x):
        return x*100
    def skewedSlight(x):
        return x**(1.15)*100
    def skewedNormal(x):
        return x**(1.35)*100
    def polarized(x, exp):
        side = int(round(x*1000)) % 2
        x = x**exp*100
        if side == 1:
            return 100-x
        return x
    def polarizedSlight(x):
        return polarized(x, 1.7)
    def polarizedStrong(x):
        return polarized(x, 1)

    rvars = np.random.rand(number)
    if distribution == 'skewed-slight':
        transform = skewedSlight
    elif distribution == 'skewed-normal':
        transform = skewedNormal
    elif distribution == 'skewed-strong':
        transform = uniform
        rvars=stats.beta.rvs(5,1,loc=0,scale=1,size=number)
    elif distribution == 'polarized-strong':
        transform = polarizedStrong
        rvars=stats.beta.rvs(8,0.5,loc=0,scale=1,size=number)
    elif distribution == 'polarized-slight':
        transform = polarizedSlight
    else:
        transform = uniform

    data = []
    for i in rvars:
        data.append(transform(i))
    
    compass = Compass(data=data, config=config)

    fig = compass.plot()

    f = BytesIO()
    fig.savefig(f, format='svg')
    root = ET.fromstring(f.getvalue())  # Convert to XML Element Templat
    f.truncate(0)  # empty stream again
    
    # XML POST-MODIFICATIONS
    # set 100% size
    root.attrib['width'] = '100%'
    root.attrib.pop('height')

    # Add interactivity to dot-nodes
    # TODO: do more efficient xpath...
    scatgrid = root.find('.//*[@id="scatgrid"]')
    if scatgrid:
        nodes = scatgrid.findall('.//*[@clip-path]/*')
        for i in range(len(nodes)):
            node = nodes[i]
            node.attrib['id'] = "dot%s" % i
            node.attrib['onclick'] = "dmclick(this, %s);" % i
            node.attrib['onmouseover'] = "dmover(this, %s);" % i
            node.attrib['onmouseout'] = "dmout();"

    # export XML
    content = ET.tostring(root,  xml_declaration=True)
    return content.decode("utf-8")
