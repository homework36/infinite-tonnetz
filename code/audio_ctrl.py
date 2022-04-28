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
from imslib.synth import Synth
from imslib.mixer import Mixer
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveBuffer, WaveFile
from imslib.noteseq import NoteSequencer

# from random import randint, random
import numpy as np
# from pyrsistent import b
from helper_function import *

from pedalboard import Reverb



Chromatics = np.array([12-i for i in range(13)]+[-24]) 

class AudioController(object):
    def __init__(self):
        super(AudioController, self).__init__()
        self.audio = Audio(2)
        self.mixer = Mixer()
        self.synth_bg = SynthEffect(effect=Reverb(room_size=0.7, wet_level=0.7))
        self.synth = SynthEffect(effect=Reverb(room_size=0.5, wet_level=0.7))
        self.synth2 = Synth()
        self.synth3 = SynthEffect(effect=Reverb(room_size=0.3, wet_level=0.3))

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(72)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.mixer)
        self.mixer.add(self.synth_bg)
        self.mixer.add(self.synth)
        self.mixer.add(self.synth2)
        self.mixer.add(self.synth3)

        # note parameters
        self.root_pitch = 60
        self.pitch = 60
        self.mode = 1
        self.vel = 40
        self.triad = np.array([[0,3,7],[0,4,7]][self.mode]) + self.pitch
        self.triad = open_triad(self.triad)
        self.seventh = np.array([[10,11][self.mode]]) + self.pitch
        # print('seventh',self.seventh)
        self.if_seventh = False
        self.chord_audio = chord_audio(self.sched, self.synth_bg, 1, (0,49), self.triad, loop=False)
        self.chord_svth_chan = 0
        self.chord_audio_svth = chord_audio(self.sched, self.synth_bg, self.chord_svth_chan, (0,99), self.seventh, loop=False)
        self.backround_sound = True # play background chord at the beginning
    


        self.keys = ['C','C#','D','Eb','E','F','F#',\
                'G','Ab','A','Bb','B','C']
        self.modes = [' minor',' major']
        self.key = self.keys[(self.pitch-60)%12] + self.modes[self.mode]
        self.pitchlists = [(0, 2, 3, 5, 7, 8, 11, 12),\
            (0, 2, 4, 5, 7, 9, 11, 12)]
        self.make_notes()
        self.arpeg_chan = 2
        self.arpeg_synth = self.synth_bg
        self.arpeg = Arpeggiator2(self.sched, self.arpeg_synth, self.flashynotes, 480, self.arpeg_chan, program=(0,33),vel=30,rhythm_change=True)  
        self.arpeg.jump = 0.5
        self.melody_chan = 3
        self.melody_synth = self.synth
        self.melody = Jammer2(self.sched, self.melody_synth, self.melody_chan, (0,68),(self.pitch,self.mode))   
        self.chromscale_chan = 4
        self.chromscale_synth = self.synth2
        self.chromscale = ChromScaleSeq(self.sched, self.chromscale_synth, self.chromscale_chan,  (0,14), self.chromnotes, vel=35, loop=False)  
        self.sidepiece_chan = 5
        self.sidepiece_synth = self.synth2
        self.sidepiece = SidePiece(self.sched, self.sidepiece_synth, self.sidepiece_chan, (128,33), (self.pitch,self.mode))
        
        self.soundeffect_chan = 10
        self.soundeffect_synth = self.synth
        self.soundeffect = ChromScaleSeq(self.sched, self.soundeffect_synth, self.soundeffect_chan,  (8,116), self.triad[:2]-24,  vel=80, loop=False)  
        self.soundeffect.length = 160

        self.drum_chan = 9
        self.drum_synth = self.synth3
        self.drum1 = Drum(self.sched, self.drum_synth, self.triad, self.drum_chan, (128,9), rhythm=0, vel = 45) 
        self.drum2 = Drum(self.sched, self.drum_synth, self.triad, self.drum_chan-2, (8,116),rhythm=1, vel = 60)
        self.drum3 = Drum(self.sched, self.drum_synth, self.triad, self.drum_chan-2, (0,118), rhythm=2, vel = 60)
        self.drum4 = Drum(self.sched, self.drum_synth, self.triad, self.drum_chan-3, (0,116), rhythm=3, vel = 60) 
        self.drums = []
        self.drums.append(self.drum1)
        self.drums.append(self.drum2)
        self.drums.append(self.drum3)
        self.drums.append(self.drum4)
        
        self.highline_chan = 6
        self.highline_synth = self.synth3
        self.highline = Jammer(self.sched, self.highline_synth, self.highline_chan, (0,98), (self.pitch,self.mode),vel=45)

        self.climax_synth = self.synth
        self.climax_chan = 0
        self.climax = Jammer(self.sched, self.climax_synth, self.climax_chan, (0,99),(self.pitch,self.mode),vel=65,ornament=Ornament2)
        self.climax.set_length(160)
        self.climax.loop_max = 8

        self.jpn_reading = WaveGenerator(WaveFile('../sound/LPP_ch1_jpn.wav'),loop=True)
        self.fr_reading = WaveGenerator(WaveFile('../sound/LPP_ch1_fr.wav'),loop=True)
        self.reading_max_gain = 0.15
        self.mixer.add(self.jpn_reading)
        self.mixer.add(self.fr_reading)
        self.jpn_reading.pause()
        self.fr_reading.pause()
        self.jpn_reading.set_gain(self.reading_max_gain)
        self.fr_reading.set_gain(self.reading_max_gain)
    
  

    def make_notes(self):
        self.melodynotes = self.pitchlists[self.mode] + self.triad[0] 
        self.flashynotes = np.array([0,7,12,-5])+self.pitch%12+36
        self.chromnotes = self.pitch % 12 + 72 + Chromatics
  
    def melody_jump(self,num):
        self.melody.set_jump(num)
        
    def change_flashyrhythm(self,length, articulation):
        self.arpeg.set_rhythm(length, articulation)


    def make_prl(self, trans):
        print('key before',self.key)
        print('made trans',trans)
        # make prl transformation, record new data
        mode, triad, key = make_trans(self.mode,self.triad,self.pitch,trans=trans)
        self.mode,self.triad,self.pitch = mode, triad, key
        self.key = self.keys[(self.pitch-60)%12] + self.modes[self.mode]
        print('key after',self.key)
        print()
        self.seventh = np.array([[10,11][self.mode]]) + self.pitch

        # set new chord
        self.chord_audio.set_triad(self.triad)
        self.chord_audio_svth.set_triad(self.seventh)
        self.sidepiece.set_key((self.pitch,self.mode))
        self.highline.set_key((self.pitch,self.mode))
        self.climax.set_key((self.pitch,self.mode))
        self.soundeffect.set_pitches(self.triad[:2]-24)    

        self.soundeffect.start()
        # play chord in the background
        if self.backround_sound:
            self.chord_audio.start()
            if self.if_seventh:
                self.chord_audio_svth.start()

        

        # update notes in other things
        self.make_notes()
        self.arpeg.set_pitches(self.flashynotes)
        self.melody.set_key((self.pitch,self.mode))
        self.chromscale.set_pitches(self.chromnotes)
        
       
        for drum in self.drums:
            drum.set_pitches(self.triad)

        
    def play_bg_drum(self,idx=[]):
        for i in idx:
            drum = self.drums[i]
            if not drum.playing:
                drum.start()

    def stop_bg_drum(self,idx=[]):
        for i in idx:
            drum = self.drums[i]
            if drum.playing:
                drum.stop()
    
    def play_highline(self):
        if not self.highline.playing:
            self.highline.start()


    def stop_highline(self):
        if self.highline.playing:
            self.highline.stop()


    def play_astronaut(self, lan=1):
        # 1 == french
        # 0 == japanese
        if lan == 1:
            if self.fr_reading.paused:
                self.fr_reading.play()
            if not self.jpn_reading.paused:
                self.jpn_reading.pause()
        else:
            if self.jpn_reading.paused:
                self.jpn_reading.play()
            if not self.fr_reading.paused:
                self.fr_reading.pause()
    
    def pause_astronaut(self):
        if not self.fr_reading.paused:
                self.fr_reading.pause()
        if not self.jpn_reading.paused:
                self.jpn_reading.pause()

    def play_seventh(self):
        if not self.if_seventh:
            self.if_seventh = True

    def pause_seventh(self):
        if self.if_seventh:
            self.if_seventh = False

    def toggle_seventh(self):
        if self.if_seventh:
            self.if_seventh = False
        else:
            self.if_seventh = True
    
    def play_jazz(self):
        if not self.sidepiece.playing:
            self.sidepiece.start()

    def stop_jazz(self):
        if self.sidepiece.playing:
            self.sidepiece.stop()

    def play_chromscale(self):
        self.chromscale.start()
        # chromscale will end automatically

    def play_melody(self):
        if not self.melody.playing:
            self.melody.start()
    
    def stop_melody(self):
        if self.melody.playing:
            self.melody.stop()
    
    def play_modescale(self):
        if not self.arpeg.playing:
            self.arpeg.start()
    
    def stop_modescale(self):
        if self.arpeg.playing:
            self.arpeg.stop()

    # needed to update audio
    def on_update(self):
        self.audio.on_update()

    def adjust_volume(self, synth, chan_num, val):
        '''chan_num: channel number, can pass in self.xxxchan
           val: value of volumn, can use (third arg is the val value, 
           but probably want other max and min)
           val = int(np.interp(pt[0], (0, 1), (0, 127)))'''
        synth.cc(chan_num,7,val)
        # self.synth.cc(chan_num,11,val) might be better?
    
    def adjust_astronaut(self,vel):
        self.reading_max_gain = max(0.01,min(0.15,vel))
        self.jpn_reading.set_gain(self.reading_max_gain)
        self.fr_reading.set_gain(self.reading_max_gain)



