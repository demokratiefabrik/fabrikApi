""" Assemblies List View. """

# from io import BytesIO
import logging
import math
from scipy import stats
    
from cornice.service import Service
# from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
# from numpy import random

# from fabrikApi.models.assembly import DBAssembly
# from fabrikApi.models.mixins import arrow
# from fabrikApi.plugins.CIR.views.plots.beeplot import beeplot
from fabrikApi.plugins.CIR.views.plots.polarbee import Compass
# from fabrikApi.util.cors import CORS_LOCATION, CORS_MAX_AGE
import lxml.etree as ET


logger = logging.getLogger(__name__)



def get_data(request):
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

    return data



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

    config={
        "markerSizeFactor": float(request.GET.get('marker-size-factor', 1)),
        "markerColorMap": request.GET.get('marker-color-map', 'winter'),
        "xAxisLabels":  [
            (math.radians(10), 'Kontra'),
            (math.radians(90), 'Unentschieden'),
            (math.radians(170), 'Pro')
        ]
    }
    data = get_data(request)
    compass = Compass(data=data, config=config)
    xml = compass.plotAsXml()    


    # XML POST-MODIFICATIONS

    # following nodes are renderes as last (for on-top/vertical ordering.)
    selectedNodeIds = [60]
    selectedNodeEls = []

    # set 100% size
    root = ET.fromstring(xml)  # Convert to XML Element Templat
    root.attrib['width'] = '100%'
    root.attrib.pop('height')
    
    # Add interactivity to dot-nodes
    # TODO: do more efficient xpath...
    scatgrid = root.find('.//*[@id="scatgrid"]')
    if scatgrid:
        nodes = scatgrid.findall('.//*[@clip-path]/*')
        for i in range(len(nodes)):
            node = nodes[i]
            node.attrib['id'] = "dot%s" % i # Temporary
            node.attrib['value'] = "%s" % round(compass.dots[i].value) # Temporary
            node.attrib['pos'] = "%s" % i # Original Position in List (used for z-index reordering)
            node.attrib['onclick'] = "dmclick(this, %s);" % i
            node.attrib['onmouseover'] = "dmover(this, %s);" % i
            if i in selectedNodeIds:
                selectedNodeEls.append(node)

        for sel in selectedNodeEls:
            g = sel.getparent()
            scatgrid.append(g) 
            # test_list.insert(0, test_list.pop())
            pass

        # Ad new element
        # ET.SubElement(root,"use", id='placeholder')


    # Append Background to XML Image
    # z = compass.config['zoomFactor']/2
    # x, y, r = compass._matplotlib_get_polar_chart_position()
    # bgEl = ET.fromstring("""<g id="bgpattern">
    #     <defs>
    #     <path id="meab67247b1" d="M 0 7.284288  C 1.931816 7.284288 3.784769 6.516769 5.150769 5.150769  C 6.516769 3.784769 7.284288 1.931816 7.284288 0  C 7.284288 -1.931816 6.516769 -3.784769 5.150769 -5.150769  C 3.784769 -6.516769 1.931816 -7.284288 0 -7.284288  C -1.931816 -7.284288 -3.784769 -6.516769 -5.150769 -5.150769  C -6.516769 -3.784769 -7.284288 -1.931816 -7.284288 0  C -7.284288 1.931816 -6.516769 3.784769 -5.150769 5.150769  C -3.784769 6.516769 -1.931816 7.284288 0 7.284288  z " style="stroke: #1f77b4; stroke-opacity: 0.75"/>
    #     <linearGradient id="myGradient" >
    #     <stop offset="0%%"  stop-color="gold" />
    #     <stop offset="100%%" stop-color="blue" />
    #     </linearGradient>
    #     </defs>
    #     <circle cx="%s" cy="%s" r="%s" fill="url('#myGradient')" />
    # </g>""" % (x*z, y*z, r*z))
    # axes1El = root.find('.//*[@id="axes_1"]')
    # axes1El.insert(1, bgEl)


    # export XML
    content = ET.tostring(root,  xml_declaration=True, encoding="UTF-8")
    return content.decode("utf-8")
