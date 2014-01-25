'''
Created on 21.12.2013

@author: ruckt
'''

from __future__ import print_function

import pyopencl as cl
import numpy
import math
import pygame
import time



def raytrace_chunk1(start_pos, direction, size, data):
    slope_y = direction[1]/float(direction[0])
    slope_z = direction[2]/float(direction[0])
    dir_x = 1 if direction[0] >= 0 else -1
    dir_y = 1 if direction[1] >= 0 else -1
    dir_z = 1 if direction[2] >= 0 else -1
    x = 0
    y = 0
    z = 0.99
    while True:
        next_y = slope_y * x + dir_y
        next_z = slope_z * x + dir_z
        while (dir_y > 0 and int(y) < int(next_y) or dir_y < 0 and int(y) > int(next_y)) and (y+start_pos[1]) > 0 and (y+start_pos[1]) < size and (z+start_pos[2]) > 0 and (z+start_pos[2]) < size:
            while (dir_z > 0 and int(z) < int(next_z) or dir_z < 0 and int(z) > int(next_z)) and (z+start_pos[2]) > 0 and (z+start_pos[2]) < size:
                data[int(x+start_pos[0]), int(y+start_pos[1]), int(z+start_pos[2])] = 1
                z += dir_z
            z -= dir_z
            y += dir_y
        print(x+start_pos[0],y+start_pos[1],z+start_pos[2])
        if not ((x+start_pos[0]) >= 0 and (x+start_pos[0]) < size and (y+start_pos[1]) >= 0 and (y+start_pos[1]) < size and (z+start_pos[2]) >= 0 and (z+start_pos[2]) < size): break
        y -= dir_y
        x += dir_x

epsilon = 0.00001
def raytrace_chunk2(start_pos, direction, size, data, intersection_points):
    voxel_width = 1
    x = int(start_pos[0])
    y = int(start_pos[1])
    z = int(start_pos[2])
    
    step_x, end_x, clamp_fx = (-1, -1, math.ceil) if direction[0] < 0 else (1, size+1, math.floor)
    step_y, end_y, clamp_fy = (-1, -1, math.ceil) if direction[1] < 0 else (1, size+1, math.floor)
    step_z, end_z, clamp_fz = (-1, -1, math.ceil) if direction[2] < 0 else (1, size+1, math.floor)
    
    if direction[0] < -epsilon or direction[0] > epsilon:
        t_max_x = (clamp_fx(start_pos[0] + step_x + epsilon) - start_pos[0]) / direction[0]
        delta_t_x = abs(voxel_width / direction[0])
    else:
        delta_t_x = t_max_x = 1e32 # something final and large
    
    if direction[1] < -epsilon or direction[1] > epsilon:
        t_max_y = (clamp_fy(start_pos[1] + step_y + epsilon) - start_pos[1]) / direction[1]
        delta_t_y = abs(voxel_width / direction[1])
    else:
        delta_t_y = t_max_y = 1e32 # something final and large
        
    if direction[2] < -epsilon or direction[2] > epsilon:
        t_max_z = (clamp_fz(start_pos[2] + step_z + epsilon) - start_pos[2]) / direction[2]
        delta_t_z = abs(voxel_width / direction[2])
    else:
        delta_t_z = t_max_z = 1e32 # something final and large
        
    while x != end_x and y != end_y and z != end_z:
        data[x, y, z] = 1
        t = max(list({t_max_x, t_max_y, t_max_z} - {1e32}))
        intersection_points[x, y, z]['loc'][0] = start_pos[0] + direction[0]*t
        intersection_points[x, y, z]['loc'][1] = start_pos[1] + direction[1]*t
        if t_max_x < t_max_y:
            if t_max_x < t_max_z:
                x += step_x
                t_max_x += delta_t_x
            else:
                z += step_z
                t_max_z += delta_t_z
        else:
            if t_max_y < t_max_z:
                y += step_y
                t_max_y += delta_t_y
            else:
                z += step_z
                t_max_z += delta_t_z
        
data = numpy.zeros((100, 100, 100), numpy.byte)
ipoints = numpy.zeros((100, 100, 100), numpy.dtype([('loc', numpy.float32, 2)]))
direction = (-1.5, -1.143, 0)
h = math.sqrt(sum(d*d for d in direction))
direction = [ d/h for d in direction ]
start = (10.1,10.1, 0)
raytrace_chunk2(start, direction, 20, data, ipoints)
#start = (start[0]-.99)*30, (start[1]-.99)*30
start = [ s*30 for s in start ]

display = pygame.display.set_mode((700, 700))

running = True
z = 0
while running:
    time.sleep(0.1)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    display.fill((0,0,0))
    pressed = pygame.key.get_pressed()
    
    if pressed[pygame.K_w] and z < 100:
        z += 1
    if pressed[pygame.K_s] and z > 0:
        z -= 1
        
    for x in range(0, 20):
        for y in range(0, 20):
            if data[x,y,z]:
                pygame.draw.rect(display, (255, 255, 255), [x*30, y*30, 30, 30])
                pygame.draw.rect(display, (0, 0, 255), [int(ipoints[x,y,z]['loc'][0]*30), int(ipoints[x,y,z]['loc'][1]*30), 3, 3])
    pygame.draw.line(display, (255, 0, 0), [start[0], start[1]], [1000*direction[0]+start[0], 1000*direction[1]+start[1]] )
    pygame.display.update()