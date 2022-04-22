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
    def __init__(self, bubble, tonnetz, audio_ctrl):
        super(Player, self).__init__()
        self.tonnetz = tonnetz
        self.audio_ctrl = audio_ctrl
        self.bubble = bubble
        self.on_update()
        
 
    def on_update(self):
        self.audio_ctrl.on_update()
        last_pos = self.bubble.get_last_pos()
        cur_pos = self.bubble.get_curr_pos()
        for line in self.tonnetz.line_list:
            if_trans = line.check_cross(cur_pos,last_pos)
            if if_trans is None:
                pass
            else:
                # print('trans:',if_trans)
                self.audio_ctrl.make_prl(if_trans)
