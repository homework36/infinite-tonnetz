from math import radians, ceil
from struct import calcsize
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
rescale_const = Window.width / 2 / 5

class PhysBubble(InstructionGroup):
    def __init__(self, pos, r, color=(1,1,1), callback=None):
        super(PhysBubble, self).__init__()

        self.radius = r
        self.pos_x, self.pos_y = pos
        self.last_pos = pos
        self.vel_x, self.vel_y = 0., 0.

        self.add(PushMatrix())
        self.rotate = Rotate(angle=0)
        self.add(self.rotate)

        self.color = Color(rgb=color)
        self.add(self.color)

        self.circle = CEllipse(cpos=pos, csize=(2*r,2*r), segments = 40)
        self.add(self.circle)

        self.add(PopMatrix())

        self.circle.texture = Image(source='../img/icon.png').texture
        self.callback = callback
        self.last_angle = 0

        # self.width, self.height = Window.width, Window.height
        
    
    def set_accel(self, ax, ay):
        self.ax = ax
        self.ay = ay

    def get_last_pos(self):
        return self.last_pos

    def get_curr_pos(self):
        return [self.pos_x, self.pos_y]

    def on_resize(self, win_size):
        self.circle.csize = (2 * win_size[0] // 50,2 * win_size[0] // 50)

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
        # x left
        elif self.radius + left_width > self.pos_x + self.dx:
            self.pos_x = self.radius + left_width
            if self.callback:
                self.callback(-self.dx, None)
        # x right
        else: # self.pos_x + self.dx > Window.width - self.radius
            self.pos_x = right_width- self.radius
            if self.callback:
                self.callback(-self.dx, None)

        # y within boundary
        if self.radius + bottom_height <= self.pos_y + self.dy <= top_height - self.radius:
            self.pos_y += self.dy
        elif self.radius + bottom_height > self.pos_y + self.dy:
            self.pos_y = self.radius + bottom_height
            if self.callback:
                self.callback(None, -self.dy)

        else: # self.pos_y + self.dy > Window.height - self.radius
            self.pos_y = top_height - self.radius
            if self.callback:
                self.callback(None, -self.dy)

        self.circle.cpos = np.array([self.pos_x, self.pos_y], dtype=float)
        self.rotate.origin = self.get_curr_pos()

        self.set_rotate_angle()
        return True


    def set_rotate_angle(self):
        self.last_angle = self.rotate.angle
        
        # counterclockwise --> positive, clockwise --> negative
        if self.dy == 0:
            if self.dx > 0: # horizontally right
                self.rotate.angle = -90
            elif self.dx < 0: # horizontally left
                self.rotate.angle = 90
        else:
            temp_angle = np.arctan(-self.dx / self.dy) * 180 / np.pi
            if self.dx < 0 and self.dy < 0: # lower left
                self.rotate.angle = 180+temp_angle

            elif self.dx > 0 and self.dy < 0: # lower right
                temp_angle = np.arctan(self.dx / self.dy) * 180 / np.pi
                self.rotate.angle = -(180 + temp_angle)

            elif self.dx == 0 and self.dy < 0: # vertically down
                self.rotate.angle = -180
            else:
                self.rotate.angle = temp_angle