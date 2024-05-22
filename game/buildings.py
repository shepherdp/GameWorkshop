# File for all building classes

import pygame as pg


class Building:

    def __init__(self, pos, loc, imgname, bldgname, resourcemanager):
        self.image = pg.image.load(f'assets\\graphics\\{imgname}.png').convert_alpha()
        self.name = bldgname
        self.rect = self.image.get_rect(topleft=pos)
        self.loc = loc
        self.resourcemanager = resourcemanager
        self.resourcemanager.apply_cost(self.name)
        self.resourcecooldown = pg.time.get_ticks()

    def update(self):
        pass

class TownCenter(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'towncenter', 'towncenter', manager)

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            self.resourcemanager.resources['wood'] += 2
            self.resourcemanager.resources['water'] += 2
            self.resourcemanager.resources['gold'] += 2
            self.resourcecooldown = pg.time.get_ticks()

class ChoppingBlock(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'choppingblock', 'chopping', manager)

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            self.resourcemanager.resources['wood'] += 1
            self.resourcemanager.resources['gold'] += 1
            self.resourcecooldown = pg.time.get_ticks()

class Well(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'well', 'well', manager)

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            self.resourcemanager.resources['water'] += 1
            self.resourcemanager.resources['gold'] += 1
            self.resourcecooldown = pg.time.get_ticks()

class Road(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'road', 'road', manager)

class Quarry(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'quarry', 'quarry', manager)

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            self.resourcemanager.resources['stone'] += 1
            self.resourcemanager.resources['gold'] += 1
            self.resourcecooldown = pg.time.get_ticks()

class Wheatfield(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'wheatfield', 'wheatfield', manager)

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            self.resourcemanager.resources['wheat'] += 1
            self.resourcemanager.resources['gold'] += 1
            self.resourcecooldown = pg.time.get_ticks()
