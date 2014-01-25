'''
Created on 13.01.2014

@author: ruckt
'''
from __future__ import print_function

from world.generate import worldgenerator
from render.voxel.chunkarray import Chunk, ChunkArray
import numpy
import pyopencl

class DiamondSquareGenerator(worldgenerator.WorldGenerator):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        super(DiamondSquareGenerator, self).__init__(params)
        self.roughness = params['roughness']
        self.widthlog2 = params['widthlog2']
        self.factor    = params['factor']
        
    def _generate_hmap(self):
        #assert isinstance(chunk, Chunk)
        #assert chunk.level == 0
        w = 2**self.widthlog2
        maxc = w+1
        rnd = self.random
        hmap = numpy.zeros((w+1, w+1), numpy.float32)
        hmap[0,0] = rnd.random() * self.roughness
        hmap[0,w] = rnd.random() * self.roughness
        hmap[w,0] = rnd.random() * self.roughness
        hmap[w,w] = rnd.random() * self.roughness
        for gen_level in range(self.widthlog2): # log2 w
            self.roughness *= self.factor
            
            w2 = w >> 1
            # square step
            for x in range(w2, maxc, w):
                for y in range(w2, maxc, w):
                    sum_s = hmap[x-w2, y-w2] + hmap[x+w2, y-w2] + hmap[x-w2, y+w2] + hmap[x+w2, y+w2]
                    sum_s *= 0.25
                    hmap[x, y] = sum_s + rnd.uniform(-1, 1) * self.roughness
            
            w >>= 1
            offset_y = True
            for x in range(0, maxc, w):
                for y1 in range(0, maxc, w*2):
                    y = y1 - (w if offset_y else 0)
                    if y >= 0:
                        n = 0
                        sum_s = 0
                        for dx, dy in [ (0, -w), (-w, 0), (w, 0), (0, w) ]:
                            if x+dx >= 0 and y+dx >= 0 and x+dx < maxc and y+dy < maxc:
                                sum_s += hmap[x + dx, y + dy] + rnd.uniform(-1, 1) * self.roughness
                                n += 1
                        hmap[x, y] = sum_s / n
                    
                offset_y = not offset_y
            
        return hmap
    
    