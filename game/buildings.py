# File for all building classes

import pygame as pg


JOBNAMES = {'chopping': 'Woodcutter',
            'quarry': 'Quarryman',
            'wheatfield': 'Farmer',
            'well': 'Water Carrier',
            }

class Building:

    def __init__(self, pos, loc, imgname, bldgname, resourcemanager, workers_needed):
        self.image = pg.image.load(f'assets\\graphics\\buildings\\{imgname}.png').convert_alpha()
        self.name = bldgname
        self.rect = self.image.get_rect(topleft=pos)
        self.loc = loc
        self.resourcemanager = resourcemanager

        if not self.name == 'towncenter':
            self.resourcemanager.apply_cost(self.name)

        self.resourcecooldown = pg.time.get_ticks()
        self.workers_needed = workers_needed
        self.workers = []
        self.storage = {}
        self.capacity = 10

    def is_full(self):
        return sum(self.storage.values()) >= self.capacity

    def update(self):
        pass

class TownCenter(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'towncenter', 'towncenter', manager, 0)
        self.buildings = []
        self.num_buildings = {}
        self.villagers = []
        self.housing_capacity = 5

    def update(self):

        # assign villagers to workplaces if any are needed
        worker = None
        for v in self.villagers:
            if v.workplace is None:
                worker = v
                break
        if worker is not None:
            for bldg in self.buildings:
                if len(bldg.workers) < bldg.workers_needed:
                    bldg.workers.append(worker)
                    worker.workplace = bldg
                    worker.occupation = JOBNAMES[bldg.name]
                    worker.get_path_to_work()
                    break

        # if pg.time.get_ticks() - self.resourcecooldown > 2000:
        #     self.resourcemanager.resources['wood'] += 2
        #     self.resourcemanager.resources['water'] += 2
        #     self.resourcemanager.resources['gold'] += 2
        #     self.resourcecooldown = pg.time.get_ticks()

class ChoppingBlock(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'choppingblock', 'chopping', manager, 2)
        self.storage = {'wood': 0}

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            if not self.is_full():
                self.storage['wood'] += 1
            # self.resourcemanager.resources['gold'] += 1
            self.resourcecooldown = pg.time.get_ticks()

class Well(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'well', 'well', manager, 1)
        self.storage = {'water': 0}

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            if not self.is_full():
                self.storage['water'] += 1
            # self.resourcemanager.resources['gold'] += 1
            self.resourcecooldown = pg.time.get_ticks()

class Road(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'road', 'road', manager, 0)

class Quarry(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'quarry', 'quarry', manager, 2)
        self.storage = {'stone': 0}

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            if not self.is_full():
                self.storage['stone'] += 1
            # self.resourcemanager.resources['gold'] += 1
            self.resourcecooldown = pg.time.get_ticks()

class Wheatfield(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'wheatfield', 'wheatfield', manager, 2)
        self.storage = {'wheat': 0}

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            if not self.is_full():
                self.storage['wheat'] += 1
            # self.resourcemanager.resources['gold'] += 1
            self.resourcecooldown = pg.time.get_ticks()

class House(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'house', 'house', manager, 0)

    def update(self):
        pass