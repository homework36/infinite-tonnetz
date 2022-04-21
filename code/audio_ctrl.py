# from math import radians, ceil
# from struct import calcsize
import sys, os
sys.path.insert(0, os.path.abspath('..'))

# from imslib.core import BaseWidget, run, lookup
# from imslib.gfxutil import topleft_label, resize_topleft_label, CEllipse, KFAnim, AnimGroup, CRectangle

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
# from kivy.uix.label import Label
# from kivy.graphics.instructions import InstructionGroup
# from kivy.graphics import Color, Ellipse, Rectangle, Line
# from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate


from imslib.writer import AudioWriter
from imslib.audio import Audio
from imslib.clock import SimpleTempoMap, AudioScheduler, kTicksPerQuarter, quantize_tick_up
from imslib.core import BaseWidget, run
from imslib.gfxutil import topleft_label, resize_topleft_label, Cursor3D, AnimGroup, scale_point, CEllipse
from imslib.leap import getLeapInfo, getLeapFrame
from imslib.synth import Synth
from imslib.mixer import Mixer

# from random import randint, random
import numpy as np
# from pyrsistent import b
from helper_function import *

from pedalboard import Pedalboard, Reverb



class AudioController(object):
    def __init__(self):
        super(AudioController, self).__init__()
        self.audio = Audio(2)
        self.mixer = Mixer()
        self.synth_bg = SynthEffect(effect=Reverb(room_size=0.75, wet_level=0.5))
        self.synth = SynthEffect(effect=Reverb(room_size=0.5, wet_level=0.5))


        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(80)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.mixer)
        self.mixer.add(self.synth_bg)
        self.mixer.add(self.synth)

        # note parameters
        self.root_pitch = 60
        self.pitch = 60
        self.mode = 1
        self.vel = 40
        self.triad = np.array([[0,3,7],[0,4,7]][self.mode]) + self.pitch
        self.triad = open_triad(self.triad)
        self.chord_audio = chord_audio(self.sched, self.synth_bg, 1, (0,49), self.triad, loop=False)


        self.keys = ['C','C#','D','Eb','E','F','F#',\
                'G','Ab','A','Bb','B','C']
        self.modes = [' minor',' major']
        self.key = self.keys[(self.pitch-60)%12] + self.modes[self.mode]
        self.pitchlists = [(0, 2, 3, 5, 7, 8, 11, 12),\
            (0, 2, 4, 5, 7, 9, 11, 12)]
        self.make_notes()
        self.arpeg = Arpeggiator(self.sched, self.synth, self.flashynotes, channel = 2, program = (0,47) )  
        self.melody = Arpeggiator2(self.sched, self.synth, notes=self.melodynotes+24, length = 960, channel = 3, program = (0,53) )   

        self.playing = False
    
    def make_notes(self):
        self.melodynotes = self.pitchlists[self.mode] + self.triad[0] 
        self.flashynotes = np.array([self.melodynotes[i] for i in [0,2,3,4,3,2]]) + 12 * 2
        

    def melody_jump(self,num):
        self.melody.set_jump(num)
        
    def change_flashyrhythm(self,length, articulation):
        self.arpeg.set_rhythm(length, articulation)


    def make_prl(self, trans):

        # print('making trans:',trans)
        mode, triad, key = make_trans(self.mode,self.triad,self.pitch,trans=trans)
        self.mode,self.triad,self.pitch = mode, triad, key
        self.key = self.keys[(self.pitch-60)%12] + self.modes[self.mode]
        # print('after trans',self.key, self.triad, self.mode)
        self.chord_audio.set_triad(self.triad)
        self.make_notes()
        self.arpeg.set_pitches(self.flashynotes)
        self.melody.set_pitches(self.melodynotes+24)

    # start / stop the song
    def toggle(self):
        if self.chord_audio.playing:
            self.chord_audio.stop()
            self.arpeg.stop()
            self.melody.stop()
            self.playing = False
        else:
            self.chord_audio.start()
            self.arpeg.start()
            self.melody.start()
            self.playing = True

    # needed to update audio
    def on_update(self):
        self.audio.on_update()

