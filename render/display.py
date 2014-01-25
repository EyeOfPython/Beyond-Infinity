'''
Created on 21.01.2014

@author: ruckt
'''

import pyopencl as cl
from render.program import build_program
from render.scene import Scene
import numpy

import pygame

class OpenCLError(Exception):
    pass

class Display(object):
    '''
    Handles the rendering
    '''


    def __init__(self, size):
        '''
        Constructor
        '''
        
        self.size = size
        self.ctx = None
        
    def setup_opencl(self):
        platforms = cl.get_platforms()
        if not platforms:
            raise OpenCLError("No OpenCL platforms found.")
        self.ctx =   cl.Context(platforms[0].get_devices(device_type=cl.device_type.GPU))
        self.queue = cl.CommandQueue(self.ctx)
        
    def setup_kernels(self):
        self.cl_program = build_program(self.ctx, "kernels")
        self.raytrace = self.cl_program.raytrace
        self.init_chunk_array = self.cl_program.init_chunk_array
        
    def setup_scene(self):
        self.scene = Scene(self.ctx, self.queue)
        
        self._h_img_canvas = numpy.empty((self.size[0]*4, self.size[1]), dtype=numpy.ubyte)
        im_format = cl.ImageFormat(cl.channel_order.RGBA, cl.channel_type.UNORM_INT8)
        self._d_img_canvas = cl.Image(self.ctx, cl.mem_flags.WRITE_ONLY, im_format, self.size)
        
    def setup_pygame(self):
        pygame.init()
        self.surface = pygame.display.set_mode(self.size)
        
    def init_chunk_array(self):
        self.init_chunk_array(self.queue, )
        
    def render(self):
        self.scene.upload_buffers()
        self.raytrace(self.queue, (16, 4), self.size, self._d_img_canvas, self.scene._cam_buffer)
        
        cl.enqueue_copy(self.queue, self._h_img_canvas, self._d_img_canvas)
        self.surface.blit(pygame.image.fromstring(self._h_img_canvas.tostring(), self.size, 'RGBA'), (0,0))
        
    def render_loop(self):
        self.setup_opencl()
        
        self.setup_kernels()
        self.setup_scene()
        
        self.setup_pygame()
        
        self.render()
        
        clock = pygame.time.Clock()
        while True:
            elapsed = clock.tick(30)/1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            
            self.render()
        