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
        self.on_update()

    def on_update(self):
        self.near_planet = 0
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
        for i in self.space_objects:
            obj_x, obj_y = i.get_curr_pos()
            obj_size = i.r
            type = i.type
            dist = np.sqrt((main_x - obj_x)**2 + (main_y - obj_y)**2)
            touch_dist = (main_size + obj_size)
            astronaut_dist = touch_dist * 3
            if type == 'star':
                if dist < touch_dist:
                    vel = int(np.interp(dist, (0, touch_dist), (100, 30)))
                    self.audio_ctrl.adjust_volume(
                        self.audio_ctrl.synth, self.audio_ctrl.chromscale_chan, vel)
                    self.audio_ctrl.play_chromscale()
                    i.on_update(0, start_anim=True)

            elif type == 'astronaut':  # play recording
                if dist < astronaut_dist:
                    vel = np.interp(dist, (0, astronaut_dist), (0.2, 0.01))
                    self.audio_ctrl.adjust_astronaut(vel)
                    self.audio_ctrl.play_astronaut()
                    i.on_update(0, start_anim=True)
                else:
                    self.audio_ctrl.pause_astronaut()
                pass

            elif type == 'planet':  # play seventh note
                if dist <= touch_dist * 2:
                    
                    self.near_planet += 1
                    self.audio_ctrl.play_seventh()
                    i.on_update(0, start_anim=True)
                    if dist <= touch_dist:
                        vel = int(np.interp(dist, (0, touch_dist), (80, 15)))
                        self.audio_ctrl.adjust_volume(
                        self.audio_ctrl.synth2, self.audio_ctrl.melody_chan, vel)
                        self.audio_ctrl.play_melody()


            elif type == 'splanet':
                if dist <= touch_dist * 2:
                    # adjust for chord
                    vel = int(np.interp(dist, (0, touch_dist * 2), (0, 60)))
                    self.audio_ctrl.adjust_volume(
                        self.audio_ctrl.synth_bg, 1, vel)
                    # adjust for splanet
                    vel = int(np.interp(dist, (0, touch_dist * 2), (70, 15)))
                    self.audio_ctrl.adjust_volume(
                        self.audio_ctrl.synth, self.audio_ctrl.sidepiece_chan, vel)
                    self.audio_ctrl.play_jazz()
                    i.on_update(0, start_anim=True)
                else:
                    self.audio_ctrl.stop_jazz()