# no looping
class chord_audio(object):
    def __init__(self, sched, synth, channel, program, triad, loop=True, vel = 60):
   
        super(chord_audio, self).__init__()
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        self.triad = triad
        self.playing = False
        self.length = 480 * 2
        self.vel = vel

        self.on_cmd = None
        self.off_cmd = []
        self.loop = loop
        self.synth.cc(self.channel,91,100)
        self.synth.cc(self.channel,64,65)


    def toggle(self):
        if self.playing:
            self.stop()
            self.playing = False
        else:
            self.start()
            self.playing = True
    
    def fade_out(self):
        if self.playing:
            val = self.vel
            while val > 0:
                val -= 10
                self.synth.cc(self.channel,7,val)
            self.stop()

    
    # 2nd version using reverb synth
    ############################################

    def set_triad(self, new_triad):
        self.synth.cc(self.channel,64,60)
        self.triad = new_triad
        # if not self.loop:
        #     self.stop()
        #     self.start()
        self.fade_out()
        

    def start(self):
        self.synth.cc(self.channel,64,65)
        if self.playing:
            return
        self.synth.cc(self.channel,7,self.vel)
        self.playing = True
        self.synth.program(self.channel, self.program[0], self.program[1])


        # post the first note on the next quarter-note:
        now = self.sched.get_tick()
        # next_beat = quantize_tick_up(now, int(kTicksPerQuarter/2))
        self.on_cmd = self.sched.post_at_tick(self._note_on, now)


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

        # play note and post note off
        for note in self.triad:
            self.synth.noteon(self.channel, note, self.vel)
    

        off_tick = tick + self.length * .95 # slightly detached 
        for note in self.triad:
            self.off_cmd.append(self.sched.post_at_tick(self._note_off, off_tick, note)) 
        

        if self.loop:
        # schedule the next note:
            self.on_cmd = self.sched.post_at_tick(self._note_on, tick + self.length)


    def _note_off(self, tick, pitch):
        # terminate current note:
        self.synth.noteoff(self.channel, pitch)