# no looping
class chord_audio(object):
    def __init__(self, sched, synth, channel, program, triad, loop=False):
        """
        :param sched: The Scheduler object. Should keep track of ticks and
            allow commands to be scheduled.
        :param synth: The Synthesizer object that will generate audio.
        :param channel: The channel to use for playing audio.
        :param program: A tuple (bank, preset). Allows an instrument to be specified.
        :param chord: The chord to play, a list of pitches.
        :param loop: whether to loop the chord
        """
        super(chord_audio, self).__init__()
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        self.triad = triad
        self.playing = False
        self.length = 480*5
        self.vel = 40

        self.on_cmd = None
        self.off_cmd = []
        self.loop = loop


    def toggle(self):
        if self.playing:
            self.stop()
        else:
            self.start()
    
    # simple version using continuous synth
    ############################################

    # def set_triad(self, new_triad):
    #     self.stop()
    #     self.triad = new_triad
    #     self.start()

    # def start(self):
    #     if self.playing:
    #         return

    #     self.playing = True
    #     self.synth.program(self.channel, self.program[0], self.program[1])

    #     bass, third, fifth = self.triad
    #     self.synth.noteon(self.channel, bass, self.vel)
    #     self.synth.noteon(self.channel, third, self.vel)
    #     self.synth.noteon(self.channel, fifth, self.vel)

    # def stop(self):
    #     if not self.playing:
    #         return

    #     self.playing = False
    #     bass, third, fifth = self.triad
    #     self.synth.noteoff(self.channel, bass)
    #     self.synth.noteoff(self.channel, third)
    #     self.synth.noteoff(self.channel, fifth)

    
    # 2nd version using reverb synth
    ############################################

    def set_triad(self, new_triad):
        self.triad = new_triad
        if not self.loop:
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
        self.synth.noteoff(0, self.triad[0])
    
    def _note_on(self, tick):

        self.off_cmd = []
        # play new note if available
        bass, third, fifth = self.triad
        # play note and post note off
        self.synth.noteon(0, bass, self.vel)
        self.synth.noteon(1, third, self.vel)
        self.synth.noteon(2, fifth, self.vel)

        off_tick = tick + self.length * .95 # slightly detached 
        # self.off_cmd.append(self.sched.post_at_tick(self._note_off, off_tick, bass)) 
        self.off_cmd.append(self.sched.post_at_tick(self._note_off, off_tick, third)) 
        self.off_cmd.append(self.sched.post_at_tick(self._note_off, off_tick, fifth)) 

        if self.loop:
        # schedule the next note:
            self.on_cmd = self.sched.post_at_tick(self._note_on, tick + self.length)


    def _note_off(self, tick, pitch):
        # terminate current note:
        self.synth.noteoff(self.channel, pitch)


        

class SynthEffect(Synth):
    def __init__(self, filepath = None, gain = 0.8, effect = None):
        """Generator that creates sounds from a FluidSynth synthesizer bank.

        :param filepath: Path to the file containing the synthesizer bank. If ``None``, Synth will load a locally cahced FluidR3_GM.sf2 file. If uncached, Synth will download FluidR3_GMsf2.
        :param gain: The gain, a float between 0 and 1.
        """

        super(Synth, self).__init__(gain, samplerate=Audio.sample_rate)
        if filepath is None:
            filepath = self._get_cached_fluidbank()
        self.sfid = self.sfload(filepath)
        if self.sfid == -1:
            raise Exception('Error in fluidsynth.sfload(): cannot open ' + filepath)
        self.program(0, 0, 0)
        self.effect = effect
        self.sr = Audio.sample_rate
    
    def generate(self, num_frames, num_channels):
        """
        Generates and returns frames. Should be called every frame.

        :param num_frames: An integer number of frames to generate.
        :param num_channels: Number of channels. Can be 1 (mono) or 2 (stereo)

        :returns: A tuple ``(output, True)``. The output is a numpy array of length
            **(num_frames * num_channels)**
        """

        assert(num_channels == 2)
        # get_samples() returns interleaved stereo, so all we have to do is scale
        # the data to [-1, 1].
        samples = self.get_samples(num_frames).astype(np.float32)
        samples *= (1.0/32768.0)
        if self.effect is not None:
            samples = self.effect(samples, sample_rate=self.sr)
        return (samples, True)


