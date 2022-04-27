import sys, os
sys.path.insert(0, os.path.abspath('..'))
import numpy as np


class Player(object):
    def __init__(self, main_obj, tonnetz, audio_ctrl, space_objects, static_objects):
        super(Player, self).__init__()
        self.tonnetz = tonnetz
        self.audio_ctrl = audio_ctrl
        self.main_obj = main_obj
        self.space_objects = space_objects
        self.static_objects = static_objects
        self.near_planet = 0
        # self.near_planet_min_dist = 10000
        self.last_tonnetz_seg = self.tonnetz.seg
        self.on_update()
        
        

    def on_update(self):
        
        self.sound_anim_effect()

        if self.near_planet == 0:
            self.audio_ctrl.pause_seventh()
            self.audio_ctrl.stop_melody()
        
        self.update_pos_at_bounadry()

    def update_pos_at_bounadry(self):
        # move space objects relatively as main object moves
        if self.main_obj.touch_boundary_x or self.main_obj.touch_boundary_y:
            dx, dy = self.main_obj.get_moving_dist()
            scale_x = 1.1 if dx > 0 else 0.9
            scale_y = 1.1 if dy > 0 else 0.9
            for i in self.space_objects:
                if self.main_obj.touch_boundary_x and self.main_obj.touch_boundary_y:
                    i.on_update(0, start_anim=False, dx=-dx*scale_x, dy=-dy*scale_y)
                elif self.main_obj.touch_boundary_x:
                    i.on_update(0, start_anim=False, dx=-dx*scale_x, dy=0)
                elif self.main_obj.touch_boundary_y:
                    i.on_update(0, start_anim=False, dx=0, dy=-dy*scale_y)

            for i in self.static_objects:
                if self.main_obj.touch_boundary_x and self.main_obj.touch_boundary_y:
                    i.on_update(0, start_anim=False, dx=-dx*scale_x, dy=-dy*scale_y)
                elif self.main_obj.touch_boundary_x:
                    i.on_update(0, start_anim=False, dx=-dx*scale_x, dy=0)
                elif self.main_obj.touch_boundary_y:
                    i.on_update(0, start_anim=False, dx=0, dy=-dy*scale_y)

    def sound_anim_effect(self):
        main_x, main_y = self.main_obj.get_curr_pos()
        main_size = self.main_obj.radius
        self.near_planet = 0
        # self.near_planet_min_dist = 10000
        for i in self.space_objects:
            obj_x, obj_y = i.get_curr_pos()
            obj_size = i.r
            type = i.type
            dist = np.sqrt((main_x - obj_x)**2 + (main_y - obj_y)**2)
            touch_dist = (main_size + obj_size)
            astronaut_dist = touch_dist * 3

            if type == 'star':
                if dist < touch_dist:
                    vel = int(np.interp(dist, (0, touch_dist), (80, 50)))
                    self.audio_ctrl.adjust_volume(
                        self.audio_ctrl.chromscale_synth, self.audio_ctrl.chromscale_chan, vel)
                    self.audio_ctrl.play_chromscale()
                    i.on_update(0, start_anim=True)

            elif type == 'astronaut':  # play recording
                if dist < astronaut_dist:
                    vel = np.interp(dist, (0, astronaut_dist), (0.12, 0.01))
                    self.audio_ctrl.adjust_astronaut(vel)
                    self.audio_ctrl.play_astronaut(lan=i.rand_lan)
                    i.on_update(0, start_anim=True)
                else:
                    self.audio_ctrl.pause_astronaut()
                    i.rand_lan = np.random.choice([1,0],p=[.5,.5])
                

            elif type == 'planet':  # play seventh note
                if dist <= touch_dist * 2:
                    
                    self.near_planet += 1
                    self.audio_ctrl.play_seventh()
                    i.on_update(0, start_anim=True)

                    if dist <= touch_dist*1.2:
                        vel = int(np.interp(dist, (0, touch_dist*1.2), (90, 15)))
                        self.audio_ctrl.adjust_volume(
                        self.audio_ctrl.melody_synth, self.audio_ctrl.melody_chan, vel)
                        self.audio_ctrl.play_melody()



            elif type == 'splanet':
                if dist <= touch_dist * 2:
                    # adjust for chord
                    vel = int(np.interp(dist, (0, touch_dist ), (20, 60)))
                    self.audio_ctrl.adjust_volume(
                        self.audio_ctrl.synth_bg, 1, vel)
                    # adjust for splanet
                    vel = int(np.interp(dist, (0, touch_dist * 2), (70, 15)))
                    self.audio_ctrl.adjust_volume(
                        self.audio_ctrl.sidepiece_synth, self.audio_ctrl.sidepiece_chan, vel)
                    self.audio_ctrl.play_jazz()
                    i.on_update(0, start_anim=True)

                else:
                    self.audio_ctrl.stop_jazz()

                if dist <= self.last_tonnetz_seg:
                    vel = int(np.interp(dist, (0, self.last_tonnetz_seg), (60, 10)))
                    self.audio_ctrl.adjust_volume(
                        self.audio_ctrl.drum_synth, self.audio_ctrl.drum_chan, vel)
                    self.audio_ctrl.play_bg_drum()
                else:
                    self.audio_ctrl.stop_bg_drum()

    def zoom(self,_in=True):
        if _in:
            val = 10
        else:
            val = -10
        self.tonnetz.modify_seq_length(val)
        cur_seq = self.tonnetz.seg
        origin = self.main_obj.get_curr_pos()
        scaling_factor = cur_seq/self.last_tonnetz_seg
        for i in self.space_objects:
            i.on_zoom(scaling_factor,origin)
        for i in self.static_objects:
            i.on_zoom(scaling_factor,origin)
        self.last_tonnetz_seg = cur_seq
