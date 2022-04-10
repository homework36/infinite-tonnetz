from math import radians, ceil
from struct import calcsize
import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run, lookup
from imslib.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup, CRectangle

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.label import Label
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate

from random import randint, random
import numpy as np
from pyrsistent import b



# helper functions
# make triad within range C2-C6 (4 octaves)
def bound_triad(notes):
    for i in range(3):
        note = notes[i]
        if note < 36:
            notes[i] += 12
        elif note > 84:
            notes[i] -= 12
    return notes 
            

# calculate if two lines intersect
def ccw(A,B,C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

# Return true if line segments AB and CD intersect
def intersect(A,B,C,D):
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

# another way
def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

def intersect2(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    div = det(xdiff, ydiff)
    if div == 0:
       raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y
    
# transformation
def make_trans(mode,triad,key,trans='p',print=False):
    '''mode: 1 if major, 0 if minor
       triad: a list of three notes forming a triad
       key: current key '''
    trans_type = trans.lower()
    assert trans_type in ['p','r','l']
    assert len(triad) == 3

    # parallel transformation
    if trans_type == 'p':
        if mode == 1:
            triad[1] -= 1
            mode = 0
        else:
            triad[1] += 1
            mode = 1

    # relative transformation
    elif trans_type == 'r':
        if mode == 1:
            key -= 3
            mode = 0
            # move fifth up a tone
            triad[2] += 2
        else:
            key += 3
            mode = 1
            # move root down a tone
            triad[0] -= 2


    # leading-tone exchange
    else:
        if mode == 1:
            key += 4
            mode = 0
            # move root down a semitone
            triad[0] -= 1
        else:
            key -= 4
            mode = 1
            # move fifth up a semitone
            triad[2] += 1


    # make sure pitch is in the valid range 
    key = key % 12 + 60
    # rearrange triad
    temp = (triad - key)%12
    triad = np.array([x for _, x in sorted(zip(temp, triad))])

    # check if calculation is correct
    if mode == 1:
        calc_triad = key + np.array([0,4,7])
    else:
        calc_triad = key + np.array([0,3,7])
    if print:
        print('sorted triad:',triad)
        print('pitch triad:',calc_triad)
    assert np.array_equal(triad % 12, calc_triad % 12)

    return mode, bound_triad(triad), key

def calc_star(trans_type='p'):
    width, height = Window.width, Window.height
    pass

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

        # if want to make line
        self.add(self.line)
    
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
        pass

    def check_cross(self, main_obj):
        '''pos: current position of main object
           last_pos: last position of main object'''
        if self.intersect(main_obj.pos,main_obj.last_pos,self.end1,self.end2):
            mode, triad, key = main_obj.mode, main_obj.triad, main_obj.key
            new_mode, new_triad, new_key = make_trans(mode,triad,key,trans=self.type)
            main_obj.mode =  new_mode
            main_obj.triad = new_triad
            main_obj.key = new_key
        else:
            pass

# create static tonnetz
class Tonnetz(InstructionGroup):
    def __init__(self, seg_length, origin=(10,10)):
        '''create full tonnetz with a given seg_length and origin'''
        super(Tonnetz, self).__init__()
        self.width, self.height = Window.width, Window.height
        self.seg = seg_length
        self.seg_height = self.seg*sq3/2
        self.origin = origin
        self.make_lines()
    
    def make_lines(self):
        self.line_list = []
        num_rl = max(1,ceil(self.width/self.seg))
        for i in range(int(num_rl+1)):
            for trans in ['r','l']:
                self.line_list.append(StarLine((self.origin[0]+self.seg*i,self.origin[1]),trans))
    
        num_p = max(1,ceil(self.height/self.seg_height))
        for i in range(int(num_p+1)):
            self.line_list.append(StarLine((self.origin[0],self.origin[1]+self.seg_height*i),'p'))
            if i%2 == 0:
                self.line_list.append(StarLine((self.origin[0],self.origin[1]+self.seg_height*i),'l'))
                self.line_list.append(StarLine((self.origin[0]+self.seg*num_rl,self.origin[1]+self.seg_height*i),'r'))
        for line in self.line_list:
            self.add(line)
    
    def on_resize(self, win_size):
        # remove first
        for line in self.children:
            self.children.remove(line)
        self.width, self.height = win_size
        self.make_lines()

    def on_update(self,dt):
        pass

# for testing
class PhysBubble(InstructionGroup):
    def __init__(self, pos, r, color):
        super(PhysBubble, self).__init__()

        self.radius = r
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array((randint(-300, 300), 0), dtype=float)

        self.color = Color(*color)
        self.add(self.color)

        self.circle = CEllipse(cpos=pos, csize=(2*r,2*r), segments = 40)
        self.add(self.circle)

        self.mode = np.random.randint(0,2)
        self.key = np.random.randint(0,12) + 60
        self.triad = np.array([0,3,7]) + self.key
        self.triad[1] += self.mode
        self.lastpos = None
        
        self.on_update(0)

    def on_update(self, dt):
        # integrate accel to get vel
        self.vel += (0,-900) * dt

        # integrate vel to get pos
        self.pos += self.vel * dt

        self.lastpos = self.pos.copy()
        self.circle.cpos = self.pos

        return True



# testing widget
class TestWidget(BaseWidget):
    def __init__(self):
        super(TestWidget, self).__init__()
        width, height = Window.width, Window.height
        self.info = topleft_label()
        self.add_widget(self.info)
        self.mainobj = None
        # AnimGroup handles drawing, animation, and object lifetime management
        self.objects = AnimGroup()
        self.canvas.add(self.objects)
        
        # lines
        midpoint = (width/2,height/2)
        self.color = Color(1, 1, 1)
        self.canvas.add(self.color)
        self.tonnetz = Tonnetz(150)
        self.canvas.add(self.tonnetz)

    def on_update(self):
      
        self.objects.on_update()
        self.info.text = f'{str(Window.mouse_pos)}\n'
        self.info.text += f'fps:{kivyClock.get_fps():.0f}\n'

    def on_resize(self,win_size):
        self.tonnetz.on_resize(win_size)

        

if __name__ == "__main__":
    run(TestWidget())