'''
Created on 21.01.2014

@author: ruckt
'''
from render.display import Display

display = Display((800, 600))

if __name__ == '__main__':
    display.render_loop()