# File for all building classes

import pygame as pg


class Building:

    def __init__(self, pos, imgname, bldgname, resourcemanager):
        self.image = pg.image.load(f'assets\\graphics\\{imgname}.png').convert_alpha()
        self.name = bldgname
        self.rect = self.image.get_rect(topleft=pos)
        self.resourcemanager = resourcemanager
        self.resourcemanager.apply_cost(self.name)
        self.resourcecooldown = pg.time.get_ticks()

    def update(self):
        pass

class ChoppingBlock(Building):

    def __init__(self, pos, manager):
        super().__init__(pos, 'choppingblock', 'chopping', manager)

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            self.resourcemanager.resources['wood'] += 1
            self.resourcecooldown = pg.time.get_ticks()

class Well(Building):

    def __init__(self, pos, manager):
        super().__init__(pos, 'well', 'well', manager)

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            self.resourcemanager.resources['water'] += 1
            self.resourcecooldown = pg.time.get_ticks()
