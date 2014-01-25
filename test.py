'''
Created on 09.01.2014

@author: ruckt
'''
import unittest
from render.voxel.chunkarray import ChunkArray

import pyopencl
import numpy
import random
from render.voxel.voxeldata import VoxelData
from render.renderbuffer import RenderBuffer

""""h = 6.6e-34
me = 9e-31
p = me * 1000
lbd = h / p
print(lbd * 1000000)"""

class Test(unittest.TestCase):
    
    def setUp(self):
        self.ctx = pyopencl.create_some_context()
        self.queue = pyopencl.CommandQueue(self.ctx)
        
    def test_renderbuffer(self):
        buffer = RenderBuffer(self.ctx, self.queue, 256, 64)
        b1 = buffer.allocate_array(256, numpy.dtype([('p', numpy.byte)]))
        b2 = buffer.allocate_array(16, numpy.dtype([('p', numpy.byte)]))
        
    def test_chunk_array(self):
        chunk_array = ChunkArray(self.ctx, self.queue, (0, 1), None)
        chunk_array.allocate_layer(0, x_bounds=(0, 1), y_bounds=(0, 1))
        chunk_array.allocate_chunk(0, 0, 0, level=0)
        print(chunk_array.chunk_layers_ptr)
        print(chunk_array.x_bounds, chunk_array.y_bounds, chunk_array.z_bounds)
        layer = chunk_array.get_layer(0)
        print(layer.x_bounds, layer.y_bounds)
        
        chunk = chunk_array.get_chunk(0, 0, 0)
        chunk.voxel_data[:] = numpy.array([(1, (0,0,0), (-1, -1)) for i in range(32**3)], dtype=VoxelData.test_dtype)
        
        self.assertEqual(chunk.voxel_data.shape, (32**3,))
        self.assertEqual(chunk.get_voxel((31, 31, 31))['flags'], 1)
        