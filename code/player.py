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
            if type == 'star':
                if dist < touch_dist:
                    self.audio_ctrl.play_chromscale()

            elif type == 'astronaut':  # play recording
                if dist < touch_dist * 2:
                    if not self.audio_ctrl.playing:
                        self.audio_ctrl.toggle()
                        self.audio_ctrl.reading_max_gain = 0.05 * \
                            (1.5-dist / touch_dist)
                elif dist < touch_dist * 3:
                    if not self.audio_ctrl.playing:
                        self.audio_ctrl.toggle()
                        self.audio_ctrl.reading_max_gain = 0.05 * \
                            (dist / touch_dist / 3 * 0.05)
                else:
                    if self.audio_ctrl.playing:
                        self.audio_ctrl.toggle()

            elif type == 'planet':  # play seventh note
                if dist < touch_dist:
                    self.audio_ctrl.toggle_seventh()

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