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


class AudioController(object):
    def __init__(self):
        super(AudioController, self).__init__()
        self.audio = Audio(2)
        self.synth = Synth()

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(60)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # note parameters
        self.root_pitch = 60
        self.pitch = 60
        self.mode = 1
        self.vel = 80
        self.triad = np.array([[0,3,7],[0,4,7]][self.mode]) + self.pitch
        self.chord_audio = chord_audio(self.sched, self.synth, 1, (0,2), self.triad)


        self.keys = ['C','C#','D','Eb','E','F','F#',\
                'G','Ab','A','Bb','B','C']
        self.modes = [' minor',' major']
        self.key = self.keys[(self.pitch-60)%12] + self.modes[self.mode]
        self.pitchlists = [(0, 2, 3, 5, 7, 8, 11, 12),\
            (0, 2, 4, 5, 7, 9, 11, 12)]

        self.playing = False

    def make_prl(self, trans):

        print('making trans:',trans)
        mode, triad, key = make_trans(self.mode,self.triad,self.pitch,trans=trans)
        self.mode,self.triad,self.pitch = mode, triad, key
        self.key = self.keys[(self.pitch-60)%12] + self.modes[self.mode]
        print('after trans',self.key, self.triad, self.mode)
        self.chord_audio.set_triad(self.triad)

    # start / stop the song
    def toggle(self):
        if self.chord_audio.playing:
            self.chord_audio.stop()
            self.playing = False
        else:
            self.chord_audio.start()
            self.playing = True

    # needed to update audio
    def on_update(self):
        self.audio.on_update()

class chord_audio(object):
    def __init__(self, sched, synth, channel, program, triad):
        """
        :param sched: The Scheduler object. Should keep track of ticks and
            allow commands to be scheduled.
        :param synth: The Synthesizer object that will generate audio.
        :param channel: The channel to use for playing audio.
        :param program: A tuple (bank, preset). Allows an instrument to be specified.
        :param chord: The chord to play, a list of pitches.
        :param loop: When True, restarts playback from the first note.
        """
        super(chord_audio, self).__init__()
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        self.triad = triad
        self.playing = False
        self.length = 480
        self.vel = 80

        self.on_cmd = None
        self.off_cmd = []

    def set_triad(self, new_triad):
        self.triad = new_triad
        self.stop()
        self.start()

    def start(self):
        if self.playing:
            return

        self.playing = True
        self.synth.program(self.channel, self.program[0], self.program[1])


        # post the first note on the next quarter-note:
        now = self.sched.get_tick()
        next_beat = quantize_tick_up(now, kTicksPerQuarter)
        self.on_cmd = self.sched.post_at_tick(self._note_on, next_beat)


    def stop(self):
        if not self.playing:
            return

        self.playing = False
        if self.on_cmd:
            self.sched.cancel(self.on_cmd)
        if len(self.off_cmd) > 0:
            for cmd in self.off_cmd:
                self.sched.cancel(cmd)
                cmd.execute() # cause note off to happen right now
        self.on_cmd = None
        self.off_cmd = []

    def toggle(self):
        if self.playing:
            self.stop()
        else:
            self.start()

    def _note_on(self, tick):

        self.off_cmd = []
        # play new note if available
        bass, third, fifth = self.triad
        # play note and post note off
        self.synth.noteon(0, bass, self.vel)
        self.synth.noteon(1, third, self.vel)
        self.synth.noteon(2, fifth, self.vel)

        off_tick = tick + self.length * .95 # slightly detached 
        for note in self.triad:
            self.off_cmd.append(self.sched.post_at_tick(self._note_off, off_tick, note)) 

        # schedule the next note:
        self.on_cmd = self.sched.post_at_tick(self._note_on, tick + self.length)


    def _note_off(self, tick, pitch):
        # terminate current note:
        self.synth.noteoff(self.channel, pitch)