class Arpeggiator(object):
    def __init__(self, sched, synth, notes, length = 240, channel=2, program=(0, 40)):
        super(Arpeggiator, self).__init__()

        self.playing = False
        self.initind = True
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        
        self.notes = notes
        self.length = length
        self.articulation = 1
        self.playmode = self._up
        self.playmodename = 'up'
        self.goingup = True
        self.ind = self.playmode(0)

        self.on_cmd = None
        self.off_cmd = None

        self.oldlength = None
        self.oldarticulation = None
        self.vel = 30

        self.lastpitch = None
        self.jump = 0.5
    
    def change_channel_vol(self,in_num):
        if in_num == 1:
            self.vel += 10
        if in_num == -1:
            self.vel -= 10
        if self.vel >= 120:
            self.vel = 120
        if self.vel <= 80:
            self.vel = 80

    # start the arpeggiator
    def start(self):
        if self.playing:
            return 
        if len(self.notes) == 0:
            return 
        self.playing = True

        self.synth.program(self.channel,self.program[0],self.program[1])
        tick = self.sched.get_tick()

        # can start with synchopation
        noteplay_original = self.length + tick
        noteplay = quantize_tick_up(noteplay_original, self.length) - self.length
        self.on_cmd = self.sched.post_at_tick(self._noteon, noteplay)
        

    # stop the arpeggiator
    def stop(self):
        if not self.playing:
            return

        self.playing = False
        if self.on_cmd:
            self.sched.cancel(self.on_cmd)
        if self.off_cmd:
            self.sched.cancel(self.off_cmd)
            self.off_cmd.execute() # cause note off to happen right now
        
        self.on_cmd = None
        self.off_cmd = None
        
    
    # pitches is a list of MIDI pitch values. For example [60 64 67 72]
    def set_pitches(self, pitches):
        self.notes = np.sort(np.array(pitches))
        while self.ind >= len(self.notes):
            self.ind = len(self.notes) - 1

 
    def set_rhythm(self, length, articulation):

        self.oldlength = self.length
        self.oldarticulation = self.articulation
        self.length = length
        self.articulation = articulation
        # self.start()
    

    # dir is either 'up', 'down', or 'updown'
    def set_direction(self, direction):
        if direction == 'updown':
            self.playmode = self._updown
        elif  direction == 'down':
            self.playmode = self._down
        else:
            self.playmode = self._up

    def _noteon(self,tick):
        if len(self.notes) == 0:
            return
        
        pitch = self.notes[self.ind]   
        self.synth.noteon(self.channel,pitch,self.vel) 

        noteplay_original = self.length + tick
        noteplay = quantize_tick_up(noteplay_original, self.length) - self.length
        
        # schedule the next noteon
        self.on_cmd = self.sched.post_at_tick(self._noteon, noteplay)
        
        
        notestop = .95*(self.length*self.articulation) + tick
        # schedule the noteoff
        self.off_cmd = self.sched.post_at_tick(self._noteoff, notestop, pitch)

        # to next
        self.ind = self.playmode(self.ind)
    
    def _noteoff(self,tick,pitch):
        self.synth.noteoff(self.channel,pitch)

    def _up(self,idx):
        self.playmodename = 'up'
        if self.initind:
            self.initind = False
            return 0
        if len(self.notes) == 1:
            return 0
        if idx >= len(self.notes) - 1:
            return 0
        else:
            return idx + 1
    
    def _down(self,idx):
        self.playmodename = 'down'
        if self.initind:
            self.initind = False
            assert len(self.notes) >= 1
            return len(self.notes) - 1
        if len(self.notes) == 1:
            return 0
        if idx == 0:
            return len(self.notes) - 1
        else:
            return idx - 1
    
    def _updown(self,idx):
        self.playmodename = 'updown'
        if self.initind:
            self.initind = False
            assert len(self.notes) > 1
            return 0
        if len(self.notes) == 1:
            return 0
        if idx <= 0:
            self.goingup = True
            return 1
        elif idx >= len(self.notes) - 1:
            self.goingup = False
            return len(self.notes) - 2

        if self.goingup:
            return idx + 1
        else:
            return idx - 1
    
