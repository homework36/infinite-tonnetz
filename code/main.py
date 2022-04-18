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
from kivy.uix.image import Image

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
from tonnetz import Tonnetz
from audio_ctrl import AudioController
from player import Player

'''
Please make sure to quit ZIG Indicator on the computer, otherwise 
there would be the error " OSError: [Errno 48] Address already in use"

Please have ZIG SIM open all the time on the phone and stay on the tab "Start"
'''

rescale_const = Window.width / 2
class PhysBubble(InstructionGroup):
    def __init__(self, pos, r, color=(1,1,1), callback=None):
        super(PhysBubble, self).__init__()

        self.radius = r
        self.pos_x, self.pos_y = pos
        self.last_pos = pos
        self.vel_x, self.vel_y = 0., 0.

        self.add(PushMatrix())
        # self.add(Translate(*pos))
        self.angle = 60/(1+np.random.randint(10))
        self.add(Rotate(angle=self.angle))

        self.color = Color(rgb=color)
        self.add(self.color)

        self.circle = CEllipse(cpos=pos, csize=(2*r,2*r), segments = 40)
        self.circle.texture = Image(source='../img/icon.png').texture
        self.add(self.circle)
        self.callback = callback

        self.add(PopMatrix())
        self.circle.cpos = pos


    def set_accel(self, ax, ay):
        self.ax = ax
        self.ay = ay

    def get_last_pos(self):
        return self.last_pos

    def get_curr_pos(self):
        return [self.pos_x, self.pos_y]

    def on_resize(self, win_size):
        self.circle.csize = (2 * win_size[0] // 50,2 * win_size[0] // 50)

    def on_update(self, dt):
        self.add(PushMatrix())
        # self.add(Translate(*self.last_pos))
        self.add(Rotate(angle=self.angle))

        self.last_pos = [self.pos_x, self.pos_y]

        # integrate accel to get vel
        self.vel_x = self.ax * rescale_const
        self.vel_y = self.ay * rescale_const

        # integrate vel to get pos
        if self.radius <= self.pos_x + self.vel_x * dt <= Window.width - self.radius:
            self.pos_x += self.vel_x * dt
        elif self.radius > self.pos_x + self.vel_x * dt:
            self.pos_x = self.radius
            if self.callback:
                self.callback(self.vel_x * dt, None)

        else: # self.pos_x + self.vel_x * dt > Window.width - self.radius
            self.pos_x = Window.width - self.radius
            if self.callback:
                self.callback(self.vel_x * dt, None)

        if self.radius <= self.pos_y + self.vel_y * dt <= Window.height - self.radius:
            self.pos_y += self.vel_y * dt
        elif self.radius > self.pos_y + self.vel_y * dt:
            self.pos_y = self.radius
            if self.callback:
                self.callback(None, self.vel_y * dt)

        else: # self.pos_y + self.vel_y * dt > Window.height - self.radius
            self.pos_y = Window.height - self.radius
            if self.callback:
                self.callback(None, self.vel_y * dt)


        self.circle.cpos = np.array([self.pos_x, self.pos_y], dtype=float)

        self.add(PopMatrix())

        return True

# testing widget
class MainWidget(BaseWidget):
    def __init__(self, ip, port):
        super(MainWidget, self).__init__()
        width, height = Window.width, Window.height

        self.info = topleft_label()
        self.add_widget(self.info)

        self.reader = OSCReader(ip, int(port))
        self.curr_pos = self.reader.get_pos()['gravity']

        self.color = Color(1, 1, 1)
        self.canvas.add(self.color)
        self.tonnetz = Tonnetz(400)
        self.canvas.add(self.tonnetz)

        self.starship = PhysBubble(pos=(Window.width/2, Window.height/2), 
                                   r=Window.width/50, 
                                   color=(1,1,1),
                                   callback=self.tonnetz.on_boundary)

        # AnimGroup handles drawing, animation, and object lifetime management
        self.objects = AnimGroup()
        self.canvas.add(self.objects)
        self.objects.add(self.starship)

        self.audio_ctrl = AudioController()

        self.player = Player(self.starship, self.tonnetz, self.audio_ctrl)

    def on_update(self):
        self.player.on_update()
        self.audio_ctrl.on_update()

        self.update_pos()
        self.starship.set_accel(self.curr_pos['x'], self.curr_pos['y'])
        self.objects.on_update()

        self.info.text = f'{str(Window.mouse_pos)}\n'
        self.info.text += f'fps:{kivyClock.get_fps():.0f}\n'

        self.info.text += 'x: ' + str(round(self.curr_pos['x'], 4)) + '\n'
        self.info.text += 'y: ' + str(round(self.curr_pos['y'], 4)) + '\n'
        self.info.text += f'position: {self.starship.get_curr_pos()}\n'
        self.info.text += f'audio {"ON" if self.audio_ctrl.playing else "OFF"} (press p to toggle)'

    def on_resize(self,win_size):
        self.tonnetz.on_resize(win_size)
        resize_topleft_label(self.info)
        self.starship.on_resize(win_size)

    def update_pos(self):
        response = self.reader.get_pos()
        if response:
            self.curr_pos = response['gravity']
        # self.curr_z = self.curr_pos['z']        
    
    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'p':
            self.audio_ctrl.toggle()       


if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    assert len(sys.argv) >= 3, 'Need arguments ip and port'
    assert sys.argv[2].isdigit() and int(sys.argv[2]) >= 1024, 'port needs to be a number greater than or equal to 1024'
    run(MainWidget(sys.argv[1], sys.argv[2]))
