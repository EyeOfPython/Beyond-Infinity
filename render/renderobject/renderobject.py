'''
Created on 24.12.2013

@author: ruckt
'''
import numpy
from transformations import quaternion_from_euler, quaternion_multiply, quaternion_about_axis

class RenderObject(object):
    '''
    Something that needs to be rendered with object data (center/origin/vertices etc.) and (in cases) orientation.
    '''
    
    # specifies the data type used for this renderobject instance, thus determining the size in bytes.
    # if None, data will be None.
    dtype = None
    
    _render_object_classes = dict()
    _light_classes = dict()

    def __init__(self, data):
        '''
        Constructor. Gets called by Scene.create_object
        '''
        self.data     = data
        self.data_ref = None
    
    @property
    def orientation(self):
        return None

    @orientation.setter
    def orientation(self, value):
        raise NotImplemented("This RenderObject has no orientation.")
    
    @property
    def position(self):
        return None
    
    @position.setter
    def position(self, value):
        raise NotImplemented("This RenderObject has no position")
    
    def orientation_from_euler(self, roll, pitch, yaw):
        if self.orientation is None:
            raise NotImplemented("This RenderObject has no orientation")
        self.orientation = quaternion_from_euler(roll, pitch, yaw)
    
    def rotate(self, roll, pitch, yaw):
        '''
        Rotate the render object around the axes. 
        Raises an error if self.orientation is None.
        '''
        ori = self.orientation
        if ori is None:
            raise 
        self.orientation = quaternion_multiply(quaternion_from_euler(roll, pitch, yaw), ori)
        
    def rotate_around(self, angle, axis):
        '''
        Rotate the render object around the axis.
        Raises an error if self.orientation is None.
        '''
        ori = self.orientation
        if ori is None:
            raise NotImplemented("This RenderObject has no orientation")
        self.orientation = quaternion_multiply(ori, quaternion_about_axis(angle, axis))
        
    def translate(self, x, y, z):
        raise NotImplemented("This RenderObject cannot be translated")
    
    def __hash__(self): # objects are stored in a set
        return id(self)
    
    def __str__(self):
        return "%s(%s)" % (type(self).__name__, self.data)
    
class ROLocatable(object):
    
    @property
    def position(self):
        return self.data['position'][:3]
    
    @position.setter
    def position(self, value):
        self.data['position'][:3] = numpy.array(value, copy=False, dtype=numpy.float32)
        
    def translate(self, x, y, z):
        self.data['position'] += numpy.array([x,y,z,0], numpy.float32)        
        
class ROOrientable(object):
    @property
    def orientation(self):
        return self.data['orientation']
    
    @orientation.setter
    def orientation(self, value):
        self.data['orientation'][:] = numpy.array(value, copy=False, dtype=numpy.float32)
        

def render_property(name, slice_obj=slice(None, None, None)):
    if slice_obj is not None:
        fget = lambda self: self.data[name][slice_obj]
    else:
        fget = lambda self: self.data[name]
    if slice_obj is not None:
        def fset(self, value):
            self.data[name][slice_obj] = numpy.array(value, copy=False, dtype=numpy.float32)
    else:
        def fset(self, value):
            self.data[name] = value
    return lambda func: property(fget, fset)

def render_object(name):
    def new_cls(cls):
        RenderObject._render_object_classes[name] = cls
        return cls
    return new_cls

def light_object(name):
    def new_cls(cls):
        RenderObject._light_classes[name] = cls
        return cls
    return new_cls