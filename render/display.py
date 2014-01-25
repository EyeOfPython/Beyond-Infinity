'''
Created on 21.01.2014

@author: ruckt
'''

import pyopencl as cl
from render.program import build_program
from render.scene import Scene
import numpy

import pygame
from world.generate.diamondsquaregenerator import DiamondSquareGenerator
import cmath
import random
from render.voxel.voxeldata import VoxelData

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
        self.ctx =   cl.Context(platforms[0].get_devices(device_type=cl.device_type.CPU))
        self.queue = cl.CommandQueue(self.ctx)
        
    def setup_kernels(self):
        self.cl_program = build_program(self.ctx, "kernels")
        self.k_raytrace = self.cl_program.raytrace
        self.k_init_chunk_array = self.cl_program.init_chunk_array
        self.k_write_height_map = self.cl_program.write_height_map
        
    def setup_scene(self):
        self.scene = Scene(self.ctx, self.queue)
        self.scene._chunk_array.upload_buffers()
        self.init_chunk_array()
        self._h_img_canvas = numpy.empty((self.size[0]*4, self.size[1]), dtype=numpy.ubyte)
        im_format = cl.ImageFormat(cl.channel_order.RGBA, cl.channel_type.UNORM_INT8)
        self._d_img_canvas = cl.Image(self.ctx, cl.mem_flags.WRITE_ONLY, im_format, self.size)
        
        #gen = DiamondSquareGenerator({ 'widthlog2': 8, 'roughness': 1, 'factor': 0.6 })
        #gen = PerlinNoiseGenerator({ 'widthlog2': 8, 'freq': 32, 'steps': 4, 'amplitude_factor': 1 })
        #gen.generate(self.scene._chunk_array, self.ctx, self.queue, self.k_write_height_map, self)
        
        self.scene._chunk_array.allocate_layer(0, x_bounds=(0, 2), y_bounds=(0, 2))
        self.scene._chunk_array.allocate_chunk(0, 0, 0, level=0)
        self.scene._chunk_array.allocate_chunk(1, 0, 0, level=0)
        self.scene._chunk_array.allocate_chunk(0, 1, 0, level=0)
        self.scene._chunk_array.allocate_chunk(1, 1, 0, level=0)
        
        for i, j in [ (0,0), (1,0), (0,1), (1,1)]:
            chunk = self.scene._chunk_array.get_chunk(i, j, 0)
            chunk.voxel_data[:] = numpy.array([(random.randint(1,1), (0,0,0), (-1,-1,-1)) for i in range(32**3)], dtype=VoxelData.test_dtype)
        
        self.scene._chunk_array.upload_buffers()
        
    def setup_pygame(self):
        pygame.init()
        pygame.font.init()
        self.surface = pygame.display.set_mode(self.size)
        self.font = pygame.font.SysFont("Garamond", 16)
        
    def init_chunk_array(self):
       
        self.k_init_chunk_array(self.queue, (1,), None, self.scene._chunk_array.array_buffer._d_buffer, 
                                     self.scene._chunk_array.layer_buffer._d_buffer,
                                     self.scene._chunk_array.chunk_buffer._d_buffer,
                                    *[ self.scene._chunk_array.voxel_data.level_buffers[i]._d_buffer for i in range(self.scene._chunk_array.voxel_data.num_levels) ])
        self.scene._chunk_array.array_buffer.download_buffer()
        
    def render(self):
        self.scene.upload_buffers()
        self.k_raytrace(self.queue, self.size, (16, 4), self._d_img_canvas, self.scene._cam_buffer._d_buffer, self.scene._chunk_array.array_buffer._d_buffer)
        
        cl.enqueue_copy(self.queue, self._h_img_canvas, self._d_img_canvas, origin=(0,0), region=self.size)
        img = pygame.image.fromstring(self._h_img_canvas.tostring(), self.size, 'RGBA')
        self.surface.blit(img, (0,0))
        
    def render_loop(self):
        self.setup_opencl()
        
        self.setup_kernels()
        self.setup_scene()
        
        self.setup_pygame()
        
        self.scene.upload_buffers()
        self.init_chunk_array()
        
        self.render()
        
        clock = pygame.time.Clock()
        
        while True:
            elapsed = clock.tick(30)/1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            
            pressed = pygame.key.get_pressed()
        
            sun_speed = 4
            """if pressed[pygame.K_f]: light.direction[0] -= 4*elapsed
            if pressed[pygame.K_h]: light.direction[0] += 4*elapsed
            if pressed[pygame.K_t]: light.direction[1] -= 4*elapsed
            if pressed[pygame.K_g]: light.direction[1] += 4*elapsed
            if pressed[pygame.K_r]: light.direction[2] -= 4*elapsed
            if pressed[pygame.K_y]: light.direction[2] += 4*elapsed"""
            
            move = 20*elapsed
            if pressed[pygame.K_w]:
                z = cmath.exp(complex(0, self.scene.camera.yaw))
                self.scene.camera.position[0] += z.imag * move
                self.scene.camera.position[1] += z.real * move
            if pressed[pygame.K_s]:
                z = cmath.exp(complex(0, self.scene.camera.yaw))
                self.scene.camera.position[0] -= z.imag * move
                self.scene.camera.position[1] -= z.real * move
            if pressed[pygame.K_d]: 
                z = cmath.exp(complex(0, self.scene.camera.yaw + cmath.pi/2))
                self.scene.camera.position[0] += z.imag * move
                self.scene.camera.position[1] += z.real * move
            if pressed[pygame.K_a]: 
                z = cmath.exp(complex(0, self.scene.camera.yaw + cmath.pi/2))
                self.scene.camera.position[0] -= z.imag * move
                self.scene.camera.position[1] -= z.real * move
            
            if pressed[pygame.K_q]: self.scene.camera.position[2] -= move
            if pressed[pygame.K_e]: self.scene.camera.position[2] += move
            
            if pressed[pygame.K_x]: self.scene.camera.rotate(-elapsed, 0, 0)
            if pressed[pygame.K_z]: self.scene.camera.rotate(elapsed, 0, 0)
            
            self.render()
            self.surface.blit(self.font.render("fps: %.2f | x: %.2f | y: %.2f | z: %.2f" % ((1.0/elapsed,) + tuple(self.scene.camera.position)), True, (255, 255, 255)), (50, 50))
        
            
            pygame.display.update()
            