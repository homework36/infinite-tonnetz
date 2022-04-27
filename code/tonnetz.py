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
    def __init__(self, point, seg_length, trans_type='p',range=3):
        super(StarLine, self).__init__()
        self.type = trans_type.lower()
        assert self.type in ['p','r','l']
        self.cx, self.cy = point
        self.seg = seg_length
        self.seg_height = self.seg*sq3/2
        self.end1, self.end2 = self.calc_line()
        self.line = Line(points=(self.end1[0],self.end1[1],self.end2[0],self.end2[1]))
        self.intersect = intersect
        self.width, self.height = Window.width, Window.height
        self.range = range
        self.last_cross_pt = None

        self.add(self.line)
    
    def update_line(self, dx, dy):
        self.cx += dx
        self.cy += dy
        self.end1, self.end2 = self.calc_line()
        self.line.points=(self.end1[0],self.end1[1],self.end2[0],self.end2[1])

    
    def calc_line(self):
        width, height = Window.width, Window.height
        
        if self.type == 'p':
            end1 = [0,self.cy]
            end2 = [width,self.cy]
            return np.array(end1), np.array(end2)
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
            return np.array(end_top), np.array(end_bottom)
            
    def on_resize(self, win_size):
        self.width, self.height = win_size
        self.end1, self.end2 = self.calc_line()
        self.line.points = self.end1[0],self.end1[1],self.end2[0],self.end2[1]

    def on_update(self, dt):
        pass
        

    def check_cross(self, cur_pos, last_pos, moving=False):
        '''pos: current position of main object
           last_pos: last position of main object'''
        temp = np.array([self.cx,self.cy])
        # avoid duplicate crossing
        # if self.last_cross_pt is not None:
        #     if np.linalg.norm(temp-self.last_cross_pt) <= 5 and moving:
        #         print('preventing duplicate')
        #         return False

        if self.type == 'p':
            # print('checking!! obj last pos',last_pos,'obj cur pos',cur_pos)
            # print(self.type,'trans with line',self.cx,self.cy)
            if cur_pos[1] >= self.cy and last_pos[1] <= self.cy:
                if self.last_cross_pt is not None:
                    if np.linalg.norm(temp-self.last_cross_pt) <= 5 and moving:
                        return False
                self.last_cross_pt = temp
                return True
            elif cur_pos[1] <= self.cy and last_pos[1] >= self.cy:
                # print('checking!! obj last pos',last_pos,'obj cur pos',cur_pos)
                # print(self.type,'trans with line',self.cx,self.cy)
                if self.last_cross_pt is not None:
                    if np.linalg.norm(temp-self.last_cross_pt) <= 5 and moving:
                        return False
                self.last_cross_pt = temp
                return True
            else:
                self.last_cross_pt = None
                return False

        if self.intersect(cur_pos, last_pos, self.end1, self.end2):
            # print('checking! obj last pos',last_pos,'obj cur pos',cur_pos)
            # print(self.type,'trans with line',self.cx,self.cy)
            if self.last_cross_pt is not None:
                if np.linalg.norm(temp-self.last_cross_pt) <= 5 and moving:
                    return False
            self.last_cross_pt = temp
            return True
        else:
            self.last_cross_pt = None
            return False
        

        

