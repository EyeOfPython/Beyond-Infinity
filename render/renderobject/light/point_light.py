'''
Created on 25.12.2013

@author: ruckt
'''
from render.renderobject.renderobject import ROLocatable, light_object
from render.renderobject.light.light import Light
import numpy

@light_object("point")
class PointLight(ROLocatable, Light):
    '''
    A light that emits in all directions from a given location.
    '''
    
    type_id = 2
    dtype = numpy.dtype([ ('position', numpy.float32, 4), ('color', numpy.float32, 4) ])

    def __init__(self, data):
        '''
        Constructor
        '''
        super(PointLight, self).__init__(data)
        