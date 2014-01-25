'''
Created on 24.12.2013

@author: ruckt
'''

import pyopencl

def build_program(ctx, name):
    return pyopencl.Program(ctx, open("cl_programs/%s.cl" % name).read()).build([r"-I C:\Users\ruckt\workspace\game0x\cl_programs", "-cl-fast-relaxed-math"])
