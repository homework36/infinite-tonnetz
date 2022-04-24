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
                    vel = int(np.interp(dist, (0, touch_dist), (60,15)))
                    self.audio_ctrl.adjust_volume(self.audio_ctrl.chromscale_chan,vel)
                    self.audio_ctrl.play_chromscale()

            elif type == 'astronaut':  # play recording
                if dist < astronaut_dist:
                    vel = np.interp(dist, (0, astronaut_dist), (0.2, 0.01))
                    self.audio_ctrl.adjust_astronaut(vel)
                    self.audio_ctrl.play_astronaut()
                else:
                    self.audio_ctrl.pause_astronaut()
                pass

            elif type == 'planet':  # play seventh note
                if dist <= touch_dist:
                    self.near_planet += 1
                else:
                    self.near_planet -= 1
                    self.near_planet = max(0,self.near_planet)
            
        if self.near_planet > 0:
            self.audio_ctrl.play_seventh()
            self.audio_ctrl.play_melody()
        else:
            self.audio_ctrl.pause_seventh()
            self.audio_ctrl.stop_melody()

        # move space objects relatively as main object moves
        if self.main_obj.touch_boundary_x or self.main_obj.touch_boundary_y:
            dx, dy = self.main_obj.get_moving_dist()
            scale_x = 1.1 if dx > 0 else 0.9
            scale_y = 1.1 if dy > 0 else 0.9
            for i in self.space_objects:
                if self.main_obj.touch_boundary_x and self.main_obj.touch_boundary_y:
                    i.update_pos(-dx*scale_x, -dy*scale_y)
                elif self.main_obj.touch_boundary_x:
                    i.update_pos(-dx*scale_x, 0)
                elif self.main_obj.touch_boundary_y:
                    i.update_pos(0, -dy*scale_y)

            for i in self.static_objects:
                if self.main_obj.touch_boundary_x and self.main_obj.touch_boundary_y:
                    i.update_pos(-dx*scale_x, -dy*scale_y)
                elif self.main_obj.touch_boundary_x:
                    i.update_pos(-dx*scale_x, 0)
                elif self.main_obj.touch_boundary_y:
                    i.update_pos(0, -dy*scale_y)