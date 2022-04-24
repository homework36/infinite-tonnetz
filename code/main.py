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


from random import randint, random
import numpy as np
# from pyrsistent import b
from OSCReader import OSCReader
from random import randint
from tonnetz import Tonnetz
from audio_ctrl import AudioController
from player import Player
from objects import PhysBubble

'''
Please make sure to quit ZIG Indicator on the computer, otherwise 
there would be the error " OSError: [Errno 48] Address already in use"

Please have ZIG SIM open all the time on the phone and stay on the tab "Start"
'''

# mainwidget
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


        self.audio_ctrl = AudioController()
        self.tonnetz = Tonnetz(600,callback=self.audio_ctrl.make_prl)
        self.canvas.add(self.tonnetz)
        self.starship = PhysBubble(pos=(Window.width/2, Window.height/2), 
                                   r=Window.width/50, 
                                   color=(1,1,1),
                                   callback=self.tonnetz.on_boundary,
                                   in_boundary=self.tonnetz.within_boundary)
        self.tonnetz.import_obj(self.starship)
        
        

        # AnimGroup handles drawing, animation, and object lifetime management
        self.objects = AnimGroup()
        self.canvas.add(self.objects)
        self.objects.add(self.starship)

        
        self.player = Player(self.starship, self.tonnetz, self.audio_ctrl)

    def on_update(self):
        # self.player.on_update()
        self.audio_ctrl.on_update()

        self.update_pos()
        self.tonnetz.on_update()
        self.starship.set_accel(self.curr_pos['x'], self.curr_pos['y'])
        self.objects.on_update()

        self.info.text = f'fps:{kivyClock.get_fps():.0f}\n'

        self.info.text += 'x: ' + str(round(self.curr_pos['x'], 4)) + '\n'
        self.info.text += 'y: ' + str(round(self.curr_pos['y'], 4)) + '\n'
        self.info.text += f'position: {self.starship.get_curr_pos()}\n'
        self.info.text += f'audio {"ON" if self.audio_ctrl.playing else "OFF"} (press p to toggle)\n'
        self.info.text += f'{self.starship.rotate.angle}'
        
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

        if keycode[1] == 'up':
            self.tonnetz.modify_seq_length(10.)    
        
        if keycode[1] == 'down':
            self.tonnetz.modify_seq_length(-10.)    

        if keycode[1] == 'c':
            self.audio_ctrl.play_chromscale()
        
        if keycode[1] == 's':
            self.audio_ctrl.toggle_seventh()

if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    assert len(sys.argv) >= 3, 'Need arguments ip and port'
    assert sys.argv[2].isdigit() and int(sys.argv[2]) >= 1024, 'port needs to be a number greater than or equal to 1024'
    run(MainWidget(sys.argv[1], sys.argv[2]))
