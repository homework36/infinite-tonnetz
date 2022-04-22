from math import radians, ceil
from struct import calcsize
import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run, lookup
from imslib.gfxutil import topleft_label, resize_topleft_label, CEllipse, KFAnim, AnimGroup, CRectangle

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.label import Label
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate


from imslib.writer import AudioWriter
from imslib.audio import Audio
from imslib.clock import SimpleTempoMap, AudioScheduler, kTicksPerQuarter, quantize_tick_up
from imslib.core import BaseWidget, run
from imslib.gfxutil import topleft_label, resize_topleft_label, Cursor3D, AnimGroup, scale_point, CEllipse
from imslib.leap import getLeapInfo, getLeapFrame
from imslib.synth import Synth

from random import randint, random
import numpy as np
# from pyrsistent import b
from OSCReader import OSCReader
from random import randint
from helper_function import *


sq3 = np.sqrt(3)
class StarLine(InstructionGroup):
    '''Create lines that forms the tonnetz, passing the given point only! '''
    def __init__(self, point, trans_type='p'):
        super(StarLine, self).__init__()
        self.type = trans_type.lower()
        assert self.type in ['p','r','l']
        self.cx, self.cy = point
        self.end1, self.end2 = self.calc_line(self.type)
        self.line = Line(points=(self.end1[0],self.end1[1],self.end2[0],self.end2[1]))
        self.intersect = intersect
        self.width, self.height = Window.width, Window.height

        # if want to make line
        self.add(self.line)
    
    def update_line(self, dx, dy):
        self.cx += dx
        self.cy += dy
        self.end1, self.end2 = self.calc_line(self.type)
        self.line.points=(self.end1[0],self.end1[1],self.end2[0],self.end2[1])

    
    def calc_line(self, trans_type):
        width, height = Window.width, Window.height
        
        if self.type == 'p':
            end1 = [0,self.cy]
            end2 = [width,self.cy]
            return end1, end2
        else:
            dist_top = (height-self.cy)/sq3
            dist_bottom = self.cy/sq3
            if self.type == 'r':
                end_top = [self.cx-dist_top,height]
                end_bottom = [self.cx+dist_bottom,0]
            # self.type == 'l'
            else:
                end_top = [self.cx+dist_top,height]
                end_bottom = [self.cx-dist_bottom,0]
            return end_top, end_bottom
            
    def on_resize(self, win_size):
        self.width, self.height = win_size
        self.end1, self.end2 = self.calc_line(self.type)
        self.line.points = self.end1[0],self.end1[1],self.end2[0],self.end2[1]

    def on_update(self, dt):
        # if self.cx < -self.width or self.cx > self.width*2 or self.cy < -self.height or self.cy > self.height*2:
        #     return False
        # return True
        pass
        

    def check_cross(self, cur_pos, last_pos):
        '''pos: current position of main object
           last_pos: last position of main object'''
        print('checking!',self.type)
        if self.intersect(cur_pos, last_pos,self.end1,self.end2):
            return self.type
        else:
            return None

# create tonnetz
class Tonnetz(InstructionGroup):
    def __init__(self, seg_length, origin=[10,10]):
        '''create full tonnetz with a given seg_length and origin'''
        super(Tonnetz, self).__init__()
        self.width, self.height = Window.width, Window.height
        self.seg = seg_length
        self.seg_height = self.seg*sq3/2
        self.origin = np.array(origin)
        self.origin[0] %= self.seg * 2
        self.origin[1] %= self.seg_height * 2
        self.line_list_p = []
        self.line_list_rl = []
        self.line_list = []
        self.make_lines()
        self.last_origin = self.origin.copy()

    def make_lines(self, p=True, rl=True):
        # print('make lines',self.origin)
        if p:
            self.make_lines_p()
            
        if rl:
            self.make_lines_rl()
            
        self.line_list = self.line_list_p + self.line_list_rl
        


    def make_lines_p(self):
        # print('make lines p',self.origin)
        for line in self.line_list_p:
            if line in self.children:
                self.children.remove(line)

        self.line_list_p = []
        num_p_p = ceil((self.height-self.origin[1])/self.seg_height) + 2
        num_p_m = ceil(self.origin[1]/self.seg_height) + 2
        for i in range(int(num_p_p)):
            self.line_list_p.append(StarLine((self.origin[0],self.origin[1]+self.seg_height*i),'p'))
        for i in range(1,int(num_p_m)):
            self.line_list_p.append(StarLine((self.origin[0],self.origin[1]-self.seg_height*i),'p'))
        for line in self.line_list_p:
            self.add(line)

    
    def make_lines_rl(self):
        # print('make lines rl',self.origin)
        for line in self.line_list_rl:
            if line in self.children:
                self.children.remove(line)

        self.line_list_rl = []
        num_rl_p = ceil((self.width-self.origin[0])/self.seg) + 2
        num_rl_m = ceil(self.origin[0]/self.seg) + 2

        for trans in ['r','l']:
            for i in range(int(num_rl_p)):
                self.line_list_rl.append(StarLine((self.origin[0]+self.seg*i,self.origin[1]),trans))
            for i in range(1,int(num_rl_m)):
                self.line_list_rl.append(StarLine((self.origin[0]-self.seg*i,self.origin[1]),trans))
    
        num_rl_leftright = ceil(self.height/sq3/self.seg) + 2
        for i in range(num_rl_leftright):
            self.line_list_rl.append(StarLine((self.origin[0]-(i+num_rl_m)*self.seg,self.origin[1]),'l'))
            self.line_list_rl.append(StarLine((self.origin[0]+(i+num_rl_p)*self.seg,self.origin[1]),'r'))

        for line in self.line_list_rl:
            self.add(line)
    
    
    def on_resize(self, win_size):
        # remove first
        for line in self.children:
            self.children.remove(line)
        self.width, self.height = win_size
        self.make_lines()

    def on_boundary(self, dx, dy):
        # print('here', dx, dy)
        if dx or dy:
            self.last_origin = self.origin.copy()

        if dx:

            self.origin[0] += dx
            self.origin[0] %= self.seg * 2

        if dy:

            self.origin[1] += dy
            self.origin[1] %= self.seg_height * 2

        if dx or dy:
            # self.make_lines()
            print('boundary moving')
            print('total line',len(self.line_list))
            self.update_lines(self.origin-self.last_origin)
        
    def update_lines(self, diff_origin):
        for line in self.line_list:
            line.update_line(diff_origin[0],diff_origin[1])

    def on_update(self,dt):
        pass
        