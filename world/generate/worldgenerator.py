'''
Created on 13.01.2014

@author: ruckt
'''
import random
import numpy
import time
from render.voxel.chunkarray import ChunkArray
import pyopencl

class WorldGenerator(object):
    '''
    Base class for generating chuks
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        self.random = random.Random()
        
    def generate_chunk(self, chunk):
        
        pass
    
    def generate(self, chunk_array, ctx, queue, heightmap_kernel):
        assert isinstance(chunk_array, ChunkArray)
        hmap = self._generate_hmap()
        x_bounds = (0, 8)
        y_bounds = (0, 8)
        for z in range(1):
            chunk_array.allocate_layer(z, x_bounds, y_bounds)
            for x in range(8):
                for y in range(8):
                    chunk_array.allocate_chunk(x, y, z, level=0)
        print("allocated!")
        ihmap = numpy.empty((256,256), dtype=numpy.int32)
        for x in range(256):
            for y in range(256):
                height = hmap[x, y]
                ihmap[x, y] = int(max(min(height*7.4 + 8, 32), 0))
        """for x in range(256):
            print(x)
            for y in range(256):
                height = hmap[x, y]
                z_max = int(max(min(height + 8, 32), 0))
                for z in range(32):
                    voxel = chunk_array.get_voxel(x, y, z)
                    voxel['flags'] = 0 if z_max < z else 1"""
        chunk_array.upload_buffers()
        buffer = pyopencl.Buffer(ctx, pyopencl.mem_flags.READ_ONLY|pyopencl.mem_flags.COPY_HOST_PTR, hostbuf = ihmap)
        #pyopencl.enqueue_copy(queue, buffer, hmap)
        heightmap_kernel(queue, (255, 255, 32), None, chunk_array.array_buffer._d_buffer, buffer)
        pyopencl.enqueue_copy(queue, chunk_array.voxel_data.level_buffers[0]._h_buffer, chunk_array.voxel_data.level_buffers[0]._d_buffer)
        chunk_array.upload_buffers()
    
if __name__ == '__main__':
    from world.generate.diamondsquaregenerator import DiamondSquareGenerator
    from world.generate.perlinnoisegenerator import PerlinNoiseGenerator
    gen = DiamondSquareGenerator({ 'widthlog2': 8, 'roughness': 1, 'factor': 0.6 })
    gen = PerlinNoiseGenerator({ 'widthlog2': 8 })
    numpy.set_printoptions(threshold=100, linewidth=32 * 10, precision=1, )
    hmap = gen._generate_hmap()
    import pygame
    surface = pygame.display.set_mode((256*3, 256*3))
    
    for x in range(256):
        for y in range(256):
            pygame.draw.rect(surface, (int(max(min((hmap[x, y]+2)*80, 255), 0)),)*3, [x*3, y*3, x*3+3, y*3+3])
            
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        time.sleep(0.02)
        pygame.display.update()