class SynthEffect(Synth):
    def __init__(self, filepath = None, gain = 0.8, effect = None):

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


        assert(num_channels == 2)
        # get_samples() returns interleaved stereo, so all we have to do is scale
        # the data to [-1, 1].
        samples = self.get_samples(num_frames).astype(np.float32)
        samples *= (1.0/32768.0)
        if self.effect is not None:
            samples = self.effect(samples, sample_rate=self.sr)
        return (samples, True)

    
class Arpeggiator2(object):
    def __init__(self, sched, synth, notes, length, channel, program=(0, 40), vel=50, rhythm_change=True):
        
        super(Arpeggiator2, self).__init__()

        self.playing = False
        self.initind = True
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program
        
        self.notes = notes
        self.length = length
        self.articulation = 1


        self.on_cmd = None
        self.off_cmd = None

        self.oldlength = None
        self.oldarticulation = None
        self.vel = vel
        self.lastpitch = None
        self.jump = 1.5
        self.rhythm_change = rhythm_change

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
  
        pitch = self.nextpitch()
        if pitch >= 78:
            pitch -= 12
        if pitch <= 48:
            pitch += 12
        self.lastpitch = pitch   
        self.synth.noteon(self.channel,pitch,self.vel) 

        noteplay = self.length + tick
        
        # schedule the next noteon
        self.on_cmd = self.sched.post_at_tick(self._noteon, noteplay)
        
        
        notestop = .95*(self.length*self.articulation) + tick
        # schedule the noteoff
        self.off_cmd = self.sched.post_at_tick(self._noteoff, notestop, pitch)

    def nextpitch(self):
        '''pitch selection process: will try to stay in the same pitch, and avoid moving too far,
        unless self.jump is set to a larger value
        when it's just launched, always pich the first in self.notes because that's the bass'''
        if self.rhythm_change:
            self.length = np.random.choice([120,240,480],p=[.05,.3,.65])
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
        

    def _noteoff(self,tick,pitch):
        self.synth.noteoff(self.channel,pitch)

    def start(self):
        if self.playing:
            return 
        if len(self.notes) == 0:
            return 
        self.playing = True

        self.synth.program(self.channel,self.program[0],self.program[1])
        tick = self.sched.get_tick()

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
    
