'''
Created on 24.12.2013

@author: ruckt
'''
from render.renderobject.renderobject import RenderObject, ROLocatable, ROOrientable, render_property,\
    render_object
import numpy
import transformations

class Camera(ROLocatable, ROOrientable, RenderObject):
    '''
    Represents a camera from which one can render the scene.
    Has position, orientation and bounds.
    '''

    dtype = numpy.dtype( [ ('position', numpy.float32, 4), ('orientation', numpy.float32, 4), ('bounds', numpy.float32, 4), ('warp', numpy.float32) ] )

    def __init__(self, data):
        '''
        Constructor
        '''
        self.yaw = 0
        self.pitch = 0
        self.roll = 0
        super(Camera, self).__init__(data)
    
    def rotate(self, yaw, pitch, roll):
        self.yaw += yaw
        self.pitch += pitch
        self.roll += roll
        q1 = transformations.quaternion_about_axis(self.pitch, (1, 0, 0))
        q2 = transformations.quaternion_about_axis(self.yaw, (0, 0, 1))
        q3 = transformations.quaternion_about_axis(self.roll, (0, 1, 0))
        self.orientation = transformations.quaternion_multiply(transformations.quaternion_multiply(q1, q2), q3)

    @render_property("bounds")
    def bounds(self):
        "left, right, bottom, top"
    
    @property
    def warp(self):
        return self.data['warp']
    
    @warp.setter
    def warp(self, value):
        self.data['warp'] = value
    