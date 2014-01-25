'''
Created on 25.12.2013

@author: ruckt
'''
import numpy
import pyopencl

class RenderBuffer(object):
    '''
    Stores data on the host and device, which will be used in the render process. 
    Grows dynamically and must be updated to be syncronized with the device.
    Not used for voxel data.
    '''

    def __init__(self, ctx, queue, size, grow_rate):
        '''
        Constructor
        '''
        self.ctx       = ctx
        self.queue     = queue
        
        self._offset   = 0
        self._h_buffer = numpy.ones(size, dtype=numpy.ubyte)*66
        self._d_buffer = pyopencl.Buffer(ctx, pyopencl.mem_flags.READ_ONLY, size)
        
        self.grow_rate = grow_rate
        self.n_elements= 0
        
    def allocate_data(self, dtype):
        new_offset = self._offset + dtype.itemsize
        if new_offset > self._h_buffer.size - 1:
            self._h_buffer.resize(self._h_buffer.size + self.grow_rate, refcheck=False)
            del self._d_buffer
            self._d_buffer = pyopencl.Buffer(self.ctx, pyopencl.mem_flags.READ_ONLY, self._h_buffer.size)
        data = self._h_buffer[self._offset:new_offset]
        offset = self._offset
        self._offset = new_offset
        self.n_elements += 1
        view = data.view(dtype)
        return view[0], offset
    
    def allocate_array(self, number, dtype):
        new_offset = self._offset + number*dtype.itemsize
        if new_offset > self._h_buffer.size - 1:
            self._h_buffer.resize(self._h_buffer.size + self.grow_rate, refcheck=False)
            del self._d_buffer
            self._d_buffer = pyopencl.Buffer(self.ctx, pyopencl.mem_flags.READ_ONLY, self._h_buffer.size)
        arr = self._h_buffer[self._offset:new_offset]
        offset = self._offset
        self._offset = new_offset
        self.n_elements += number
        arr = arr.view(dtype)
        return arr, offset
    
    def upload_buffer(self):
        pyopencl.enqueue_copy(self.queue, self._d_buffer, self._h_buffer)
        
    def download_buffer(self):
        pyopencl.enqueue_copy(self.queue, self._h_buffer, self._d_buffer)
        