class ChromScaleSeq(NoteSequencer):
    def __init__(self, sched, synth, channel, program, notes, vel = 40, loop=True, length = 30):
        super(NoteSequencer, self).__init__()
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        self.notes = notes
        self.loop = loop
        self.playing = False

        self.on_cmd = None
        self.off_cmd = None
        self.idx = 0
        self.vel = vel
        self.synth.cc(self.channel,1,50)
        self.length = length


    def start(self):
        """
        Starts playback.
        """

        if self.playing:
            return

        self.playing = True
        self.synth.program(self.channel, self.program[0], self.program[1])

        # start from the beginning
        self.idx = 0

        # post the first note on the next quarter-note:
        now = self.sched.get_tick()
        # next_beat = quantize_tick_up(now, int(kTicksPerQuarter/4))
        self.on_cmd = self.sched.post_at_tick(self._note_on, now)

    def _note_on(self, tick):
        # if looping, go back to beginning
        if self.loop and self.idx >= len(self.notes):
            self.idx = 0

        # play new note if available
        if self.idx < len(self.notes):
            pitch = self.notes[self.idx]
            if pitch != 0: # pitch 0 is a rest
                # play note and post note off
                self.synth.noteon(self.channel, pitch, self.vel)
                off_tick = tick + self.length * .95 # slightly detached 
                self.off_cmd = self.sched.post_at_tick(self._note_off, off_tick, pitch) 

            # schedule the next note:
            self.idx += 1
            self.on_cmd = self.sched.post_at_tick(self._note_on, tick + self.length)
        else:
            self.playing = False
    
    def set_pitches(self,notes):
        self.notes = notes

    def set_length(self,val):
        if 96>= self.length >= 24:
            self.length += val 

