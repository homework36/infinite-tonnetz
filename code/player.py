import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run, lookup
from imslib.audio import Audio
from imslib.mixer import Mixer
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveBuffer, WaveFile
from imslib.noteseq import NoteSequencer
from imslib.synth import Synth
from imslib.clock import SimpleTempoMap, AudioScheduler, kTicksPerQuarter, quantize_tick_up
from imslib.gfxutil import topleft_label, resize_topleft_label, CLabelRect, CRectangle
from imslib.kivyparticle import ParticleSystem
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle,PushMatrix, PopMatrix, Translate, Rotate
from kivy.core.window import Window
from kivy.uix.image import Image
from numpy import random as nprd
from kivy import metrics





class Player(object):
    def __init__(self, main_obj, tonnetz, audio_ctrl, space_objects):
        super(Player, self).__init__()
        self.tonnetz = tonnetz
        self.audio_ctrl = audio_ctrl
        self.main_obj = main_obj
        self.space_objects = space_objects
        self.on_update()
        
 
    def on_update(self):
        if self.main_obj.touch_boundary_x or self.main_obj.touch_boundary_y:
            dx, dy = self.main_obj.get_moving_dist()
            for i in self.space_objects:
                if self.main_obj.touch_boundary_x and self.main_obj.touch_boundary_y:
                    i.update_pos(-dx, -dy)
                elif self.main_obj.touch_boundary_x:
                    i.update_pos(-dx, 0)
                elif self.main_obj.touch_boundary_y:
                    i.update_pos(0, -dy)
        
