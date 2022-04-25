import sys, os
sys.path.insert(0, os.path.abspath('..'))
from kivy.uix.image import Image
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.graphics.instructions import InstructionGroup
from kivy.uix.label import Label
from kivy.clock import Clock as kivyClock
from kivy.core.window import Window
from imslib.gfxutil import topleft_label, resize_topleft_label, CEllipse, KFAnim, AnimGroup, CRectangle
import numpy as np


inner_boundary_factor = 0.2
rescale_const = Window.width / 6


class SpaceObject(InstructionGroup):
    def __init__(self, r, img_path, type, callback=None):
        super(SpaceObject, self).__init__()
        self.w, self.h = Window.width, Window.height
        self.color = Color(rgb=(1, 1, 1))
        self.add(self.color)

        self.type = type
        self.r = r
        # make star2 as background, random alpha value
        if self.type == 'star2':
            self.color.a = np.random.random()

        self.vel = np.array((np.random.uniform(-10, 10),
                            np.random.uniform(-10, 10)), dtype=float)
        # self.vel = np.array((0,0), dtype=float)
        self.pos = [np.random.uniform(-0.2, 1.2) * Window.width,
                    np.random.uniform(-0.2, 1.2) * Window.height]
        self.rect = CRectangle(cpos=self.pos, csize=(2*r, 2*r), segments=40)
        self.rect.texture = Image(source=img_path).texture

        # add random rotate angle
        self.add(PushMatrix())
        self.rotate = Rotate(angle=np.random.randint(
            low=-30, high=30), origin=self.pos)
        self.add(self.rotate)
        self.add(self.rect)
        self.add(PopMatrix())
        self.time = 0

        self.start_anim = False
        self.end_time = 0

        self.on_update(0)

    def get_curr_pos(self):
        return self.pos

    def on_resize(self, win_size):
        self.r = self.r / self.w * win_size[0]
        self.rect.csize = (2*self.r, 2*self.r)

        self.pos[0] = self.pos[0] / self.w * win_size[0]
        self.pos[1] = self.pos[1] / self.h * win_size[1]
        self.rect.cpos = self.pos
        self.rotate.origin = self.pos
        self.w, self.h = win_size

    def on_update(self, dt, start_anim=False, dx=0, dy=0):
        self.time += dt
        self.pos[0] += self.vel[0] * dt + dx
        self.pos[1] += self.vel[1] * dt + dy
        self.rect.cpos = self.pos
        self.rotate.origin = self.pos
        self.add_animation(start_anim)

        if not (-inner_boundary_factor * self.w-self.r <= self.pos[0] <=
                (1+inner_boundary_factor) * self.w+self.r and
                -inner_boundary_factor * self.h-self.r <= self.pos[1] <=
                (1+inner_boundary_factor) * self.h+self.r):
            self.reset(dx, dy)

        return True

    def add_animation(self, start_anim):
        if not self.start_anim and start_anim == True:
            if self.type == 'star':
                self.size_anim = KFAnim((self.time, 2*self.r, 2*self.r),
                                        (self.time+0.3, 2*self.r*1.5, 2*self.r*1.5),
                                        (self.time+1, 0, 0))
                self.pos_anim = KFAnim((self.time, self.pos[0], self.pos[1]),
                                       (self.time+1, self.pos[0]+np.random.uniform(-1, 1) * self.w / 3, self.pos[1]+np.random.uniform(-1, 1)*self.h / 3))

            elif self.type in ['splanet', 'planet', 'astronaut']:
                self.size_anim = KFAnim((self.time, 2*self.r, 2*self.r),
                                        (self.time+0.5, 2*self.r*1.2, 2*self.r*1.2),
                                        (self.time+1, 2*self.r*1.1, 2*self.r*1.1))

            self.end_time = self.time+1
            self.start_anim = True

        if self.time < self.end_time:
            new_size = self.size_anim.eval(self.time)
            self.rect.csize = new_size

            if self.type == 'star':
                new_pos = self.pos_anim.eval(self.time)
                self.rect.cpos = new_pos
                self.pos = new_pos

        elif self.time >= self.end_time > 0:
            self.end_time = 0
            self.start_anim = False

            if self.type == 'star':
                self.reset()

    def reset(self, dx=0, dy=0):
        def get_neg_range():
            return np.linspace(-0.1, -0.05, 20)

        def get_norm_range():
            return np.linspace(-0.05, 1.05, 100)

        def get_pos_range():
            return np.linspace(1.05, 1.1, 20)

        def get_region_choice(num):
            if num == 1:  # upper left
                x_choice = get_neg_range()
                y_choice = get_pos_range()
            elif num == 2:  # upper middle
                x_choice = get_norm_range()
                y_choice = get_pos_range()
            elif num == 3:  # upper right
                x_choice = get_pos_range()
                y_choice = get_pos_range()
            elif num == 4:  # middle left
                x_choice = get_neg_range()
                y_choice = get_norm_range()
            elif num == 5:  # middle right
                x_choice = get_pos_range()
                y_choice = get_norm_range()
            elif num == 6:  # lower left
                x_choice = get_neg_range()
                y_choice = get_neg_range()
            elif num == 7:  # lower middle
                x_choice = get_norm_range()
                y_choice = get_neg_range()
            elif num == 8:  # lower right
                x_choice = get_pos_range()
                y_choice = get_neg_range()
            return x_choice.tolist(), y_choice.tolist()

        def get_all_choices(region_options):
            region = np.random.choice(region_options)
            list_x, list_y = get_region_choice(region)
            x_weights = [1/len(list_x)] * len(list_x)
            y_weights = [1/len(list_y)] * len(list_y)
            return list_x, list_y, x_weights, y_weights

        pos_x_choice, pos_y_choice = None, None
        x_weights, y_weights = [], []
        if dx > 0 and dy < 0:
            pos_x_choice, pos_y_choice, x_weights, y_weights = get_all_choices([
                                                                               1, 2, 4])
        elif dx > 0 and dy == 0:
            pos_x_choice, pos_y_choice, x_weights, y_weights = get_all_choices([
                                                                               4])
        elif dx > 0 and dy > 0:
            pos_x_choice, pos_y_choice, x_weights, y_weights = get_all_choices([
                                                                               4, 6, 7])

        elif dx < 0 and dy < 0:
            pos_x_choice, pos_y_choice, x_weights, y_weights = get_all_choices([
                                                                               2, 3, 5])
        elif dx < 0 and dy == 0:
            pos_x_choice, pos_y_choice, x_weights, y_weights = get_all_choices([
                                                                               5])
        elif dx < 0 and dy > 0:
            pos_x_choice, pos_y_choice, x_weights, y_weights = get_all_choices([
                                                                               5, 7, 8])

        elif dx == 0 and dy < 0:
            pos_x_choice, pos_y_choice, x_weights, y_weights = get_all_choices([
                                                                               2])
        elif dx == 0 and dy == 0:
            pos_x_choice, pos_y_choice, x_weights, y_weights = get_all_choices(
                [1, 2, 3, 4, 5, 6, 7, 8])
        elif dx == 0 and dy > 0:
            pos_x_choice, pos_y_choice, x_weights, y_weights = get_all_choices([
                                                                               7])

        final_x = np.random.choice(pos_x_choice, p=x_weights)
        final_y = np.random.choice(pos_y_choice, p=y_weights)
        self.pos = [final_x * Window.width, final_y * Window.height]

        self.rect.cpos = self.pos
        self.rotate.origin = self.pos
        self.rect.csize = (2*self.r, 2*self.r)


