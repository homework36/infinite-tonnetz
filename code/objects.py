import sys, os
sys.path.insert(0, os.path.abspath('..'))
from imslib.gfxutil import topleft_label, resize_topleft_label, CEllipse, KFAnim, AnimGroup, CRectangle
from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.label import Label
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.uix.image import Image
import numpy as np


inner_boundary_factor = 0.2
rescale_const = Window.width / 6


class SpaceObject(InstructionGroup):
    def __init__(self, r, img_path, type, callback=None):
        super(SpaceObject, self).__init__()
        self.w, self.h = Window.width, Window.height
        self.color = Color(rgb=(1, 1, 1))
        self.add(self.color)

        # make star2 as background, random alpha value
        self.type = type
        if self.type == 'star2':
            self.color.a = np.random.random()

        self.r = r
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
            low=-45, high=45), origin=self.pos)
        self.add(self.rotate)
        self.add(self.rect)
        self.add(PopMatrix())
        self.time = 0
        self.on_update(0)

    def get_curr_pos(self):
        return self.pos

    def update_pos(self, dx, dy):
        self.pos[0] += dx
        self.pos[1] += dy
        self.rect.cpos = self.pos
        self.rotate.origin = self.pos
        self.on_update(0)

    def on_resize(self, win_size):
        self.r = self.r / self.w * win_size[0]
        self.rect.csize = (2*self.r, 2*self.r)

        self.pos[0] = self.pos[0] / self.w * win_size[0]
        self.pos[1] = self.pos[1] / self.h * win_size[1]
        self.rect.cpos = self.pos
        self.rotate.origin = self.pos
        self.w, self.h = win_size

    def on_update(self, dt):
        self.time += dt
        self.pos += self.vel * dt
        self.rect.cpos = self.pos

        if -inner_boundary_factor * self.w-self.r <= self.pos[0] <= \
            (1+inner_boundary_factor) * self.w+self.r and \
            -inner_boundary_factor * self.h-self.r <= self.pos[1] <= \
                (1+inner_boundary_factor) * self.h+self.r:
            return True

        # TODO: out of bound: reassign a position to pretend that a new object is created
        self.pos = [np.random.choice(np.concatenate((np.linspace(-0.1, -0.05, 20), np.linspace(1.05, 1.1, 20)), axis=None)) * Window.width,
                    np.random.choice(np.concatenate((np.linspace(-0.1, -0.05, 20), np.linspace(1.05, 1.1, 20)), axis=None)) * Window.height]
        self.rect.cpos = self.pos
        self.rotate.origin = self.pos

        return True


class PhysBubble(InstructionGroup):
    def __init__(self, pos, r, color=(1, 1, 1), callback=None, in_boundary=None):
        super(PhysBubble, self).__init__()

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

        # self.width, self.height = Window.width, Window.height

    def set_accel(self, ax, ay):
        self.ax = ax
        self.ay = ay

    def get_last_pos(self):
        return self.last_pos

    def get_curr_pos(self):
        return [self.pos_x, self.pos_y]

    def on_resize(self, win_size):
        self.radius = win_size[0] // 25
        self.circle.csize = (2 * self.radius, 2 * self.radius)

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
        width, height = Window.width, Window.height
        left_width = width * inner_boundary_factor
        right_width = width * (1-inner_boundary_factor)
        bottom_height = height * inner_boundary_factor
        top_height = height * (1-inner_boundary_factor)
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
