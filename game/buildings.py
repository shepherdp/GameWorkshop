# File for all building classes

import pygame as pg


JOBNAMES = {'chopping': 'Woodcutter',
            'quarry': 'Quarryman',
            'wheatfield': 'Farmer',
            'well': 'Water Carrier',
            'workbench': 'Tool Maker',
            'market': 'Merchant'
            }

JOBIMGS = {'chopping': 'woodcutter',
            'quarry': 'quarryman',
            'wheatfield': 'farmer',
            'well': 'watercarrier',
            'workbench': 'farmer',
            'market': 'merchant'
            }

USERATES = {'water': .4,
            'wood': .2}

class Building:

    def __init__(self, pos, loc, imgname, bldgname, resourcemanager, workers_needed, unique_id):
        self.image = pg.image.load(f'assets\\graphics\\buildings\\{imgname}.png').convert_alpha()
        self.name = bldgname
        self.rect = self.image.get_rect(topleft=pos)
        self.loc = loc
        self.resourcemanager = resourcemanager
        self.id = unique_id

        if not self.name == 'towncenter':
            self.resourcemanager.apply_cost(self.name)

        self.resourcecooldown = pg.time.get_ticks()
        self.workers_needed = workers_needed
        self.workers = []
        self.percent_employed = 0.
        self.storage = {}
        self.production = {}
        self.consumption = {}
        self.capacity = 10
        self.currently_in_building = 0

    def is_full(self):
        d = {key: val for key, val in self.storage.items() if key in self.production}
        return sum(d.values()) + sum(self.production.values()) > self.capacity

    def update_percent_employed(self):
        if self.name != 'road':
            self.percent_employed = round(len(self.workers) / self.workers_needed, 2)

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            if not self.is_full():
                for r in self.production:
                    self.storage[r] += self.production[r] * self.percent_employed
            else:
                # top off any remaining capacity space to avoid fractional leftovers
                for r in self.production:
                    self.storage[r] = self.capacity
            self.storage = {key: round(self.storage[key], 2) for key in self.storage}
            # self.resourcemanager.resources['gold'] += 1
            self.resourcecooldown = pg.time.get_ticks()

    def check_currently_in_building(self):
        return len([w for w in self.workers if w.arrived_at_work])

    def get_state_for_savefile(self):
        ret = ''
        ret += f'id={self.id}#'
        ret += f'name={self.name}#'
        ret += f'loc={self.loc}#'
        ret += '\n'
        return ret

class BaseProductionBuilding(Building):

    def __init__(self, pos, loc, img_name, bldg_name, manager, num_workers, unique_id):
        super().__init__(pos, loc, img_name, bldg_name, manager, num_workers, unique_id)

    def needs_goods(self):
        return False

class RefinedProductionBuilding(BaseProductionBuilding):

    def __init__(self, pos, loc, img_name, bldg_name, manager, num_workers, unique_id):
        super().__init__(pos, loc, img_name, bldg_name, manager, num_workers, unique_id)

    def needs_goods(self):
        return any([self.storage[key] < self.consumption[key] * 10 for key in self.consumption])

    def goods_needed(self):
        return {key: int(self.consumption[key] * 10 - self.storage[key]) + 1 for key in self.consumption}

class Housing(Building):

    def __init__(self):
        pass

class TownBuilding(Building):

    def __init__(self):
        pass

class TownCenter(Building):

    def __init__(self, pos, loc, resourcemanager, techmanager, worker_imgs, unique_id):
        super().__init__(pos, loc, 'towncenter', 'towncenter', resourcemanager, 0, unique_id)
        self.buildings = []
        self.num_buildings = {}
        self.villagers = []
        self.num_villagers = 0
        self.num_employed = 0
        self.housing_capacity = 0
        self.imgs = worker_imgs
        self.techmanager = techmanager

    def get_unemployment_rate(self):
        return self.num_employed / self.num_villagers

    def update_quantity_demanded(self):
        for key in ['wood', 'water']:
            self.resourcemanager.quantity_demanded[key] = 4 * self.num_villagers + 2
        for key in self.resourcemanager.quantity_demanded:
            if key not in ['wood', 'water']:
                self.resourcemanager.quantity_demanded[key] = self.num_villagers + 2
            else:
                self.resourcemanager.quantity_demanded[key] += self.num_villagers + 2

    def get_current_demand(self):
        d = []
        for item in self.resourcemanager.resources:
            if item == 'gold':
                continue
            d.append([self.resourcemanager.quantity_demanded[item] - self.resourcemanager.resources[item], item])
        return sorted(d, reverse=True)

    def get_stranded_merchant(self):
        if 'market' in self.num_buildings:
            for b in self.buildings:
                if b.name == 'market':
                    if b.workers[0].targettown is None:
                        return b.workers[0]

    def assign_worker_to_building(self, w, b):
        b.workers.append(w)
        if w.workplace is None:
            self.num_employed += 1
        else:
            # make sure worker doesn't show up in two buildings
            w.workplace.workers.remove(w)
        w.workplace = b
        w.workplace.update_percent_employed()
        w.occupation = JOBNAMES[b.name]
        if JOBNAMES[b.name] not in w.skills:
            w.skills[JOBNAMES[b.name]] = 0
        if w.occupation == 'Merchant':
            w.gold = 500
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
                    if bldg.name not in ['house', 'road']:
                        if bldg.percent_employed < 1:
                            self.assign_worker_to_building(w, bldg)
                            break

        self.techmanager.update_research_progress()

        if pg.time.get_ticks() - self.resourcecooldown > 10000:
            self.resourcemanager.resources['wood'] = max([self.resourcemanager.resources['wood'] - 2, 0])
            self.resourcemanager.resources['water'] = max([self.resourcemanager.resources['water'] - 2, 0])
            self.resourcemanager.resources['stone'] = max([self.resourcemanager.resources['stone'] - 2, 0])
            self.resourcecooldown = pg.time.get_ticks()

