# Camera class

import pygame as pg


class Camera:

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.scroll = pg.Vector2(0, 0)
        self.dx = 0
        self.dy = 0

        self.speed = 25

    def update(self):
        mouse_pos = pg.mouse.get_pos()
        if mouse_pos[0] > self.width * .98:
            self.dx = -self.speed
        elif mouse_pos[0] < self.width * .02:
            self.dx = self.speed
        else:
            self.dx = 0

        if mouse_pos[1] > self.height * .98:
            self.dy = -self.speed
        elif mouse_pos[1] < self.height * .02:
            self.dy = self.speed
        else:
            self.dy = 0

        self.scroll.x += self.dx
        self.scroll.y += self.dy

    def get_state_for_savefile(self):
        return f'w={self.width}#h={self.height}#scroll=({self.scroll.x},{self.scroll.y})#dx={self.dx}#dy={self.dy}\n'