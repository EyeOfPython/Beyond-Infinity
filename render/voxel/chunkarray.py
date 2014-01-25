'''
Created on 08.01.2014

@author: ruckt
'''
import numpy
from render.renderobject.renderobject import render_property
from render.renderbuffer import RenderBuffer
from render.voxel.voxeldata import VoxelData

class Chunk(object):
    
    def __init__(self, data, offset):
        self.data = data
        self.offset = offset
        self.voxel_data = None
        
    @render_property("level", None)
    def level(self):
        "0-5"
        
    @render_property("voxel_offset", None)
    def voxel_offset(self):
        "uint"
        
    def get_voxel(self, loc):
        w = 32 >> self.level
        return self.voxel_data[loc[2]*w*w + loc[1]*w + loc[0]]

    def set_voxel(self, loc, voxel):
        w = 32 >> self.level
        self.voxel_data[loc[2]*w*w + loc[1]*w + loc[0]] = voxel

class ChunkLayer(object):
    
    def __init__(self, data, offset):
        self.data = data
        self.offset = offset
        self.chunks = None
    
    @render_property("x_bounds")
    def x_bounds(self):
        "x_min, x_max"
    
    @render_property("y_bounds")
    def y_bounds(self):
        "y_min, y_max"
    
    @render_property("chunk_offset", None)
    def chunk_offset(self):
        "uint"
    
class ChunkArray(object):
    '''
    Stores chunk layers in a array structure.
    '''
    
    dtype_array = numpy.dtype( [ ('x_bounds', numpy.int32, 2), ('y_bounds', numpy.int32, 2), ('z_bounds', numpy.int32, 2),
                                 ('chunk_layers_ptr', numpy.uintp), ('chunks_ptr', numpy.uintp), ('voxel_levels_ptr', numpy.uintp, 6) ] )
    
    dtype_layer = numpy.dtype( [ ('x_bounds', numpy.int32, 2), ('y_bounds', numpy.int32, 2), ('chunk_offset', numpy.uint32) ] )
    
    dtype_chunk = numpy.dtype( [ ('level', numpy.int), ('voxel_offset', numpy.uint32) ] )
    
    def __init__(self, ctx, queue, z_bounds, init_chunk_array_kernel):
        '''
        
        '''
        num_layers = z_bounds[1] - z_bounds[0]
        self.array_buffer = RenderBuffer(ctx, queue, self.dtype_array.itemsize, 0) # may not grow
        self.layer_buffer = RenderBuffer(ctx, queue, 2**14, 2**12)
        self.chunk_buffer = RenderBuffer(ctx, queue, 2**14, 2**12) # The chunks
        
        self.data, offset = self.array_buffer.allocate_data(self.dtype_array)
        self.layers = [ ChunkLayer(*self.layer_buffer.allocate_data(self.dtype_layer)) for i in range(num_layers) ]
        self.z_bounds = z_bounds
        self.x_bounds = (2**30, -2**30)
        self.y_bounds = (2**30, -2**30)
        self.chunk_layers_ptr = self.layer_buffer._d_buffer.int_ptr
        
        self.voxel_data = VoxelData(ctx, queue)
        self.init_chunk_array_kernel = init_chunk_array_kernel
        
        self.ctx = ctx
        self.queue = queue
        
    def get_layer(self, z):
        if z < self.z_bounds[0] or z >= self.z_bounds[1]:
            raise IndexError("%d index is out of bounds (layer not found)" % z)
        return self.layers[z - self.z_bounds[0]]
        
    def get_chunk(self, x, y, z):
        layer = self.get_layer(z)
        if (x < layer.x_bounds[0] or x >= layer.x_bounds[1] or
            y < layer.y_bounds[0] or y >= layer.y_bounds[1]):
            raise IndexError("Layer %d found, but not chunk (%d, %d) in it. " % (z, x, y))
        x_offset = x - layer.x_bounds[0]
        y_offset = y - layer.y_bounds[0]
        return layer.chunks[x_offset + y_offset*(layer.y_bounds[1]-layer.y_bounds[0])]
        
    def get_voxel(self, x, y, z):
        chunk_x, voxel_x = divmod(x, 32)
        chunk_y, voxel_y = divmod(y, 32)
        chunk_z, voxel_z = divmod(z, 32)
        chunk = self.get_chunk(chunk_x, chunk_y, chunk_z)
        return chunk.get_voxel((voxel_x, voxel_y, voxel_z))
        
    def allocate_layer(self, z, x_bounds, y_bounds):
        layer = self.get_layer(z)
        
        x_size = x_bounds[1] - x_bounds[0]
        y_size = y_bounds[1] - y_bounds[0]
        if x_bounds[0] < self.x_bounds[0]:
            self.x_bounds[0] = x_bounds[0]
        if x_bounds[1] > self.x_bounds[1]:
            self.x_bounds[1] = x_bounds[1]
        if y_bounds[0] < self.y_bounds[0]:
            self.y_bounds[0] = y_bounds[0]
        if y_bounds[1] > self.y_bounds[1]:
            self.y_bounds[1] = y_bounds[1]
            
        layer.x_bounds = x_bounds
        layer.y_bounds = y_bounds
        layer.chunks = [ Chunk(*self.chunk_buffer.allocate_data(self.dtype_chunk)) for i in range(x_size*y_size) ]
        
        layer.chunk_offset = layer.chunks[0].offset / self.dtype_chunk.itemsize
        
    def allocate_chunk(self, x, y, z, level):
        chunk = self.get_chunk(x, y, z)
        chunk.level = level
        data, offset = self.voxel_data.allocate_buffer(level)
        chunk.voxel_offset = offset / self.voxel_data.test_dtype.itemsize
        chunk.voxel_data = data
        
    def upload_buffers(self):
        self.array_buffer.upload_buffer()
        self.layer_buffer.upload_buffer()
        self.chunk_buffer.upload_buffer()
        self.voxel_data.upload_buffers()
        """self.init_chunk_array_kernel(self.queue, (1,), None, 
                                     self.array_buffer._d_buffer, 
                                     self.layer_buffer._d_buffer,
                                     self.chunk_buffer._d_buffer,
                                      *[ self.voxel_data.level_buffers[i]._d_buffer for i in range(self.voxel_data.num_levels) ])
        self.array_buffer.download_buffer()"""
        
    @render_property("x_bounds")
    def x_bounds(self):
        "x_min, x_max"
        
    @render_property("y_bounds")
    def y_bounds(self):
        "y_min, y_max"
    
    @render_property("z_bounds")
    def z_bounds(self):
        "z_min, z_max"

    @render_property("chunk_layers_ptr", None)
    def chunk_layers_ptr(self):
        "chunk_layer_t*"
    
    @render_property("chunks_ptr", None)
    def chunks_ptr(self):
        "chunk_t*"
        
    @render_property("voxel_levels_ptr")
    def voxel_levels_ptr(self):
        "voxel_t* [6]"