class SidePiece(object):
    def __init__(self, sched, synth, channel, program, key, vel = 60):
   
        super(SidePiece, self).__init__()
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        self.pitch, self.mode = key
        self.playing = False
        self.vel = vel

        self.on_cmd = None
        self.off_cmd = []
        self.loop = 0
        # self.synth.cc(self.channel,91,40)
        
        self.idx_top = 0
        # ii - V - i/I - iv/IV
        # self.secondary = (np.array([2, 7, 0, 5]) + self.pitch)%12+48
        # self.secondary_chord = [[0,1,0,0],[0,1,1,1]][self.mode]

        # descending fifth
        self.secondary = (np.array([0, 4, -1, 3, -2, 2, 5, 0]) + self.pitch)%12+48
        self.secondary_chord = [[0,0,1,1, 1,2,1,0 ],[1,1,0,0, 0,0,1,1]][self.mode]
        self.secondary_ind = 0
        self.scales = [[100,0, 2, 3, 5, 7, 8, 10, 12],[100,0, 2, 4, 5, 7, 9, 11, 12]]
        self.scales_basenotes = [[0,3,7,10],[0,4,7,11],[0,3,6,12]]
        self.ornament = [[-1,0],[2,-1,0],[2,0],[0]]
        self.cur_base = None
        self.cur_mode = None
        self.length = 120
        self.loop_max = 1
        self.make_notes()

    def make_notes(self,change_chord=True):
        self.cur_base = self.secondary[self.secondary_ind]
        self.cur_mode = self.secondary_chord[self.secondary_ind]
        cur_scales_base = self.scales_basenotes[self.cur_mode]
        if change_chord:
            self.idx_top = 0
            temp_notes = []
            for i in range(4):
                base_note = cur_scales_base[np.random.randint(0,4)]
                ornament = self.ornament[np.random.choice(range(4),p=[.2,.2,.2,.4])]
                temp_notes += [note + base_note for note in ornament]
                temp_notes.append(100)
            len_notes = len(temp_notes)
            beats = int(np.floor(len_notes/4)*4)
            temp_notes = temp_notes[:beats-2]
            temp_notes.append(0)
            self.notes_top_frame = np.array(temp_notes)
            self.note_num = len(self.notes_top_frame)
            # self.notes_top_frame = [self.scales[self.cur_mode][np.random.choice(range(9))] for i in range(self.note_num)]
            # self.notes_top_frame = temp_notes
            self.secondary_ind += 1
            self.secondary_ind %= 4
        
        
        self.notes_top = np.zeros(self.note_num)
        for i in range(self.note_num):
            cur = self.notes_top_frame[i]
            if cur < 100:
                temp_note = cur + self.cur_base
                while temp_note > 72:
                    temp_note -= 12
                self.notes_top[i] = temp_note
        
        self.notes_bass = np.array([[0,3,7,10],[0,4,7,11]][self.cur_mode]) + self.cur_base
        self.notes_bass = self.notes_bass%12 + 60

      
    def toggle(self):
        if self.playing:
            self.stop()
            self.playing = False
        else:
            self.start()
            self.playing = True

    def _note_on(self, tick):
        # print('playing')
        # if looping, go back to beginning
        if self.idx_top >= len(self.notes_top):
            self.idx_top = 0
            self.loop += 1
            # self.make_notes()
            if self.loop >= self.loop_max:
                self.make_notes()
                self.loop = 0
        
        if self.idx_top < len(self.notes_top):
            pitch = int(self.notes_top[self.idx_top])
            # length = int(self.length_top[self.idx_top])
            if pitch != 0: # pitch 0 is a rest
                # play note and post note off
                self.synth.noteon(self.channel, pitch, self.vel)
                off_tick = tick + self.length * .95 # slightly detached 
                self.off_cmd.append(self.sched.post_at_tick(self._note_off, off_tick, pitch)) 
            if self.idx_top % 4 == 3:
                for note in self.notes_bass:
                    cur_note = int(note)
                    self.synth.noteon(self.channel, cur_note, self.vel)
                    off_tick = tick + self.length * .95 # slightly detached 
                    self.off_cmd.append(self.sched.post_at_tick(self._note_off, off_tick, cur_note))  
            # schedule the next note:
            self.idx_top += 1
            noteplay_original = self.length + tick
            noteplay = quantize_tick_up(noteplay_original, self.length) - self.length
            self.on_cmd = self.sched.post_at_tick(self._note_on, noteplay)
        else:
            self.playing = False

        
    def set_key(self, new_key):
        self.pitch, self.mode = new_key
        self.pitch = self.pitch % 12 + 60
        self.secondary = np.array([2, 7, 0, 5]) + self.pitch
        self.secondary_chord = [[0,1,0,0],[0,1,1,1]][self.mode]
        self.make_notes(change_chord=False)

    def start(self):
        if self.playing:
            return
        self.synth.cc(self.channel,7,self.vel)
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
        # self.synth.noteoff(0, self.triad[0])


    def _note_off(self, tick, pitch):
        # terminate current note:
        self.synth.noteoff(self.channel, pitch)


