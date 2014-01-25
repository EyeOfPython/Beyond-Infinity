'''
Created on 24.12.2013

@author: ruckt
'''
from __future__ import print_function
from render.scene import Scene
import pyopencl
import numpy
from PIL import  Image

import pygame
from transformations import quaternion_from_euler, quaternion_about_axis,\
    quaternion_multiply, quaternion_inverse, euler_from_quaternion
import time
import transformations
import cmath
import sys
from world.generate.diamondsquaregenerator import DiamondSquareGenerator
from world.generate.perlinnoisegenerator import PerlinNoiseGenerator

if __name__ == '__main__':
    platform = pyopencl.get_platforms()
    my_gpu_devices = platform[0].get_devices(device_type=pyopencl.device_type.CPU)
    ctx = pyopencl.Context(devices=my_gpu_devices)
    print(ctx.devices[0].max_compute_units)
    queue = pyopencl.CommandQueue(ctx)
    scene = Scene(ctx, queue)

    gen = DiamondSquareGenerator({ 'widthlog2': 8, 'roughness': 1, 'factor': 0.6 })
    #gen = PerlinNoiseGenerator({ 'widthlog2': 8, 'freq': 32, 'steps': 4, 'amplitude_factor': 1 })
    gen.generate(scene._chunk_array, ctx, queue, scene.raytrace_pgrm.write_height_map)
    
    sphere  = scene.create_object("sphere", position=(2,0,0), radius=2)
    #cube = scene.create_object("aacube", position=(0,0,0,0), width=6)
    scene.create_object("sphere", position=(-4,0,0), radius=1)
    scene.create_object("aacube", position=(-4,0,-5), width=1)
    scene.create_object("aacube", position=(-2, 0, 0), width=1.5)
    scene.create_object("aacube", position=(-2, 0, -5), width=1.5)
    scene.create_object("aacube", position=(-10, 3, -10), width=15)
    
    light   = scene.create_light("directional", direction=(1,1,1), color=(1,1,1))
    #scene.create_light("directional", direction=(1,1,1), color=(1,1,1))
    
    size = (800, 600)
    h_result_image = numpy.empty((size[0]*4, size[1]), dtype=numpy.ubyte)
    im_format = pyopencl.ImageFormat(pyopencl.channel_order.RGBA, pyopencl.channel_type.UNORM_INT8)
    d_result_image = pyopencl.Image(ctx, pyopencl.mem_flags.WRITE_ONLY, im_format, size)
    
    #scene.call_test()
    #print(scene.h_test_buffer[:10, :10, :10])
    print("render...")
    print([ c.voxel_offset for c in scene._chunk_array.layers[0].chunks ])
    #print(scene._chunk_array.chunk_buffer._h_buffer[:scene._chunk_array.dtype_chunk.itemsize*16].view(scene._chunk_array.dtype_chunk))
    
    scene._chunk_array.upload_buffers()
    scene.render(d_result_image, size)
    print(scene.h_test_buffer[0,0,:10])
    display = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    
    grab_mouse = True
    running = True
    pygame.font.init()
    font = pygame.font.SysFont("Garamond", 16)
    
    s = 0
    n = 0
    while running:
        elapsed = clock.tick(50)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                print("average fps:", 1.0/(s/n))
                print(n, "cycles")
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    grab_mouse = not grab_mouse
                    pygame.mouse.set_visible(not grab_mouse)
                    pygame.event.set_grab(grab_mouse)
        
        pressed = pygame.key.get_pressed()
        
        sun_speed = 4
        if pressed[pygame.K_f]: light.direction[0] -= 4*elapsed
        if pressed[pygame.K_h]: light.direction[0] += 4*elapsed
        if pressed[pygame.K_t]: light.direction[1] -= 4*elapsed
        if pressed[pygame.K_g]: light.direction[1] += 4*elapsed
        if pressed[pygame.K_r]: light.direction[2] -= 4*elapsed
        if pressed[pygame.K_y]: light.direction[2] += 4*elapsed
        
        move = 20*elapsed
        if pressed[pygame.K_w]:
            z = cmath.exp(complex(0, scene.camera.yaw))
            scene.camera.position[0] += z.imag * move
            scene.camera.position[1] += z.real * move
        if pressed[pygame.K_s]:
            z = cmath.exp(complex(0, scene.camera.yaw))
            scene.camera.position[0] -= z.imag * move
            scene.camera.position[1] -= z.real * move
        if pressed[pygame.K_d]: 
            z = cmath.exp(complex(0, scene.camera.yaw + cmath.pi/2))
            scene.camera.position[0] += z.imag * move
            scene.camera.position[1] += z.real * move
        if pressed[pygame.K_a]: 
            z = cmath.exp(complex(0, scene.camera.yaw + cmath.pi/2))
            scene.camera.position[0] -= z.imag * move
            scene.camera.position[1] -= z.real * move
        
        if pressed[pygame.K_q]: scene.camera.position[2] -= move
        if pressed[pygame.K_e]: scene.camera.position[2] += move
        
        if grab_mouse:
            rot_factor = 0.001
            rot_x, rot_y = pygame.mouse.get_rel()
            rot_x *= rot_factor
            rot_y *= rot_factor
            scene.camera.rotate(rot_x, rot_y, 0)
        
        scene.render(d_result_image, size)
        
        pyopencl.enqueue_copy(queue, h_result_image, d_result_image, origin=(0,0), region=size)
        img = pygame.image.fromstring(h_result_image.tostring(), size, 'RGBA')
        
        display.blit(img, (0,0))
        #Image.fromstring('RGBA', size, h_result_image.tostring()).show()
        display.blit(font.render("fps: %.2f | x: %.2f | y: %.2f | z: %.2f" % ((1.0/elapsed,) + tuple(scene.camera.position)), True, (255, 255, 255)), (50, 50))
        
        s += elapsed
        n += 1
        
        pygame.display.update()
        