class PhysBubble(InstructionGroup):
    def __init__(self, pos, r, color=(1, 1, 1), callback=None, in_boundary=None):
        super(PhysBubble, self).__init__()

        self.width, self.height = Window.width, Window.height
        self.radius = r
        self.pos_x, self.pos_y = pos
        self.last_pos = pos
        self.vel_x, self.vel_y = 0., 0.
        self.dx, self.dy = 0., 0.

        self.add(PushMatrix())
        self.rotate = Rotate(angle=0)
        self.add(self.rotate)

        self.color = Color(rgb=color)
        self.add(self.color)

        self.circle = CEllipse(cpos=pos, csize=(2*r, 2*r), segments=40)
        self.add(self.circle)

        self.add(PopMatrix())

        self.circle.texture = Image(source='../img/icon.png').texture
        self.callback = callback
        self.in_boundary_callback = in_boundary
        self.last_angle = 0

        self.touch_boundary_x = False
        self.touch_boundary_y = False

    def set_accel(self, ax, ay):
        self.ax = ax
        self.ay = ay

    def get_last_pos(self):
        return self.last_pos

    def get_curr_pos(self):
        return [self.pos_x, self.pos_y]

    def on_resize(self, win_size):
        self.radius = self.radius / self.width * win_size[0]
        self.circle.csize = (2 * self.radius, 2 * self.radius)
        self.width, self.height = win_size

    def get_moving_dist(self):
        return self.dx, self.dy

    def on_update(self, dt):
        self.last_pos = [self.pos_x, self.pos_y]

        # integrate accel to get vel
        self.vel_x = self.ax * rescale_const
        self.vel_y = self.ay * rescale_const
        self.dx = self.vel_x * dt
        self.dy = self.vel_y * dt

        # integrate vel to get pos
        left_width = self.width * inner_boundary_factor
        right_width = self.width * (1-inner_boundary_factor)
        bottom_height = self.height * inner_boundary_factor
        top_height = self.height * (1-inner_boundary_factor)
        # x within boundary
        if self.radius + left_width <= self.pos_x + self.dx <= right_width - self.radius:
            self.pos_x += self.dx
            self.in_boundary_callback(True)
            self.touch_boundary_x = False

        # x left
        elif self.radius + left_width > self.pos_x + self.dx:
            self.pos_x = self.radius + left_width
            self.callback(-self.dx, None)
            self.in_boundary_callback(False)
            self.touch_boundary_x = True

        # x right
        else:  # self.pos_x + self.dx > Window.width - self.radius
            self.pos_x = right_width - self.radius
            self.callback(-self.dx, None)
            self.in_boundary_callback(False)
            self.touch_boundary_x = True

        # y within boundary
        if self.radius + bottom_height <= self.pos_y + self.dy <= top_height - self.radius:
            self.pos_y += self.dy
            self.in_boundary_callback(True)
            self.touch_boundary_y = False

        elif self.radius + bottom_height > self.pos_y + self.dy:
            self.pos_y = self.radius + bottom_height
            self.callback(None, -self.dy)
            self.in_boundary_callback(False)
            self.touch_boundary_y = True

        else:  # self.pos_y + self.dy > Window.height - self.radius
            self.pos_y = top_height - self.radius
            self.callback(None, -self.dy)
            self.in_boundary_callback(False)
            self.touch_boundary_y = True

        self.circle.cpos = np.array([self.pos_x, self.pos_y], dtype=float)
        self.rotate.origin = self.get_curr_pos()

        self.set_rotate_angle()
        return True

    def set_rotate_angle(self):
        self.last_angle = self.rotate.angle

        # counterclockwise --> positive, clockwise --> negative
        if self.dy == 0:
            if self.dx > 0:  # horizontally right
                self.rotate.angle = -90
            elif self.dx < 0:  # horizontally left
                self.rotate.angle = 90
        else:
            temp_angle = np.arctan(-self.dx / self.dy) * 180 / np.pi
            if self.dx < 0 and self.dy < 0:  # lower left
                self.rotate.angle = 180+temp_angle

            elif self.dx > 0 and self.dy < 0:  # lower right
                temp_angle = np.arctan(self.dx / self.dy) * 180 / np.pi
                self.rotate.angle = -(180 + temp_angle)

            elif self.dx == 0 and self.dy < 0:  # vertically down
                self.rotate.angle = -180
            else:
                self.rotate.angle = temp_angle
