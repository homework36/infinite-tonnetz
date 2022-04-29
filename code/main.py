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
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from sys import platform
import subprocess

'''
Please make sure to quit ZIG Indicator on the computer, otherwise 
there would be the error " OSError: [Errno 48] Address already in use"
Please have ZIG SIM open all the time on the phone and stay on the tab "Start"
'''

class StartScreen(RelativeLayout):
    def __init__(self, callback_fn, ip, moving_objs, static_objs):
        super(StartScreen, self).__init__()
        self.w, self.h = Window.width, Window.height
        self.start_game = callback_fn
        if not ip:
            self.ip_text = 'Enter IP'
        else:
            self.ip_text = ip

        # optional: comment out to have a clear background
        for obj in moving_objs:
            self.canvas.add(obj)
        for obj in static_objs:
            self.canvas.add(obj)

        # add background
        with self.canvas.before:
            self.background = CRectangle(cpos=(self.w/2, self.h/2), 
                                         csize=(self.w, self.h), 
                                         color=Color(rgb=(0.062, 0.023, 0.219, 0.6)))

        # add title
        self.title_label = Label(text='[color=e3dfe0]Infinite Tonnetz[/color]',
                                 size_hint=(.6, .1),
                                 pos_hint={'x': .2, 'y': .75},
                                 font_name='../materials/PixelOperator-Bold.ttf',
                                 markup=True)
        self.add_widget(self.title_label)

        # add ip label
        self.ip_label = Label(text='Enter IP',
                                 size_hint=(.3, .08),
                                 pos_hint={'x': .15, 'y': .5},
                                 font_name='../materials/PixelOperator-Bold.ttf',
                                 markup=True)
        self.add_widget(self.ip_label)

        # add pre-filled ip entry
        self.ip_input = TextInput(size_hint=(.3, .08),
                                  font_name='../materials/PixelOperator-Bold.ttf',
                                  pos_hint={'x': .15, 'y': .4},
                                  padding=(0, self.height/4, 0, 0),
                                  multiline=False)
        if not ip:
            self.ip_input.hint_text = 'Your IP'
        else:
            self.ip_input.text = ip
        self.add_widget(self.ip_input)

        # add port label
        self.port_label = Label(text='Enter Port',
                                 size_hint=(.3, .08),
                                 pos_hint={'x': .55, 'y': .5},
                                 font_name='../materials/PixelOperator-Bold.ttf',
                                 markup=True)
        self.add_widget(self.port_label)

        # add port entry
        self.port_input = TextInput(size_hint=(.3, .08),
                                    font_name='../materials/PixelOperator-Bold.ttf',
                                    pos_hint={'x': .55, 'y': .4},
                                    # halign='center',
                                    padding=(0, self.height/3.5, 0, 0),
                                    hint_text='greater than 1024',
                                    multiline=False)
        self.add_widget(self.port_input)

        # add start button
        self.start_button = Button(text=f'Start Exploration',
                                        # font_size = self.width/2,
                                        size_hint=(.4, .1),
                                        font_name='../materials/PixelOperator-Bold.ttf',
                                        pos_hint={'x': .3, 'y': .25},
                                        color=(1, 1, 1, 1),
                                        background_color=(0, .7, 1.))
        self.start_button.bind(on_press=lambda _: self.start_game_check())
        self.add_widget(self.start_button)

    def start_game_check(self):
        if self.ip_input.text == '' and self.port_input.text == '':
            self.ip_input.hint_text = 'IP cannot be empty'
            self.port_input.hint_text = 'Port cannot be empty'
            return
        elif self.ip_input.text == '':
            self.ip_input.hint_text = 'IP cannot be empty'
            return
        elif self.port_input.text == '':
            self.port_input.hint_text = 'Port cannot be empty'
            return
            
        self.start_game(self.ip_input.text, self.port_input.text)

    def on_resize(self, win_size):
        self.w, self.h = win_size

        self.background.cpos=(self.w/2, self.h/2)
        self.background.csize = (self.w, self.h)

        self.title_label.font_size = self.width/10
        self.start_button.font_size = self.width/25

        self.ip_label.font_size = self.width/35
        self.port_label.font_size = self.width/35

        self.ip_input.font_size = self.width/50
        self.port_input.font_size = self.width/50