RhythmBank = [
[1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
[1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0],
[0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0],
[0,0,0,0, 1,0,1,0, 0,0,0,0, 0,1,1,1]
]

class Drum(NoteSequencer):
    def __init__(self, sched, synth, notes, channel, program, vel=30, rhythm=0, note=0):
        
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        self.triad = notes
        self.rhythm = np.array(RhythmBank[rhythm])
        self.noteidx = note
        self.make_notes()
        self.loop = True
        self.playing = False

        self.on_cmd = None
        self.off_cmd = None
        self.idx = 0

        self.vel = vel
        self.synth.cc(self.channel,7,vel)
    

    def set_pitches(self, pitches):
        # self.notes = np.sort(np.array(pitches))
        self.triad = pitches
        self.make_notes()
        # print(self.notes)

    def make_notes(self):
        note = self.triad[self.noteidx]
        note = note % 12 + 12
        top = note * self.rhythm
        self.notes = [[120,top[i]] for i in range(16)]
   
    def change_rhythm(self,rhythm):
        self.rhythm = np.array(RhythmBank[rhythm])

Ornament1 = [[7,0,7],[0,7,0],[5,7],[7,5],[7,7],[0,0]]
Ornament2 = [[100,7],[100,0],[7,0],[0,7],[5,7],[2,0]]
class Jammer(SidePiece):
    def __init__(self, sched, synth, channel, program, key, ornament=Ornament1, vel = 50):
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        self.pitch, self.mode = key
        self.playing = False
        self.vel = vel

        self.on_cmd = None
        self.off_cmd = []
        self.loop = 0
        # self.synth.cc(self.channel,91,40)
        
        self.idx_top = 0
        self.ornament = ornament
        self.cur_base = None
        self.cur_mode = None
        self.length = 960
        self.notes_bass = []
        self.loop_max = 4
        self.make_notes()

    def make_notes(self,change_chord=True):

        if change_chord:
            self.idx_top = 0
            temp_notes = []
            for i in range(4):
                ornament = self.ornament[np.random.choice(range(len(self.ornament)))]
                temp_notes += [note + self.pitch for note in ornament]
                # temp_notes.append(100)
            len_notes = len(temp_notes)
            beats = int(np.floor(len_notes/4)*4)
            temp_notes = temp_notes[:beats-2]
            temp_notes.append(0)
            self.notes_top_frame = np.array(temp_notes)
            self.note_num = len(self.notes_top_frame)
        
        self.notes_top = np.zeros(self.note_num)
        for i in range(self.note_num):
            cur = self.notes_top_frame[i]
            if cur < 100:
                temp_note = cur + self.pitch
                while temp_note > 72:
                    temp_note -= 12
                self.notes_top[i] = int(temp_note)

    
    def set_key(self, new_key):
        self.pitch, self.mode = new_key
        self.pitch = self.pitch % 12 + 60
        self.make_notes(change_chord=False)

    def set_length(self, length):
        self.length = length
    
class Jammer2(SidePiece):
    def _note_on(self, tick):
        # print('playing')
        # if looping, go back to beginning
        if self.idx_top >= len(self.notes_top):
            self.idx_top = 0
            self.loop += 1
            # self.make_notes()
            if self.loop >= self.loop_max:
                self.make_notes()
                self.loop = 0
        
        if self.idx_top < len(self.notes_top):
            length = np.random.choice([120,160,240,480,720],p=[.05,.05,.3,.4,.2])
            pitch = int(self.notes_top[self.idx_top])
            # length = int(self.length_top[self.idx_top])
            if pitch != 0: # pitch 0 is a rest
                # play note and post note off
                self.synth.noteon(self.channel, pitch, self.vel)
                off_tick = tick +  length * .95 # slightly detached 
                self.off_cmd.append(self.sched.post_at_tick(self._note_off, off_tick, pitch)) 
            # schedule the next note:
            self.idx_top += 1
            noteplay_original = length + tick
            # noteplay = quantize_tick_up(noteplay_original, length) - length
            self.on_cmd = self.sched.post_at_tick(self._note_on, noteplay_original)
        else:
            self.playing = False

    def make_notes(self,change_chord=True):
        self.secondary = (np.array([0,0,0,0]) + self.pitch)%12+48
        self.secondary_chord = [[0,0,0,0],[1,1,1,1]][self.mode]
        self.cur_base = self.secondary[self.secondary_ind]
        self.cur_mode = self.secondary_chord[self.secondary_ind]
        cur_scales_base = self.scales_basenotes[self.cur_mode]
        if change_chord:
            self.idx_top = 0
            temp_notes = []
            for i in range(4):
                base_note = cur_scales_base[np.random.randint(0,4)]
                ornament = self.ornament[np.random.choice(range(4),p=[.2,.2,.2,.4])]
                temp_notes += [note + base_note for note in ornament]
            len_notes = len(temp_notes)
            beats = int(np.floor(len_notes/4)*4)
            temp_notes = temp_notes[:beats-2]
            temp_notes.append(0)
            self.notes_top_frame = np.array(temp_notes)
            self.note_num = len(self.notes_top_frame)
            # self.notes_top_frame = [self.scales[self.cur_mode][np.random.choice(range(9))] for i in range(self.note_num)]
            # self.notes_top_frame = temp_notes
            self.secondary_ind += 1
            self.secondary_ind %= 4
        
        
        self.notes_top = np.zeros(self.note_num)
        for i in range(self.note_num):
            cur = self.notes_top_frame[i]
            if cur < 100:
                temp_note = cur + self.cur_base
                while temp_note < 60:
                    temp_note += 12
                self.notes_top[i] = temp_note