'''
Created on 24.12.2013

@author: ruckt
'''
import numpy
from render.renderobject.camera import Camera

import pyopencl
from render.renderbuffer import RenderBuffer
from render.renderobject.renderobject import RenderObject
from render.program import build_program
from render.voxel.chunkarray import ChunkArray
from render.voxel.voxeldata import VoxelData
import random

class Scene(object):
    '''
    Stores a list of render objects and allocates them. 
    '''

    reference_t = numpy.dtype([ ('obj_type', numpy.short), ('obj_offset', numpy.uint32) ])
    
    def __init__(self, clctx, queue):
        '''
        Constructor
        '''
        self.clctx = clctx
        self.queue = queue
        
        # stores the objects of the scene. (data and ref)
        self.objects = set() 
        self.lights = set()
        
        # stores the (byte)data of the objects
        self._obj_buffer     = RenderBuffer(clctx, queue, 2**16, 2**15)
        
        # stores the references on the (byte)data. 
        # these will be raytraced in the render process.
        self._obj_references = RenderBuffer(clctx, queue, 2**15, 2**14)
        
        # couldn't help myself but put this in a buffer... maybe sometimes we need multiple cameras.
        self._cam_buffer     = RenderBuffer(clctx, queue, Camera.dtype.itemsize, Camera.dtype.itemsize)
        
        # The lights in the scene. These are referenced by _light_references
        self._light_buffer     = RenderBuffer(clctx, queue, 2**9, 2**7)
        self._light_references = RenderBuffer(clctx, queue, 2**8, 2**6)
        
        # This camera will be passed to the render process
        self.camera = self.create_camera(position=(-2,-2,30), orientation=(1,0,0,0), bounds=(-2,2,1.5,-1.5), warp=4)
        
        self.raytrace_pgrm = build_program(clctx, "raytrace")
        self.raytrace = self.raytrace_pgrm.raytrace
        self.raytrace.set_scalar_arg_dtypes([None, None, None, numpy.uint32, None, None, None, None])
        self._chunk_array = ChunkArray(self.clctx, self.queue, (0, 1) , self.raytrace_pgrm.init_chunk_array)
        
        """self._chunk_array.allocate_layer(0, x_bounds=(0, 2), y_bounds=(0, 2))
        self._chunk_array.allocate_layer(1, x_bounds=(0, 2), y_bounds=(0, 2))
        self._chunk_array.allocate_chunk(0, 0, 0, level=0)
        self._chunk_array.allocate_chunk(1, 0, 0, level=1)
        self._chunk_array.allocate_chunk(0, 0, 1, level=0)
        self._chunk_array.allocate_chunk(1, 0, 1, level=0)
        self._chunk_array.allocate_chunk(0, 1, 0, level=0)
        self._chunk_array.allocate_chunk(1, 1, 0, level=0)
        self._chunk_array.allocate_chunk(0, 1, 1, level=0)
        self._chunk_array.allocate_chunk(1, 1, 1, level=0)
        
        self._chunk_array.get_layer(0).chunk_offset = 0
        chunk = self._chunk_array.get_chunk(0, 0, 0)
        chunk.voxel_data[:] = numpy.array([(random.randint(0,2), (0,0,0), (-1,-1,-1)) for i in range(32**3)], dtype=VoxelData.test_dtype)
        
        chunk = self._chunk_array.get_chunk(1, 0, 0)
        chunk.voxel_data[:] = numpy.array([(i % 2, (0,0,0), (-1,-1,-1)) for i in range(16**3)], dtype=VoxelData.test_dtype)
        
        chunk = self._chunk_array.get_chunk(0, 0, 1)
        chunk.voxel_data[:] = numpy.array([(random.randint(0,2), (0,0,0), (-1,-1,-1)) for i in range(32**3)], dtype=VoxelData.test_dtype)
        
        self._chunk_array.get_chunk(1, 0, 1).voxel_data[:] = chunk.voxel_data
        
        
        self._chunk_array.get_chunk(0, 1, 0).voxel_data[:] = chunk.voxel_data
        self._chunk_array.get_chunk(1, 1, 0).voxel_data[:] = chunk.voxel_data
        self._chunk_array.get_chunk(0, 1, 1).voxel_data[:] = chunk.voxel_data
        self._chunk_array.get_chunk(1, 1, 1).voxel_data[:] = chunk.voxel_data"""
        
        self.h_test_buffer = numpy.zeros((32,32,32), dtype=numpy.uint32)
        self.d_test_buffer = pyopencl.Buffer(clctx, pyopencl.mem_flags.READ_WRITE | pyopencl.mem_flags.COPY_HOST_PTR, hostbuf=self.h_test_buffer)
        
    def _create_buffer_object(self, buff, cls, **kwargs):
        dtype = cls.dtype
        data = None
        
        if dtype is not None:
            data, offset = buff.allocate_data(dtype)
            
        obj = cls(data)
        for k,v in kwargs.items():
            obj.__setattr__(k, v)
        return obj, offset
        
    def create_reference(self, ref_buffer, obj_type, obj_offset):
        ref, offset = ref_buffer.allocate_data(self.reference_t)
        ref['obj_type']   = obj_type
        ref['obj_offset'] = obj_offset
        return ref
        
    def create_object(self, name, **kwargs):
        cls = RenderObject._render_object_classes[name]
        obj, offset = self._create_buffer_object(self._obj_buffer, cls, **kwargs)
        
        ref = self.create_reference(self._obj_references, cls.type_id, offset)
        obj.data_ref = ref
        
        self.objects.add(obj)
        return obj
    
    def create_camera(self, **kwargs):
        cam, offset = self._create_buffer_object(self._cam_buffer, Camera, **kwargs)
        return cam
    
    def create_light(self, name, **kwargs):
        cls = RenderObject._light_classes[name]
        light, offset = self._create_buffer_object(self._light_buffer, cls, **kwargs)
        
        ref = self.create_reference(self._light_references, cls.type_id, offset)
        light.data_ref = ref
        return light
    
    def call_test(self):
        self.raytrace_pgrm.test_kernel(self.queue, (1,), None, self.d_test_buffer)
        pyopencl.enqueue_copy(self.queue, self.h_test_buffer, self.d_test_buffer)
    
    def render(self, img, size):
        self._obj_buffer.upload_buffer()
        self._obj_references.upload_buffer()
        self._cam_buffer.upload_buffer()
        self._light_buffer.upload_buffer()
        self._light_references.upload_buffer()
        
        """self.raytrace(self.queue, size, None,
                        img, self._cam_buffer._d_buffer, 
                             self._obj_references.n_elements,
                             self._obj_references._d_buffer,
                             self._obj_buffer._d_buffer,
                             self._light_references.n_elements,
                             self._light_references._d_buffer,
                             self._light_buffer._d_buffer,
                             self.d_test_buffer)"""
                             
        self.raytrace(self.queue, size, (16,8), img, self._cam_buffer._d_buffer, 
                             self._chunk_array.array_buffer._d_buffer,
                             self._light_references.n_elements,
                             self._light_references._d_buffer,
                             self._light_buffer._d_buffer,
                             self.d_test_buffer,
                             self._chunk_array.voxel_data.level_buffers[0]._d_buffer)
        pyopencl.enqueue_copy(self.queue, self.h_test_buffer, self.d_test_buffer)
        #pyopencl.enqueue_copy(self.queue, self._chunk_array.array_buffer._h_buffer, self._chunk_array.array_buffer._d_buffer)
        