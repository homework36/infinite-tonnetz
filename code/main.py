import sys, os
sys.path.insert(0, os.path.abspath('..'))
from objects import *
from player import Player
from audio_ctrl import AudioController
from tonnetz import Tonnetz
from OSCReader import OSCReader

import numpy as np
from imslib.gfxutil import topleft_label, resize_topleft_label, Cursor3D, AnimGroup, scale_point, CEllipse
from imslib.core import BaseWidget, run

from kivy.clock import Clock as kivyClock
from kivy.core.window import Window


'''
Please make sure to quit ZIG Indicator on the computer, otherwise 
there would be the error " OSError: [Errno 48] Address already in use"

Please have ZIG SIM open all the time on the phone and stay on the tab "Start"
'''

# mainwidget
class MainWidget(BaseWidget):
    def __init__(self, ip, port):
        super(MainWidget, self).__init__()
        Window.clearcolor = (0.062, 0.023, 0.219, 0.6)

        self.info = topleft_label()
        self.add_widget(self.info)

        self.reader = OSCReader(ip, int(port))
        self.curr_pos = self.reader.get_pos()['gravity']

        self.audio_ctrl = AudioController()
        self.tonnetz = Tonnetz(600, callback=self.audio_ctrl.make_prl)
        self.canvas.add(self.tonnetz)
        self.starship = PhysBubble(pos=(Window.width/2, Window.height/2),
                                   r=Window.width/25,
                                   color=(1, 1, 1),
                                   callback=self.tonnetz.on_boundary,
                                   in_boundary=self.tonnetz.within_boundary)
        self.tonnetz.import_obj(self.starship)

        # AnimGroup handles drawing, animation, and object lifetime management
        self.objects = AnimGroup()
        self.canvas.add(self.objects)
        self.objects.add(self.starship)

        self.add_space_objects()
        self.player = Player(self.starship, self.tonnetz,
                             self.audio_ctrl, self.space_objects)

    def add_space_objects(self):
        planet_weights = [0.1, 0.3, 0.3, 0.3]
        planet_choices = ['special_planet', 'planet1', 'planet2', 'planet3']

        self.space_objects = []

        for _ in range(5):  # create planets
            rand_planet = np.random.choice(planet_choices, p=planet_weights)
            self.space_objects.append(SpaceObject(np.random.randint(
                30, 60), '../img/'+rand_planet+'.png', 'planet'))

        for _ in range(5):  # create stars
            self.space_objects.append(SpaceObject(
                np.random.randint(10, 20), '../img/star.png', 'star'))

        for _ in range(70):  # create round stars
            self.space_objects.append(SpaceObject(
                np.random.randint(4, 8), '../img/star2.png', 'star2'))

        # create astronaut
        self.space_objects.append(SpaceObject(
            50, '../img/astronaut.png', 'astronaut'))

        for obj in self.space_objects:
            self.objects.add(obj)  # to be changed to anim_group

    def on_update(self):
        self.update_pos()
        self.tonnetz.on_update()
        self.starship.set_accel(self.curr_pos['x'], self.curr_pos['y'])

        self.audio_ctrl.on_update()
        self.player.on_update()
        self.objects.on_update()  # anim group

        self.info.text = f'fps:{kivyClock.get_fps():.0f}\n'

        self.info.text += 'x: ' + str(round(self.curr_pos['x'], 4)) + '\n'
        self.info.text += 'y: ' + str(round(self.curr_pos['y'], 4)) + '\n'
        self.info.text += f'position: {self.starship.get_curr_pos()}\n'
        self.info.text += f'audio {"ON" if self.audio_ctrl.playing else "OFF"} (press p to toggle)\n'
        # self.info.text += f'{self.starship.rotate.angle}'
        self.info.text += f'{self.objects.size()}'

    def on_resize(self, win_size):
        self.tonnetz.on_resize(win_size)
        resize_topleft_label(self.info)
        self.starship.on_resize(win_size)
        for obj in self.space_objects:
            obj.on_resize(win_size)

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
        
        if keycode[1] == 'l':
            self.audio_ctrl.toggle_sidepiece()


if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    assert len(sys.argv) >= 3, 'Need arguments ip and port'
    assert sys.argv[2].isdigit() and int(
        sys.argv[2]) >= 1024, 'port needs to be a number greater than or equal to 1024'
    run(MainWidget(sys.argv[1], sys.argv[2]))