# mainwidget
class MainWidget(BaseWidget):
    def __init__(self, ip=None):
        super(MainWidget, self).__init__()
        Window.clearcolor = (0.062, 0.023, 0.219, 0.6)

        self.info = topleft_label()
        self.add_widget(self.info)

        self.reader = None

        self.audio_ctrl = AudioController()
        self.tonnetz = Tonnetz(600, callback=self.audio_ctrl.make_prl)
        self.canvas.add(self.tonnetz)

        self.starship = PhysBubble(pos=(Window.width/2, Window.height/2),
                                   r=Window.width/25,
                                   color=(1, 1, 1),
                                   callback=self.tonnetz.on_boundary,
                                   in_boundary=self.tonnetz.check_lines)
        # self.tonnetz.import_obj(self.starship)

        # AnimGroup handles drawing, animation, and object lifetime management
        self.objects = AnimGroup()
        self.canvas.add(self.objects)

        self.add_space_objects()

        self.player = Player(self.starship, self.tonnetz,
                             self.audio_ctrl, self.space_objects, self.static_objects)


        self.ip_address = self.get_ip(ip)
        self.start_screen = StartScreen(self.start_game, 
                                        self.ip_address,
                                        self.objects.children, 
                                        self.static_objects)
        
        with self.canvas.before:
            self.add_widget(self.start_screen, 0)
        
    def get_ip(self, ip_arg=''):
        if platform == 'darwin': # macOS
            command = 'ipconfig getifaddr en0'
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()
            if error:
                return ''
            return output.decode('utf-8')

        elif platform == 'Windows': # Windows
            command =  "for /f \"tokens=2 delims=[]\" %a in ('ping -n 1 -4 \"%computername%\"') do @echo %a"
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()
            if error:
                return ''
            return output.decode('utf-8')

        else: # other OS 
            return ip_arg

    def start_game(self, ip_val, port_val):
        self.remove_widget(self.start_screen)
        if not self.reader:
            self.reader = OSCReader(ip_val.strip(), int(port_val.strip()))

        self.curr_pos = self.reader.get_pos()['gravity']
        self.curr_touch = {} # self.reader.get_pos()['touch']
        self.last_touch = {}
        self.touch_diff_x, self.touch_diff_y = 0, 0

        
    def add_space_objects(self):
        # planet_weights = [0.1, 0.3, 0.3, 0.3]
        # planet_choices = ['special_planet', 'planet1', 'planet2', 'planet3']

        self.space_objects = []

        for _ in range(5):  # create planets
            # rand_planet = np.random.choice(planet_choices, p=planet_weights)
            self.space_objects.append(SpaceObject(np.random.randint(
                30, 60), '../img/planet'+str(np.random.choice(range(1,5)))+'.png', 'planet'))

        for _ in range(20):  # create stars
            self.space_objects.append(SpaceObject(
                np.random.randint(10, 20), '../img/star.png', 'star'))

        # create astronaut
        self.space_objects.append(SpaceObject(
            50, '../img/astronaut.png', 'astronaut'))

        self.space_objects.append(SpaceObject(
            80, '../img/special_planet2.png', 'splanet'))

        self.space_objects.append(SpaceObject(
            80, '../img/special_planet.png', 'splanet2'))

        for obj in self.space_objects:
            self.objects.add(obj)  # to be changed to anim_group

        # create static stars
        self.static_objects = []
        for _ in range(60):  # create round stars
            self.static_objects.append(SpaceObject(
                np.random.randint(4, 8), '../img/star2.png', 'star2'))

        for obj in self.static_objects:
            self.canvas.add(obj)  # to be changed to anim_group

        # add spaceship
        self.starship_anim_group = AnimGroup()
        self.canvas.add(self.starship_anim_group)
        self.starship_anim_group.add(self.starship)

    def on_update(self):
        if self.reader:
            print('here')
            self.update_pos()
            self.starship.set_accel(self.curr_pos['x'], self.curr_pos['y'])
        else:
            self.starship.set_accel(0,0)

        self.tonnetz.on_update()
        
        self.audio_ctrl.on_update()
        self.objects.on_update()  # anim group
        self.starship_anim_group.on_update()
        self.player.on_update()

        self.info.text = ''
        # self.info.text = f'fps:{kivyClock.get_fps():.0f}\n'

        # self.info.text += 'x: ' + str(round(self.curr_pos['x'], 4)) + '\n'
        # self.info.text += 'y: ' + str(round(self.curr_pos['y'], 4)) + '\n'
        # self.info.text += f'position: {self.starship.get_curr_pos()}\n'
        # # self.info.text += f'{self.starship.rotate.angle}'
        # self.info.text += f'{self.objects.size()}\n'
        # self.info.text += f'touch x: {self.touch_diff_x} y: {self.touch_diff_y}'

    def on_resize(self, win_size):
        self.tonnetz.on_resize(win_size)
        resize_topleft_label(self.info)
        self.starship.on_resize(win_size)
        self.start_screen.width, self.start_screen.height =win_size
        self.start_screen.on_resize(win_size)
        for obj in self.space_objects:
            obj.on_resize(win_size)

    def update_pos(self):
        response = self.reader.get_pos()
        if response:
            self.curr_pos = response['gravity']
            if len(response['touch']) > 0:
                self.last_touch = self.curr_touch
                self.curr_touch = response['touch'][0]
                if 'x' in self.last_touch and 'y' in self.last_touch:
                    self.touch_diff_x = self.curr_touch['x'] - self.last_touch['x']
                    self.touch_diff_y = self.curr_touch['y'] - self.last_touch['y']
                
                # zoom in/out
                if self.touch_diff_y < 0:
                    self.player.zoom(_in=True)
                elif self.touch_diff_y > 0:
                    self.player.zoom(_in=False)
                    
            else:
                self.curr_touch = {}
                self.touch_diff_x, self.touch_diff_y = 0, 0

    def on_key_down(self, keycode, modifiers):

        if keycode[1] == 'up':
            # self.tonnetz.modify_seq_length(10.)
            self.player.zoom(_in=True)

        if keycode[1] == 'down':
            # self.tonnetz.modify_seq_length(-10.)
            self.player.zoom(_in=False)

        # following commands are for debugging
        # may have conflicts with player
        if keycode[1] == 'p':
            self.audio_ctrl.play_astronaut()

        if keycode[1] == 'q':
            self.audio_ctrl.pause_astronaut()

        if keycode[1] == 'c':
            self.audio_ctrl.play_chromscale()

        if keycode[1] == 's':
            self.audio_ctrl.play_seventh()
            self.audio_ctrl.play_melody()

        if keycode[1] == 'd':
            self.audio_ctrl.pause_seventh()
            self.audio_ctrl.stop_melody()

        if keycode[1] == 'm':
            self.audio_ctrl.play_modescale()

        if keycode[1] == 'n':
            self.audio_ctrl.stop_modescale()

        if keycode[1] == 'j':
            self.audio_ctrl.climax.start()

        if keycode[1] == 'k':
            self.audio_ctrl.climax.stop()
        
        if keycode[1] == 'v':
            self.audio_ctrl.soundeffect.start()

        if keycode[1] == 'b':
            self.audio_ctrl.soundeffect.stop()

        if keycode[1] == '[':
            self.audio_ctrl.play_highline()

        if keycode[1] == ']':
            self.audio_ctrl.stop_highline()

        # click 'a' to go back to main screen
        if keycode[1] == 'a':
            if self.start_screen not in self.children:
                with self.canvas.before:
                    self.add_widget(self.start_screen, 0)
                    self.reader = None

if __name__ == "__main__":
    if platform == 'darwin': # macOS
        run(MainWidget())
    else: # platform == 'Windows': # Windows
        assert len(sys.argv) >= 2, 'Need arguments ip and port'
        # assert sys.argv[2].isdigit() and int(
        #     sys.argv[2]) >= 1024, 'port needs to be a number greater than or equal to 1024'

        run(MainWidget(sys.argv[1]))
