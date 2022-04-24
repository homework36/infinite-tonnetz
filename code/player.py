import sys, os
sys.path.insert(0, os.path.abspath('..'))


class Player(object):
    def __init__(self, main_obj, tonnetz, audio_ctrl, space_objects):
        super(Player, self).__init__()
        self.tonnetz = tonnetz
        self.audio_ctrl = audio_ctrl
        self.main_obj = main_obj
        self.space_objects = space_objects
        self.on_update()

    def on_update(self):
        main_x, main_y = self.main_obj.get_curr_pos()
        main_size = self.main_obj.radius
        
        for obj in self.space_objects.values():
            for i in obj:
                obj_x, obj_y = i.get_curr_pos()
                obj_size = i.r
                # if main_x + main_size >= obj_x - obj_size:
                #     print(i.type, 'right')
                # if main_x - main_size <= obj_x + obj_size:
                #     print(i.type, 'left')
                # if main_y + main_size >= obj_y - obj_size:
                #     print(i.type, 'bottom')
                # if main_y - main_size <= obj_y + obj_size:
                #     print(i.type, 'up')

        # move space objects relatively as main object moves
        if self.main_obj.touch_boundary_x or self.main_obj.touch_boundary_y:
            dx, dy = self.main_obj.get_moving_dist()
            scale_x = 1.1 if dx > 0 else 0.9
            scale_y = 1.1 if dy > 0 else 0.9
            for obj in self.space_objects.values():
                for i in obj:
                    if self.main_obj.touch_boundary_x and self.main_obj.touch_boundary_y:
                        i.update_pos(-dx*scale_x, -dy*scale_y)
                    elif self.main_obj.touch_boundary_x:
                        i.update_pos(-dx*scale_x, 0)
                    elif self.main_obj.touch_boundary_y:
                        i.update_pos(0, -dy*scale_y)
