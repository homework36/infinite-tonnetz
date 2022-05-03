import sys, os
sys.path.insert(0, os.path.abspath('..'))
from helper_function import *
import numpy as np
from kivy.graphics import Color, Line
from kivy.graphics.instructions import InstructionGroup
from kivy.core.window import Window
from math import ceil


sq3 = np.sqrt(3)
class StarLine(InstructionGroup):
    '''Create lines that forms the tonnetz, passing the given point only! '''

    def __init__(self, point, seg_length, total_lines, trans_type='p'):
        super(StarLine, self).__init__()
        self.type = trans_type.lower()
        assert self.type in ['p', 'r', 'l']
        self.original_pt = point
        self.cx, self.cy = point
        self.cx_last, self.cy_last = self.cx, self.cy
        self.seg = seg_length
        self.seg_height = self.seg*sq3/2
        self.end1, self.end2 = self.calc_line()
        self.line = Line(
            points=(self.end1[0], self.end1[1], self.end2[0], self.end2[1]))
        self.intersect = intersect
        self.width, self.height = Window.width, Window.height

        self.last_cross_pt = None
        self.color = Color(1, 1, 1)
        self.color.a = 0.3
        self.add(self.color)
        self.color_change_elapse = 0
        self.add(self.line)
        self.threshold = 10

        if self.type == 'p':
            self.limit = self.seg_height * (total_lines // 2)
            self.reset_dist = self.seg_height * total_lines
        else:
            self.limit = self.seg * (total_lines // 2)
            self.reset_dist = self.seg * total_lines
            # self.cy = 0
    def update_line(self, dx, dy):
        self.cx += dx
        self.cy += dy

        if self.type == 'p':
            if dy > 0 and self.cy > self.limit:
                self.cy -= self.reset_dist
            elif dy < 0 and self.cy < -self.limit:
                self.cy += self.reset_dist
        
        else:
            if dy > 0 and self.cy / sq3 * 2 > self.limit:
                self.cy -= self.reset_dist / 2 * sq3
                
            elif dy < 0 and self.cy / sq3 * 2 < -self.limit:
                self.cy += self.reset_dist / 2 * sq3

            elif dx > 0 and self.cx > self.limit:
                    self.cx -= self.reset_dist
                    
            elif dx < 0 and self.cx < -self.limit:
                    self.cx += self.reset_dist

        self.end1, self.end2 = self.calc_line()
        self.line.points = (
            self.end1[0], self.end1[1], self.end2[0], self.end2[1])

    def calc_line(self):
        width, height = Window.width, Window.height

        if self.type == 'p':
            end1 = [0, self.cy]
            end2 = [width, self.cy]
            return np.array(end1), np.array(end2)
        else:
            dist_top = (height-self.cy)/sq3
            dist_bottom = self.cy/sq3
            if self.type == 'r':
                end_top = [self.cx-dist_top, height]
                end_bottom = [self.cx+dist_bottom, 0]
            else: # self.type == 'l'
                end_top = [self.cx+dist_top, height]
                end_bottom = [self.cx-dist_bottom, 0]
            return np.array(end_top), np.array(end_bottom)

    def on_resize(self, win_size):
        self.width, self.height = win_size
        self.end1, self.end2 = self.calc_line()
        self.line.points = self.end1[0], self.end1[1], self.end2[0], self.end2[1]

    def on_update(self, dt):
        pass

    def check_cross(self, cur_pos, last_pos):
        '''pos: current position of main object
           last_pos: last position of main object'''
        self.color_change_elapse += 1

        if self.cx != self.cx_last or self.cy != self.cy_last:
            moving = True
        else:
            moving = False

        cur_pos = np.array(cur_pos)
        # avoid duplicate crossing

        if self.type == 'p':
            if cur_pos[1] > self.cy and last_pos[1] < self.cy:
                if self.last_cross_pt is not None and np.linalg.norm(cur_pos-self.last_cross_pt) <= self.threshold and moving:
                    self.change_color(default=False)
                    return False
                else:
                    self.last_cross_pt = cur_pos
                    self.change_color()
                    self.cx_last, self.cy_last = self.cx, self.cy
                    return True
            elif cur_pos[1] < self.cy and last_pos[1] > self.cy:
                if self.last_cross_pt is not None and np.linalg.norm(cur_pos-self.last_cross_pt) <= self.threshold and moving:
                    self.change_color(default=False)
                    self.cx_last, self.cy_last = self.cx, self.cy
                    return False
                else:
                    self.last_cross_pt = cur_pos
                    self.change_color()
                    self.cx_last, self.cy_last = self.cx, self.cy
                    return True
            else:
                self.last_cross_pt = None
                self.change_color(default=False)
                self.cx_last, self.cy_last = self.cx, self.cy
                return False
        else:
            if self.intersect(cur_pos, last_pos, self.end1, self.end2):
                if self.last_cross_pt is not None and np.linalg.norm(cur_pos-self.last_cross_pt) <= self.threshold and moving:
                    self.change_color(default=False)
                    return False
                else:
                    self.last_cross_pt = cur_pos
                    self.change_color()
                    self.cx_last, self.cy_last = self.cx, self.cy
                    return True
            else:
                self.last_cross_pt = None
                self.change_color(default=False)
                self.cx_last, self.cy_last = self.cx, self.cy
                return False

    def change_color(self, default=True):
        if default:
            self.color.rgb = (.7, .6, .2)
        else:
            if self.color_change_elapse >= 30:
                self.color_change_elapse = 0
                self.color.rgb = (1., 1., 1.)


# create tonnetz
class Tonnetz(InstructionGroup):
    def __init__(self, seg_length, origin=[300, 300], callback=None):
        '''create full tonnetz with a given seg_length and origin'''
        super(Tonnetz, self).__init__()
        self.width, self.height = Window.width, Window.height
        self.seg = seg_length
        self.seg_height = self.seg*sq3/2

        self.origin = np.array(origin)
        self.origin[0] %= self.seg * 2
        self.origin[1] %= self.seg_height * 2

        self.line_list_p = []
        self.line_list_r = []
        self.line_list_l = []
        self.line_list = []

        self.make_lines()
        self.last_origin = self.origin.copy()
        self.callback = callback

    def make_lines(self, p=True, rl=True):
        if p:
            self.make_lines_p()

        if rl:
            self.make_lines_rl()

        self.line_list = self.line_list_p + self.line_list_r + self.line_list_l

    def make_lines_p(self):
        for line in self.line_list_p:
            if line in self.children:
                self.children.remove(line)

        self.line_list_p = []
        self.calc_p_num_points()

        for i in range(int(self.num_p_p)+1):  # 7 up + 1 middle
            self.line_list_p.append(
                StarLine((self.origin[0], self.origin[1]+self.seg_height*i), self.seg, self.num_p_p+self.num_p_m+1, 'p'))

        for i in range(1, int(self.num_p_m)+1):  # 7 down
            self.line_list_p.append(
                StarLine((self.origin[0], self.origin[1]-self.seg_height*i), self.seg, self.num_p_p+self.num_p_m+1, 'p'))

        for line in self.line_list_p:
            self.add(line)

        self.p_num = len(self.line_list_p)
        self.p_limit = self.seg_height * (self.p_num // 2)

    def calc_p_num_points(self):
        self.num_p_p = ceil((self.height)/self.seg_height) + 4
        self.num_p_m = ceil(self.height/self.seg_height) + 4

    def calc_rl_num_points(self):
        # append self.height/sq3/self.seg to left
        self.num_l_p = ceil((self.width+self.height/sq3)/self.seg) + 2
        self.num_l_m = ceil((self.width+self.height/sq3)/self.seg) + 3

        # append self.height/sq3/self.seg to right
        self.num_r_p = ceil((self.width+self.height/sq3)/self.seg) + 3
        self.num_r_m = ceil((self.width+self.height/sq3)/self.seg) + 2

    def make_lines_rl(self):
        for line in self.line_list_r:
            if line in self.children:
                self.children.remove(line)
        for line in self.line_list_l:
            if line in self.children:
                self.children.remove(line)

        self.line_list_r = []
        self.line_list_l = []

        self.calc_rl_num_points()

        for i in range(int(self.num_l_p)+1):
            self.line_list_l.append(
                StarLine((self.origin[0]+self.seg*i, self.origin[1]), self.seg, self.num_l_p+self.num_l_m+1, 'l'))
        for i in range(1, int(self.num_l_m)+1):
            self.line_list_l.append(
                StarLine((self.origin[0]-self.seg*i, self.origin[1]), self.seg, self.num_l_p+self.num_l_m+1, 'l'))

        for i in range(int(self.num_r_p)+1):
            self.line_list_r.append(
                StarLine((self.origin[0]+self.seg*i, self.origin[1]), self.seg, self.num_r_p+self.num_r_m+1, 'r'))
        for i in range(1, int(self.num_r_m)+1):
            self.line_list_r.append(
                StarLine((self.origin[0]-self.seg*i, self.origin[1]), self.seg, self.num_r_p+self.num_r_m+1, 'r'))

        for line in self.line_list_r:
            self.add(line)

        for line in self.line_list_l:
            self.add(line)

        self.l_num = len(self.line_list_l)
        self.r_num = len(self.line_list_r)

        self.l_limit = self.seg * (self.l_num // 2)
        self.r_limit = self.seg * (self.r_num // 2)

    def on_resize(self, win_size):
        # remove first
        for line in self.children:
            self.children.remove(line)
        # rescale  segment length
        old_width = self.width
        self.width, self.height = win_size
        self.seg *= self.width/old_width
        self.seg_height = self.seg*sq3/2
        self.origin[0] %= self.seg * 2
        self.origin[1] %= self.seg_height * 2
        self.last_origin = self.origin.copy()
        self.make_lines()

    def on_boundary(self, dx, dy):
        diffx, diffy = 0, 0
        if dx or dy:
            self.last_origin = self.origin.copy()

        if dx:
            self.origin[0] += dx
            diffx = dx
            # more than window size, need to mod
            if self.origin[0] > self.seg * 2:
                self.origin[0] -= self.seg * 2

            elif self.origin[0] < 0:
                self.origin[0] += self.seg * 2

        if dy:
            self.origin[1] += dy
            diffy = dy

            # more than window size, need to mod
            if self.origin[1] > self.seg_height * 2:
                self.origin[1] -= self.seg_height * 2

            elif self.origin[1] < 0:
                self.origin[1] += self.seg_height * 2

        if dx or dy:
            self.update_lines(diffx, diffy)

    def push_l(self, right):
        '''make the right most line to the left most'''
        line_l_x = [line.cx for line in self.line_list_l]
        self.l_limit = self.seg * (self.l_num // 2)
        if right:
            line_to_be_reset = np.argmax(np.array(line_l_x))
            dist = -self.l_num * self.seg
            line = self.line_list_l[line_to_be_reset]
            if line.cx < self.l_limit:
                return
        else:
            line_to_be_reset = np.argmin(np.array(line_l_x))
            dist = self.l_num * self.seg
            line = self.line_list_l[line_to_be_reset]
            if line.cx > -self.l_limit:
                return

        line.update_line(dist, 0)

    def push_r(self, right):
        '''make the right most line to the left most'''
        line_r_x = [line.cx for line in self.line_list_r]
        self.r_limit = self.seg * (self.r_num // 2)
        if right:
            line_to_be_reset = np.argmax(np.array(line_r_x))
            dist = -self.r_num * self.seg
            line = self.line_list_r[line_to_be_reset]
            if line.cx < self.r_limit:
                return
        else:
            line_to_be_reset = np.argmin(np.array(line_r_x))
            dist = self.r_num * self.seg
            line = self.line_list_r[line_to_be_reset]
            if line.cx > -self.r_limit:
                return

        line.update_line(dist, 0)

    def push_p(self, up):
        '''make the right most line to the left most'''
        line_p_y = [line.cy for line in self.line_list_p]
        if up:
            line_to_be_reset = np.argmax(np.array(line_p_y))
            dist = -self.p_num * self.seg_height
            line = self.line_list_p[line_to_be_reset]
            if line.cy < self.p_limit:
                return
        else:
            line_to_be_reset = np.argmin(np.array(line_p_y))
            dist = self.p_num * self.seg_height
            line = self.line_list_p[line_to_be_reset]
            if line.cy > -self.p_limit:
                return

        line.update_line(0, dist)

    def update_lines(self, diffx, diffy):
        for line in self.line_list:
            line.update_line(diffx, diffy)

    def on_update(self):
        pass

    def check_lines(self, last_pos, dx=0, dy=0):

        cur_pos = [last_pos[0]+dx, last_pos[1]+dy]
        for line in self.line_list_p:
            if line.check_cross(cur_pos, last_pos):
                self.callback('p')

        for line in self.line_list_r:
            if line.check_cross(cur_pos, last_pos):
                self.callback('r')

        for line in self.line_list_l:
            if line.check_cross(cur_pos, last_pos):
                self.callback('l')

    def modify_seq_length(self, val):
        temp_seg = self.seg + val
        self.seg = max(400, min(self.width/1.5, temp_seg))
        self.seg_height = self.seg*sq3/2

        self.origin[0] %= self.seg * 2
        self.origin[1] %= self.seg_height * 2

        self.p_limit = self.seg_height * (self.p_num // 2)
        self.l_limit = self.seg * (self.l_num // 2)
        self.r_limit = self.seg * (self.r_num // 2)

        self.make_lines()
