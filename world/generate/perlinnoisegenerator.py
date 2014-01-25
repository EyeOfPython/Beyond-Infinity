'''
Created on 19.01.2014

@author: ruckt
'''
from world.generate.worldgenerator import WorldGenerator
import numpy

class PerlinNoiseGenerator(WorldGenerator):
    '''
    Generates super smooth perlin noise :3
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        self.widthlog2 = params['widthlog2']
        self.freq = params['freq']
        self.steps = params['steps']
        self.amplitude_factor = params['amplitude_factor']
        
    def bicublic_interpolate(self, coefficients, x, y):
        return sum( sum( coefficients[i + j*4] * (x**i) * (y**j) for j in range(4) )  for i in range(4) )
    
    def random2d(self, x:int, y:int):
        n = x + y * 57 + 12
        n = (n<<13) ^ n
        return ( 1.0 - ( (n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0)
    
    def _generate_hmap(self):
        w = 1 << self.widthlog2
        hmap = numpy.zeros((w, w), dtype=numpy.float32)
        values = numpy.zeros((4,4), dtype=numpy.float32)
        interpl_matrix = numpy.array([ 
          [ 1 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 ],
          [ 0 , 0 , 0 , 0 , 1 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 ],
          [-3 , 3 , 0 , 0 ,-2 ,-1 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 ],
          [ 2 ,-2 , 0 , 0 , 1 , 1 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 ],
          [ 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 1 , 0 , 0 , 0 , 0 , 0 , 0 , 0 ],
          [ 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 1 , 0 , 0 , 0 ],
          [ 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 ,-3 , 3 , 0 , 0 ,-2 ,-1 , 0 , 0 ],
          [ 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 2 ,-2 , 0 , 0 , 1 , 1 , 0 , 0 ],
          [-3 , 0 , 3 , 0 , 0 , 0 , 0 , 0 ,-2 , 0 ,-1 , 0 , 0 , 0 , 0 , 0 ],
          [ 0 , 0 , 0 , 0 ,-3 , 0 , 3 , 0 , 0 , 0 , 0 , 0 ,-2 , 0 ,-1 , 0 ],
          [ 9 ,-9 ,-9 , 9 , 6 , 3 ,-6 ,-3 , 6 ,-6 , 3 ,-3 , 4 , 2 , 2 , 1 ],
          [-6 , 6 , 6 ,-6 ,-3 ,-3 , 3 , 3 ,-4 , 4 ,-2 , 2 ,-2 ,-2 ,-1 ,-1 ],
          [ 2 , 0 ,-2 , 0 , 0 , 0 , 0 , 0 , 1 , 0 , 1 , 0 , 0 , 0 , 0 , 0 ],
          [ 0 , 0 , 0 , 0 , 2 , 0 ,-2 , 0 , 0 , 0 , 0 , 0 , 1 , 0 , 1 , 0 ],
          [-6 , 6 , 6 ,-6 ,-4 ,-2 , 4 , 2 ,-3 , 3 ,-3 , 3 ,-2 ,-1 ,-2 ,-1 ],
          [ 4 ,-4 ,-4 , 4 , 2 , 2 ,-2 ,-2 , 2 ,-2 , 2 ,-2 , 1 , 1 , 1 , 1 ] ], dtype=numpy.float32)
        
        for i in range(self.steps):
            self._perlin_freq(hmap, values, interpl_matrix, w, self.freq >> i, 2**(-i*self.amplitude_factor) )
        return hmap
        
    def _perlin_freq(self, hmap, values, interpl_matrix, width, grid_size, amplitude):
        c = lambda x0, y0: values[x0 + 1, y0 + 1]
        for x in range(width//grid_size):
            for y in range(width//grid_size):
                for i in range(0, 4):
                    for j in range(0, 4):
                        values[i, j] = self.random2d(x + i - 1, y + j - 1)
                        
                params = numpy.array([ c(0,0),             c(1,0),             c(0,1),             c(1,1) ,
                                       (c(1,0)-c(-1,0))/2, (c(2,0)-c(0,0))/2,  (c(1,1)-c(-1,1))/2, (c(2,1)-c(0,1))/2 ,
                                       (c(0,1)-c(0,-1))/2, (c(1,1)-c(1,-1))/2, (c(0,2)-c(0,0))/2,  (c(1,2)-c(1,0))/2 ,
                                       (c(1,1)-c(1,-1)-c(-1,1)+c(-1,-1))/4, (c(2,1)-c(2,-1)-c(0,1)+c(0,-1))/4, 
                                       (c(1,2)-c(1,0)-c(-1,2)+c(-1,0))/4, (c(2,1)-c(2,-1)-c(0,2)+c(0,0))/4 ] , dtype=numpy.float32)
                
                coefficients = numpy.dot(interpl_matrix, params)
                
                for dx in range(grid_size):
                    for dy in range(grid_size):
                        h = self.bicublic_interpolate(coefficients, (dx/(grid_size)), (dy/(grid_size)))
                        hmap[x*grid_size+dx,y*grid_size+dy] += h * amplitude
    
    