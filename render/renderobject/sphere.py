'''
Created on 24.12.2013

@author: ruckt
'''
from render.renderobject.renderobject import RenderObject, ROLocatable,\
    render_object

import numpy

@render_object("sphere")
class Sphere(ROLocatable, RenderObject):
    '''
    A sphere in 3D space. Has a position and radius but no orientation.
    '''
    
    type_id = 4
    dtype = numpy.dtype([ ('position', numpy.float32, 4), ('radius', numpy.float32) ])

    def __init__(self, data):
        '''
        Constructor
        '''
        super(Sphere, self).__init__(data)
        
    @property
    def radius(self):
        return self.data['radius']
    
    @radius.setter
    def radius(self, value):
        self.data['radius'] = value
