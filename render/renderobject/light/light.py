'''
Created on 25.12.2013

@author: ruckt
'''
from render.renderobject.renderobject import RenderObject, render_property

class Light(RenderObject):
    '''
    A light in the scene. Render time increases linear with number of lights.
    '''
    
    dtype = None

    def __init__(self, data):
        '''
        Constructor
        '''
        super(Light, self).__init__(data)
    
    @render_property("color", slice(None, 3, None))
    def color(self):
        "red, green, blue"
        