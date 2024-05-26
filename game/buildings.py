# File for all building classes

import pygame as pg


JOBNAMES = {'chopping': 'Woodcutter',
            'quarry': 'Quarryman',
            'wheatfield': 'Farmer',
            'well': 'Water Carrier',
            }

JOBIMGS = {'chopping': 'woodcutter',
            'quarry': 'quarryman',
            'wheatfield': 'farmer',
            'well': 'watercarrier',
            }

USERATES = {'water': .4,
            'wood': .2}

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
        self.percent_employed = 0.
        self.storage = {}
        self.production = {}
        self.capacity = 10
        self.currently_in_building = 0

    def is_full(self):
        return sum(self.storage.values()) + sum(self.production.values()) > self.capacity

    def update_percent_employed(self):
        self.percent_employed = round(len(self.workers) / self.workers_needed, 2)

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            if not self.is_full():
                for r in self.production:
                    self.storage[r] += self.production[r] * self.percent_employed
            # self.resourcemanager.resources['gold'] += 1
            self.resourcecooldown = pg.time.get_ticks()

    def check_currently_in_building(self):
        return len([w for w in self.workers if w.arrived_at_work])

class TownCenter(Building):

    def __init__(self, pos, loc, manager, worker_imgs):
        super().__init__(pos, loc, 'towncenter', 'towncenter', manager, 0)
        self.buildings = []
        self.num_buildings = {}
        self.villagers = []
        self.num_villagers = 0
        self.num_employed = 0
        self.housing_capacity = 0
        self.imgs = worker_imgs

    def get_unemployment_rate(self):
        return self.num_employed / self.num_villagers

    def update_quantity_demanded(self):
        for key in ['wood', 'water']:
            self.resourcemanager.quantity_demanded[key] = 4 * self.num_villagers

    def assign_worker_to_building(self, w, b):
        b.workers.append(w)
        if w.workplace is None:
            self.num_employed += 1
        else:
            w.workplace.workers.remove(w)
        w.workplace = b
        w.workplace.update_percent_employed()
        w.occupation = JOBNAMES[b.name]
        pg.transform.scale(self.imgs[JOBIMGS[b.name]],
                           (self.imgs[JOBIMGS[b.name]].get_width() * 2,
                            self.imgs[JOBIMGS[b.name]].get_height() * 2))
        w.image = pg.transform.scale(self.imgs[JOBIMGS[b.name]],
                                     (self.imgs[JOBIMGS[b.name]].get_width() * 2,
                                      self.imgs[JOBIMGS[b.name]].get_height() * 2))
        w.get_path_to_work()

    def assign_worker_to_house(self, w, h):
        h.occupants.append(w)
        for key in h.needs:
            h.needs[key] += 2
        h.num_occupants += 1
        w.home = h
        self.update_quantity_demanded()

    def get_buy_price(self, item):
        return int(self.resourcemanager.get_price(item))

    def get_sell_price(self, item):
        return int(self.resourcemanager.get_price(item, mode=1))

    def update(self):

        # assign villagers to houses if any are needed
        for w in self.villagers:
            if w.home is None:
                for bldg in self.buildings:
                    if bldg.name == 'house':
                        if bldg.has_vacancy():
                            self.assign_worker_to_house(w, bldg)
                            self.update_quantity_demanded()
                            break
            # assign villagers to workplaces if any are needed
            if w.workplace is None:
                for bldg in self.buildings:
                    if bldg.name != 'house':
                        if bldg.percent_employed < 1:
                            self.assign_worker_to_building(w, bldg)
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
        self.production = {'wood': 1}

    # def update(self):
    #     if pg.time.get_ticks() - self.resourcecooldown > 2000:
    #         if not self.is_full():
    #             self.storage['wood'] += 1
    #         # self.resourcemanager.resources['gold'] += 1
    #         self.resourcecooldown = pg.time.get_ticks()

class Well(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'well', 'well', manager, 1)
        self.storage = {'water': 0}
        self.production = {'water': 1}

    # def update(self):
    #     if pg.time.get_ticks() - self.resourcecooldown > 2000:
    #         if not self.is_full():
    #             self.storage['water'] += 1
    #         # self.resourcemanager.resources['gold'] += 1
    #         self.resourcecooldown = pg.time.get_ticks()

class Road(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'road', 'road', manager, 0)

class Quarry(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'quarry', 'quarry', manager, 2)
        self.storage = {'stone': 0}
        self.production = {'stone': 1}

    # def update(self):
    #     if pg.time.get_ticks() - self.resourcecooldown > 2000:
    #         if not self.is_full():
    #             self.storage['stone'] += 1
    #         # self.resourcemanager.resources['gold'] += 1
    #         self.resourcecooldown = pg.time.get_ticks()

class Wheatfield(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'wheatfield', 'wheatfield', manager, 2)
        self.storage = {'wheat': 0}
        self.production = {'wheat': 1}

    # def update(self):
    #     if pg.time.get_ticks() - self.resourcecooldown > 2000:
    #         if not self.is_full():
    #             self.storage['wheat'] += 1
    #         # self.resourcemanager.resources['gold'] += 1
    #         self.resourcecooldown = pg.time.get_ticks()

class House(Building):

    def __init__(self, pos, loc, manager):
        super().__init__(pos, loc, 'house', 'house', manager, 0)

        self.needs = {'wood': 0,
                      'water': 0}
        self.storage = {'wood': 0,
                        'water': 0}
        self.occupants = []
        self.num_occupants = 0
        self.housing_capacity = 5

    def get_needs(self):
        needs = {key: self.needs[key] - self.storage[key] for key in self.needs}
        return {key: needs[key] for key in needs if needs[key] > 0}

    def needs_goods(self):
        return any([self.storage[key] < self.needs[key] for key in self.needs])

    def has_vacancy(self):
        return self.num_occupants < self.housing_capacity

    def check_currently_in_building(self):
        return len([w for w in self.occupants if w.arrived_at_home])

    def update(self):
        now = pg.time.get_ticks()
        if now - self.resourcecooldown > 25000:
            self.resourcecooldown = now
            for key in self.storage:
                self.storage[key] = max([0, self.storage[key] - self.needs[key] * USERATES[key]])