class Arpeggiator2(object):
    def __init__(self, sched, synth, notes=None, length=480, channel=0, program=(0, 40)):
        
        super(Arpeggiator2, self).__init__()

        self.playing = False
        self.initind = True
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program
        self.width, self.height = Window.width, Window.height
        
        self.notes = notes
        self.length = length
        self.articulation = 1


        self.on_cmd = None
        self.off_cmd = None

        self.oldlength = None
        self.oldarticulation = None
        self.vel = 25
        self.lastpitch = None
        self.jump = 0.5
      
        if self.notes is not None:
            self.possible_notes = np.sort(np.concatenate((self.notes,self.notes+12,self.notes-12)))
    
    
    def set_jump(self,in_num):
        self.jump = in_num
        if self.jump >= 2:
            self.jump = 1.5
        if self.jump <= 0:
            self.jump = 0 
        
    
    # pitches is a list of MIDI pitch values. For example [60 64 67 72]
    def set_pitches(self, pitches):
        self.notes = np.sort(np.array(pitches))
        self.possible_notes = np.sort(np.concatenate((self.notes,self.notes+12,self.notes-12)))       
    
    def set_rhythm(self, length, articulation):
        self.oldlength = self.length
        self.oldarticulation = self.articulation
        self.length = length
        self.articulation = articulation


    def _noteon(self,tick):
        if len(self.notes) == 0:
            return

        pitch = self.nextpitch()
        self.lastpitch = pitch   
        self.synth.noteon(self.channel,pitch,self.vel) 

        noteplay_original = self.length + tick
        noteplay = quantize_tick_up(noteplay_original, self.length) - self.length
        
        # schedule the next noteon
        self.on_cmd = self.sched.post_at_tick(self._noteon, noteplay)
        
        
        notestop = .95*(self.length*self.articulation) + tick
        # schedule the noteoff
        self.off_cmd = self.sched.post_at_tick(self._noteoff, notestop, pitch)

    def nextpitch(self):
        '''pitch selection process: will try to stay in the same pitch, and avoid moving too far,
        unless self.jump is set to a larger value
        when it's just launched, always pich the first in self.notes because that's the bass'''
        if self.lastpitch:
            ind = int(np.round(np.random.laplace(loc=self.ind,scale=self.jump)))
            if ind < 0 or ind >= len(self.possible_notes):
                return self.lastpitch
            if abs(ind-self.ind)>=9:
                return self.lastpitch
            self.ind = ind
            return self.possible_notes[self.ind]
        else:
            picknote = self.notes[0]
            self.ind = np.where(self.possible_notes==picknote)[0][0]
            return picknote

    # want to remove this redundant part later
    ################################################
    def _noteoff(self,tick,pitch):
        self.synth.noteoff(self.channel,pitch)

    def start(self):
        if self.notes is None:
            return 
        if self.playing:
            return 
        if len(self.notes) == 0:
            return 
        self.playing = True

        self.synth.program(self.channel,self.program[0],self.program[1])
        tick = self.sched.get_tick()

        # start with organ
        noteplay_original = self.length + tick
        noteplay = quantize_tick_up(noteplay_original, self.length) - self.length
        self.on_cmd = self.sched.post_at_tick(self._noteon, noteplay)
        
    # stop the arpeggiator
    def stop(self):
        if self.notes is None:
            return 
        if not self.playing:
            return

        self.playing = False
        if self.on_cmd:
            self.sched.cancel(self.on_cmd)
        if self.off_cmd:
            self.sched.cancel(self.off_cmd)
            self.off_cmd.execute() # cause note off to happen right now
        
        self.on_cmd = None
        self.off_cmd = None
    
    def change_channel_vol(self,in_num):
        if in_num == 1:
            self.vel += 10
        if in_num == -1:
            self.vel -= 10
        if self.vel >= 120:
            self.vel = 120
        if self.vel <= 80:
            self.vel = 80
    
    ############################## end of redundant part

