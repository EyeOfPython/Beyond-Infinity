'''
Created on 30.12.2013

@author: ruckt
'''
from render.renderobject.renderobject import RenderObject, ROLocatable,\
    render_property, render_object
import numpy

@render_object("aacube")
class AACube(ROLocatable, RenderObject):
    '''
    An axis aligned cube.
    ''' 
    
    type_id = 1
    dtype = numpy.dtype( [ ('position', numpy.float32, 4), ('width', numpy.float32) ] )

    def __init__(self, data):
        '''
        Constructor
        '''
        super(AACube, self).__init__(data)
        
    @property
    def width(self):
        return self.data['width']
    
    @width.setter
    def width(self, value):
        self.data['width'] = value
        