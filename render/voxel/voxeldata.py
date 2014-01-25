'''
Created on 30.12.2013

@author: ruckt
'''
import numpy
from render.renderbuffer import RenderBuffer

class VoxelData(object):
    '''
    Stores and manages (raw) voxel data.
    '''

    dtype = numpy.dtype( [ ('scattered_light', numpy.ubyte, 3), 
                           ('points', numpy.ubyte, 15), 
                           ('tex_coord', numpy.ubyte, 2), ('tex_id', numpy.ubyte), 
                           ('bump_map_coords', numpy.ubyte, 2), ('bump_map_id', numpy.ubyte),
                           ('material_id', numpy.ushort), 
                           ('flags', numpy.ubyte),
                           ('topping_type', numpy.ubyte), ('topping_data', numpy.ubyte),
                           ('liquid_type', numpy.ubyte), ('liquid_data', numpy.ubyte) ] )
    
    test_dtype = numpy.dtype( [ ('flags', numpy.ubyte), ('color', numpy.float32, 3), ('_pad', numpy.byte, 3) ] )
    
    num_levels = 6
    
    def __init__(self, ctx, queue):
        '''
        Constructor
        '''
        self.level_buffers = [ RenderBuffer(ctx, queue, 2**26, 2**24) for i in range(self.num_levels) ]
        #self.superdivision_buffers = [ RenderBuffer(ctx, queue, 2**) ]
        
    def allocate_buffer(self, level):
        if level < 0 or level >= self.num_levels:
            raise ValueError("Level is not 0 <= %d <= %d" % (level, self.num_levels-1))
        
        w = 32 >> level
        return self.level_buffers[level].allocate_array(w*w*w, self.test_dtype)
    
    def upload_buffers(self):
        
        for buff in self.level_buffers:
            buff.upload_buffer()
    