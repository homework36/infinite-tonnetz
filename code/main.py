import sys, os
sys.path.insert(0, os.path.abspath('..'))

from OSCReader import OSCReader
from imslib.core import BaseWidget, run
from imslib.gfxutil import topleft_label, resize_topleft_label, Cursor3D, AnimGroup, KFAnim, scale_point, CEllipse
from imslib.synth import Synth
from imslib.audio import Audio


from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.graphics.instructions import InstructionGroup
from kivy.clock import Clock as kivyClock
import numpy as np
from random import randint

'''
Please make sure to quit ZIG Indicator on the computer, otherwise 
there would be the error " OSError: [Errno 48] Address already in use"

Please have ZIG SIM open all the time on the phone and stay on the tab "Start"
'''

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

class MainWidget(BaseWidget):
    def __init__(self, ip, port):
        super(MainWidget, self).__init__()

        self.label = topleft_label()
        self.add_widget(self.label)

        self.reader = OSCReader(ip, int(port))
        self.curr_pos = self.reader.get_pos()['gravity']

        self.starship = PhysBubble((Window.width/2, Window.height/2), 50, (self.curr_pos['x'],self.curr_pos['y']))
        self.canvas.add(self.starship)

    # will get called when the window size changes. Pass this information down
    # to Harp so that you appropriately resize it and its subcomponents.
    def on_resize(self, win_size):
        # update self.label
        resize_topleft_label(self.label)

    def on_update(self):
        self.update_pos()
        self.starship.set_pos(self.curr_pos['x'], self.curr_pos['y'])
        self.label.text = 'x: ' + str(round(self.curr_pos['x'], 4)) + '\n'
        self.label.text += 'y: ' + str(round(self.curr_pos['y'], 4)) + '\n'
        self.label.text += f'position: {self.starship.get_pos()}'
    def update_pos(self):
        self.last_pos = self.curr_pos
        self.curr_pos = self.reader.get_pos()['gravity']

        # self.curr_z = self.curr_pos['z']

if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    assert len(sys.argv) == 3, 'Need arguments ip and port'
    assert sys.argv[2].isdigit() and int(sys.argv[2]) >= 1024, 'port needs to be a number greater than or equal to 1024'
    run(MainWidget(sys.argv[1], sys.argv[2]))