# create tonnetz
class Tonnetz(InstructionGroup):
    def __init__(self, seg_length, origin=[10,10], callback=None, obj=None):
        '''create full tonnetz with a given seg_length and origin'''
        super(Tonnetz, self).__init__()
        self.width, self.height = Window.width, Window.height
        self.seg = seg_length
        self.seg_height = self.seg*sq3/2
        self.origin = np.array(origin)
        self.origin[0] %= self.seg * 2
        self.origin[1] %= self.seg_height * 2
        self.line_list_p = []
        self.line_list_r = []
        self.line_list_l = []
        self.line_list = []
        self.make_lines()
        self.last_origin = self.origin.copy()
        self.callback = callback
        self.obj = obj
        self.in_boundary = False

    def import_obj(self,obj):
        self.obj = obj

    def make_lines(self, p=True, rl=True):
        # print('make lines',self.origin)
        if p:
            self.make_lines_p()
            
        if rl:
            self.make_lines_rl()
            
        self.line_list = self.line_list_p + self.line_list_r + self.line_list_l
        
    def within_boundary(self,truth_val):
        self.in_boundary = truth_val

    def make_lines_p(self):
        for line in self.line_list_p:
            if line in self.children:
                self.children.remove(line)

        self.line_list_p = []
        num_p_p = ceil((self.height-self.origin[1])/self.seg_height) + 2
        num_p_m = ceil(self.origin[1]/self.seg_height) + 2
        for i in range(int(num_p_p)):
            self.line_list_p.append(StarLine((self.origin[0],self.origin[1]+self.seg_height*i),self.seg,'p'))
        for i in range(1,int(num_p_m)):
            self.line_list_p.append(StarLine((self.origin[0],self.origin[1]-self.seg_height*i),self.seg,'p'))
        for line in self.line_list_p:
            self.add(line)

    
    def make_lines_rl(self):
        for line in self.line_list_r:
            if line in self.children:
                self.children.remove(line)
        for line in self.line_list_l:
            if line in self.children:
                self.children.remove(line)

        self.line_list_r = []
        self.line_list_l = []
        num_rl_p = ceil((self.width-self.origin[0])/self.seg) + 2
        num_rl_m = ceil(self.origin[0]/self.seg) + 2

        for i in range(int(num_rl_p)):
            self.line_list_r.append(StarLine((self.origin[0]+self.seg*i,self.origin[1]),self.seg,'r'))
            self.line_list_l.append(StarLine((self.origin[0]+self.seg*i,self.origin[1]),self.seg,'l'))
        for i in range(1,int(num_rl_m)):
            self.line_list_r.append(StarLine((self.origin[0]-self.seg*i,self.origin[1]),self.seg,'r'))
            self.line_list_l.append(StarLine((self.origin[0]-self.seg*i,self.origin[1]),self.seg,'l'))
    
        num_rl_leftright = ceil(self.height/sq3/self.seg) + 2
        for i in range(num_rl_leftright):
            self.line_list_l.append(StarLine((self.origin[0]-(i+num_rl_m)*self.seg,self.origin[1]),self.seg,'l'))
            self.line_list_r.append(StarLine((self.origin[0]+(i+num_rl_p)*self.seg,self.origin[1]),self.seg,'r'))

        for line in self.line_list_r:
            self.add(line)

        for line in self.line_list_l:
            self.add(line)
    
    
    def on_resize(self, win_size):
        # remove first
        for line in self.children:
            self.children.remove(line)
        # rescale  segment length
        old_width = self.width
        self.width, self.height = win_size
        self.seg *= self.width/old_width
        self.seg_height = self.seg*sq3/2
        self.origin[0] %= self.seg * 2
        self.origin[1] %= self.seg_height * 2
        self.last_origin = self.origin.copy()
        self.make_lines()

    def on_boundary(self, dx, dy):
        x_adj = 0
        y_adj = 0
        # print('here', dx, dy)
        if dx or dy:
            self.last_origin = self.origin.copy()

        if dx:
            x_adj = dx
            self.origin[0] += dx
            self.origin[0] %= self.seg * 2
            
        if dy:
            y_adj = dy
            self.origin[1] += dy
            self.origin[1] %= self.seg_height * 2

        if dx or dy:
            # print()
            # print('boundary moving')
            # print('adj',x_adj, y_adj)
            self.check_lines(dx=-x_adj,dy=-y_adj)
            self.update_lines(self.origin-self.last_origin)
            # print('end of boundary checking\n')
        
    def update_lines(self, diff_origin):
        for line in self.line_list:
            line.update_line(diff_origin[0],diff_origin[1])

    def on_update(self):
        if self.in_boundary:
            self.check_lines()
        else:
            pass

    def check_lines(self,dx=0,dy=0):
        if self.obj is not None and self.callback is not None:
            last_pos = self.obj.get_last_pos()
            cur_pos = self.obj.get_curr_pos()
            adjust_pos = [cur_pos[0]+dx,cur_pos[1]+dy]
            for line in self.line_list_p:
                if line.check_cross(adjust_pos, last_pos, True):
                    self.callback('p')
    
            for line in self.line_list_r:
                if line.check_cross(adjust_pos, last_pos, True):
                    self.callback('r')

            for line in self.line_list_l:
                if line.check_cross(adjust_pos, last_pos, True):
                    self.callback('l')
    
    def modify_seq_length(self,val):
        temp_seg = self.seg + val
        self.seg = max(400,min(self.width/1.5,temp_seg))
        self.seg_height = self.seg*sq3/2
        self.origin[0] %= self.seg * 2
        self.origin[1] %= self.seg_height * 2
        self.make_lines()

    
        