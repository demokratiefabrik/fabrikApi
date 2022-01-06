""" Assemblies List View. """

from io import BytesIO
import logging

from cornice.service import Service
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np

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
    def skewedStrong(x):
        return x**2*100
    def polarized(x, exp):
        side = int(round(x*1000)) % 2
        x = x**exp*100
        if side == 1:
            return 100-x
        return x
    def polarizedSlight(x):
        return polarized(x, 1.7)
    def polarizedStrong(x):
        return polarized(x, 2.5)

    if distribution == 'skewed-slight':
        transform = skewedSlight
    elif distribution == 'skewed-normal':
        transform = skewedNormal
    elif distribution == 'skewed-strong':
        transform = skewedStrong
    elif distribution == 'polarized-strong':
        transform = polarizedStrong
    elif distribution == 'polarized-slight':
        transform = polarizedSlight
    else:
        transform = uniform

    # enable static random numbers
    # np.random.seed(5555)

    # Populate the plot
    data = []
    for i in np.random.rand(number):
        data.append(transform(i))
    
    compass = Compass(data=data, config=config)

    fig = compass.plot()

    f = BytesIO()
    fig.savefig(f, format='svg')
    root = ET.fromstring(f.getvalue())  # Convert to XML Element Templat
    f.truncate(0)  # empty stream again
    
    # fig.set_figwidth(ext.width/fig.dpi*2)
    # fig.set_figheight(ext.height/fig.dpi)
    # remove margins...
    # fig.subplots_adjust(**self.config["zoomUnits"])


    
    # XML POST-MODIFICATIONS
    # set 100% size
    root.attrib['width'] = '100%'
    root.attrib.pop('height')

    # Add ids to dot-nodes
    # TODO: do more efficient xpath...
    scatgrid = root.find('.//*[@id="scatgrid"]')
    if scatgrid:
        nodes = scatgrid.findall('.//*[@clip-path]/*')
        for i in range(len(nodes)):
            node = nodes[i]
            node.attrib['id'] = "dot%s" % i
            # onmouseoverdot
            node.attrib['onclick'] = "dotclick(this, %s);" % i
            # node.attrib['cursor'] = "pointer"
            node.attrib['pointer-events'] = "all"
            # ="all"

    # export XML
    content = ET.tostring(root,  xml_declaration=True)
    return content.decode("utf-8")

    # TODO:
    # add script
    # script = getSvgScript()
    # Insert the script at the top of the file and save it.
    # root.insert(0, ET.XML(script))
    # # tree.set('onload', 'init(evt)')
    # # tooltip = xmlid['mytooltip_{:03d}'.format(index)]
    # onechild.set('id', 'dot1')
    # content = f.getvalue()

# PLOTTER DEFS