class ChoppingBlock(BaseProductionBuilding):

    def __init__(self, pos, loc, manager, unique_id):
        super().__init__(pos, loc, 'choppingblock', 'chopping', manager, 2, unique_id)
        self.storage = {'wood': 0}
        self.production = {'wood': 1}

class Workbench(RefinedProductionBuilding):

    def __init__(self, pos, loc, manager, unique_id):
        super().__init__(pos, loc, 'workbench', 'workbench', manager, 2, unique_id)
        self.storage = {'simpletools': 0, 'wood': 1, 'stone': 1}
        self.production = {'simpletools': 1}
        self.consumption = {'wood': .1, 'stone': .1}

    def update(self):
        if pg.time.get_ticks() - self.resourcecooldown > 2000:
            if not self.is_full():
                if all([self.storage[key] > self.consumption[key] for key in self.consumption]):
                    for key in self.consumption:
                        self.storage[key] -= self.consumption[key]
                    for key in self.production:
                        self.storage[key] += self.production[key]
                self.storage = {key: round(self.storage[key], 2) for key in self.storage}

            # self.resourcemanager.resources['gold'] += 1
            self.resourcecooldown = pg.time.get_ticks()


    # def update(self):
    #     if pg.time.get_ticks() - self.resourcecooldown > 2000:
    #         if not self.is_full():
    #             self.storage['wood'] += 1
    #         # self.resourcemanager.resources['gold'] += 1
    #         self.resourcecooldown = pg.time.get_ticks()

class Well(BaseProductionBuilding):

    def __init__(self, pos, loc, manager, unique_id):
        super().__init__(pos, loc, 'well', 'well', manager, 1, unique_id)
        self.storage = {'water': 0}
        self.production = {'water': 1}

    # def update(self):
    #     if pg.time.get_ticks() - self.resourcecooldown > 2000:
    #         if not self.is_full():
    #             self.storage['water'] += 1
    #         # self.resourcemanager.resources['gold'] += 1
    #         self.resourcecooldown = pg.time.get_ticks()

class Road(Building):

    def __init__(self, pos, loc, manager, unique_id):
        super().__init__(pos, loc, 'road', 'road', manager, 0, unique_id)

class Quarry(BaseProductionBuilding):

    def __init__(self, pos, loc, manager, unique_id):
        super().__init__(pos, loc, 'quarry', 'quarry', manager, 2, unique_id)
        self.storage = {'stone': 0}
        self.production = {'stone': 1}

    # def update(self):
    #     if pg.time.get_ticks() - self.resourcecooldown > 2000:
    #         if not self.is_full():
    #             self.storage['stone'] += 1
    #         # self.resourcemanager.resources['gold'] += 1
    #         self.resourcecooldown = pg.time.get_ticks()

class Wheatfield(BaseProductionBuilding):

    def __init__(self, pos, loc, manager, unique_id):
        super().__init__(pos, loc, 'wheatfield', 'wheatfield', manager, 2, unique_id)
        self.storage = {'wheat': 0}
        self.production = {'wheat': 1}

    # def update(self):
    #     if pg.time.get_ticks() - self.resourcecooldown > 2000:
    #         if not self.is_full():
    #             self.storage['wheat'] += 1
    #         # self.resourcemanager.resources['gold'] += 1
    #         self.resourcecooldown = pg.time.get_ticks()

class House(Building):

    def __init__(self, pos, loc, manager, unique_id):
        super().__init__(pos, loc, 'house', 'house', manager, 0, unique_id)

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

class Market(Building):

    def __init__(self, pos, loc, manager, unique_id):
        super().__init__(pos, loc, 'market', 'market', manager, 1, unique_id)

    def needs_goods(self):
        return False