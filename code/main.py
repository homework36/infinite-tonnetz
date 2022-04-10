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

'''
Please make sure to quit ZIG Indicator on the computer, otherwise 
there would be the error " OSError: [Errno 48] Address already in use"

Please have ZIG SIM open all the time on the phone and stay on the tab "Start"
'''


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
        self.line.points = self.ensd1[0],self.end1[1],self.end2[0],self.end2[1]

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

# create tonnetz
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
                self.line_list.append(StarLine((self.origin[0]-self.seg*i,self.origin[1]),trans))
    
        num_p = max(1,ceil(self.height/self.seg_height))
        for i in range(int(num_p+1)):
            self.line_list.append(StarLine((self.origin[0],self.origin[1]+self.seg_height*i),'p'))
            self.line_list.append(StarLine((self.origin[0],self.origin[1]-self.seg_height*i),'p'))
            if i%2 == 0:
                self.line_list.append(StarLine((self.origin[0],self.origin[1]+self.seg_height*i),'l'))
                self.line_list.append(StarLine((self.origin[0]+self.seg*num_rl,self.origin[1]+self.seg_height*i),'r'))
                self.line_list.append(StarLine((self.origin[0],self.origin[1]-self.seg_height*i),'l'))
                self.line_list.append(StarLine((self.origin[0]+self.seg*num_rl,self.origin[1]-self.seg_height*i),'r'))
        for line in self.line_list:
            self.add(line)
    
    def on_resize(self, win_size):
        # remove first
        for line in self.children:
            self.children.remove(line)
        self.width, self.height = win_size
        self.make_lines()

    def on_boundary(self, new_origin):
        self.origin = new_origin
        self.make_lines()

    def on_update(self,dt):
        pass



class PhysBubble(InstructionGroup):
    def __init__(self, pos, r, vel, color=(1,1,1)):
        super(PhysBubble, self).__init__()

        self.radius = r
        self.pos = np.array(pos, dtype=float)
        # self.vel = np.array((randint(-300, 300), 0), dtype=float)
        self.vel = np.array(vel)
        self.color = Color(rgb=color)
        self.add(self.color)

        self.circle = CEllipse(cpos=pos, csize=(2*r,2*r), segments = 40)
        self.add(self.circle)

        # self.on_update(0)

    def set_pos(self, ax, ay):
        self.pos[0] = (ax+1.)/2 * Window.width
        self.pos[1] = (ay+1.)/2 * Window.height
        self.circle.cpos = self.pos

    def get_pos(self):
        return self.pos


class AudioController(object):
    def __init__(self, song_path):
        super(AudioController, self).__init__()
        self.audio = Audio(2)
        self.mixer = Mixer()
        self.synth = Synth()

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(60)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.mixer)

        # value for init
        self.bass = NoteGenerator(60, 0, 'sine')
        self.third = NoteGenerator(60, 0, 'sine')
        self.fifth = NoteGenerator(60, 0, 'sine')

        # note parameters
        self.root_pitch = 60
        self.pitch = 60
        self.mode = 1
        self.vel = 80

        self.keys = ['C','C#','D','Eb','E','F','F#',\
                'G','Ab','A','Bb','B','C']
        self.modes = [' minor',' major']
        self.key = self.keys[(self.pitch-60)%12] + self.modes[self.mode]
        self.pitchlists = [(0, 2, 3, 5, 7, 8, 11, 12),\
            (0, 2, 4, 5, 7, 9, 11, 12)]

    # start / stop the song
    def toggle(self):
        pass



    # needed to update audio
    def on_update(self):
        self.audio.on_update()


# testing widget
class MainWidget(BaseWidget):
    def __init__(self, ip, port):
        super(MainWidget, self).__init__()
        width, height = Window.width, Window.height

        self.info = topleft_label()
        self.add_widget(self.info)


        self.reader = OSCReader(ip, int(port))
        self.curr_pos = self.reader.get_pos()['gravity']

        self.starship = PhysBubble((Window.width/2, Window.height/2), Window.width/50, (self.curr_pos['x'],self.curr_pos['y']))
        self.canvas.add(self.starship)

        self.mainobj = None
        # AnimGroup handles drawing, animation, and object lifetime management
        self.objects = AnimGroup()
        self.canvas.add(self.objects)
        
        # lines
        midpoint = (width/2,height/2)
        self.color = Color(1, 1, 1)
        self.canvas.add(self.color)
        self.tonnetz = Tonnetz(150,origin=(400,400))
        self.canvas.add(self.tonnetz)


    def on_update(self):
        self.update_pos()
        self.starship.set_pos(self.curr_pos['x'], self.curr_pos['y'])

        self.objects.on_update()
        self.info.text = f'{str(Window.mouse_pos)}\n'
        self.info.text += f'fps:{kivyClock.get_fps():.0f}\n'

        self.info.text += 'x: ' + str(round(self.curr_pos['x'], 4)) + '\n'
        self.info.text += 'y: ' + str(round(self.curr_pos['y'], 4)) + '\n'
        self.info.text += f'position: {self.starship.get_pos()}'

    def on_resize(self,win_size):
        self.tonnetz.on_resize(win_size)
        resize_topleft_label(self.info)


    def update_pos(self):
        self.last_pos = self.curr_pos
        self.curr_pos = self.reader.get_pos()['gravity']
        # self.curr_z = self.curr_pos['z']        
    
    def on_key_down(self, keycode, modifiers):
        pass
       


if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    assert len(sys.argv) == 3, 'Need arguments ip and port'
    assert sys.argv[2].isdigit() and int(sys.argv[2]) >= 1024, 'port needs to be a number greater than or equal to 1024'
    run(MainWidget(sys.argv[1], sys.argv[2]))
