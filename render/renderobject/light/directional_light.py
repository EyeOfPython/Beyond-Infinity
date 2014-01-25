'''
Created on 25.12.2013

@author: ruckt
'''
from render.renderobject.light.light import Light
import numpy
from render.renderobject.renderobject import light_object, render_property

@light_object("directional")
class DirectionalLight(Light):
    '''
    Light that comes from a direction rather than a point.
    '''
    
    type_id = 1
    dtype   = numpy.dtype( [ ('direction', numpy.float32, 4), ('color', numpy.float32, 4) ] )

    def __init__(self, data):
        '''
        Constructor
        '''
        super(DirectionalLight, self).__init__(data)
    
    @render_property("direction", slice(None, 3, None))
    def direction(self):
        "x,y,z"
        