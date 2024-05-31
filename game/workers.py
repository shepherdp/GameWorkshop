
import pygame as pg
import random
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from networkx import dijkstra_path


class Worker:

    def __init__(self, tile, world, unique_id):
        self.world = world
        self.world.entities.append(self)
        self.name = "worker"
        image = pg.image.load("assets/graphics/characters/beggar.png").convert_alpha()
        self.image = pg.transform.scale(image, (image.get_width()*2, image.get_height()*2))
        self.tile = tile
        self.moving = False
        self.path_index = 0
        self.town = None
        self.targettown = None
        self.workplace = None
        self.home = None
        self.selected = False
        self.occupation = 'Wanderer'
        self.skills = {}
        self.gold = 5
        self.just_sold = []
        self.offsets = [0, 0]
        self.offset_amounts = [0, 0]
        self.animationtimer = pg.time.get_ticks()
        self.id = unique_id

        self.energy = 100
        self.energycooldown = pg.time.get_ticks()
        self.skillcooldown = pg.time.get_ticks()

        self.inventory = {}

        self.current_task = 'wandering'

        self.going_to_work = False
        self.arrived_at_work = False
        self.going_to_towncenter = False
        self.arrived_at_towncenter = False
        self.going_home = False
        self.arrived_at_home = False
        self.collecting_for_work = False
        self.collected_for_work = False

        # pathfinding
        self.world.workers[tile["grid"][0]][tile["grid"][1]] = self
        self.move_timer = pg.time.get_ticks()
        self.create_path()

    def create_path(self):

        newtown = self.world.find_town_with_vacancy()
        if newtown is None:
            self.get_random_path()
        else:
            self.assign_town(newtown)
            self.occupation = 'Beggar'
            self.get_path_to_towncenter()

    def get_path_to_work(self):
        self.start = (self.tile["grid"][0], self.tile["grid"][1])
        self.end = self.workplace.loc
        self.path = dijkstra_path(self.world.world_network, self.start, self.end)
        self.path_index = 0
        self.moving = True

        self.reset_travel_vars()
        self.going_to_work = True

    def get_path_to_towncenter(self):
        self.start = (self.tile["grid"][0], self.tile["grid"][1])
        self.end = self.town.loc
        self.path = dijkstra_path(self.world.world_network, self.start, self.end)
        self.path_index = 0
        self.moving = True

        self.reset_travel_vars()
        self.going_to_towncenter = True

    def get_path_to_targettown(self):
        self.start = (self.tile["grid"][0], self.tile["grid"][1])
        self.end = self.targettown.loc
        self.path = dijkstra_path(self.world.world_network, self.start, self.end)
        self.path_index = 0
        self.moving = True

        self.reset_travel_vars()
        self.going_to_towncenter = True

    def get_path_to_home(self):
        self.start = (self.tile["grid"][0], self.tile["grid"][1])
        self.end = self.home.loc
        self.path = dijkstra_path(self.world.world_network, self.start, self.end)
        self.path_index = 0
        self.moving = True

        self.reset_travel_vars()
        self.going_home = True

    def get_random_path(self):
        self.start = (self.tile["grid"][0], self.tile["grid"][1])
        found = False
        while not found:
            self.end = self.world.get_random_position()
            try:
                self.path = dijkstra_path(self.world.world_network, self.start, self.end)
                found = True
            except:
                continue
        self.path_index = 0
        self.moving = True

        self.reset_travel_vars()

    def change_tile(self, new_tile):
        self.world.workers[self.tile["grid"][0]][self.tile["grid"][1]] = None
        self.world.workers[new_tile['grid'][0]][new_tile['grid'][1]] = self
        self.tile = self.world.world[new_tile['grid'][0]][new_tile['grid'][1]]
        if self.selected:
            self.world.selected_worker = self.tile['grid']

    def check_end_of_path(self):
        # if worker reaches the destination, stop if it is a building and make a new random path if they
        # are still just wandering
        # print('a')
        if self.path_index == len(self.path) - 1:
            self.moving = False
            if self.going_to_towncenter:
                # print('b')
                self.going_to_towncenter = False
                self.arrived_at_towncenter = True
                self.current_task = 'At Town Center'
            if self.going_to_work:
                # print('c')
                self.going_to_work = False
                self.arrived_at_work = True
                self.current_task = 'Working'
            if self.going_home:
                # print('d')
                self.going_home = False
                self.arrived_at_home = True
                self.current_task = 'Resting'

        self.check_needs_town()

    def check_needs_town(self):
        # if not assigned to a town, look for one
        # if none are available, just keep moving
        if self.town is None:
            newtown = self.world.find_town_with_vacancy()
            if newtown is not None:
                self.assign_town(newtown)
            else:
                self.get_random_path()

    def check_work_needs_goods(self):
        # print('checking', self.going_to_towncenter, self.going_home, self.going_to_work, self.arrived_at_towncenter,
        #       self.arrived_at_home, self.arrived_at_work, self.collecting_for_work)
        if self.collected_for_work or self.collecting_for_work:
            return
        if self.workplace.needs_goods():
            # print('xxx')
            self.collecting_for_work = True
            if not self.going_to_towncenter:
                self.reset_travel_vars()
                self.going_to_towncenter = True
                self.get_path_to_towncenter()

    def assign_town(self, newtown):
        self.town = newtown
        self.town.villagers.append(self)
        self.get_path_to_towncenter()
        self.going_to_towncenter = True
        self.town.num_villagers += 1

    def move(self):
        now = pg.time.get_ticks()
        if now - self.animationtimer > 100:
            self.offsets[0] += self.offset_amounts[0]
            self.offsets[1] += self.offset_amounts[1]
            # print(self.tile['render_pos'][0] + self.offsets[0], self.tile['render_pos'][0] + self.offsets[0])
            self.animationtimer = pg.time.get_ticks()
        if now - self.move_timer > 500:
            # print('changing tile')
            # print(self.id)
            # print(self.path)
            # print(self.path_index)
            # update position in the world
            # try:
            new_pos = self.path[self.path_index]
            # except:
            #     print(self.path)
            #     print(self.path_index)
                # sys.exit()
            new_tile = self.world.world[new_pos[0]][new_pos[1]]
            # print(self.tile['render_pos'], new_tile['render_pos'])
            self.offset_amounts[0] = (new_tile['render_pos'][0] - self.tile['render_pos'][0]) / 5
            self.offset_amounts[1] = (new_tile['render_pos'][1] - self.tile['render_pos'][1]) / 5
            self.offsets = [0, 0]
            self.change_tile(new_tile)
            self.path_index += 1
            self.move_timer = now

            self.check_end_of_path()

    def sell_all_to_towncenter(self):
        canafford = True
        self.just_sold = []
        for item in self.inventory:
            if not canafford:
                break
            for i in range(self.inventory[item]):
                if item not in self.just_sold:
                    self.just_sold.append(item)
                price = int(self.town.resourcemanager.get_price(item, mode=1))
                canafford = self.town.resourcemanager.resources['gold'] >= price
                if canafford:
                    self.town.resourcemanager.resources['gold'] -= price
                    self.gold += price
                    self.town.resourcemanager.resources[item] += 1
                    self.inventory[item] -= 1
                else:
                    break

    def sell_all_to_targettown(self):
        canafford = True
        self.just_sold = []
        # print('selling everything to other town')
        for item in self.inventory:
            if not canafford:
                # print('out of money')
                break
            # print('selling', item)
            for i in range(self.inventory[item]):
                if item not in self.just_sold:
                    self.just_sold.append(item)
                price = int(self.targettown.resourcemanager.get_price(item, mode=1))
                canafford = self.targettown.resourcemanager.resources['gold'] >= price
                if canafford:
                    # print('selling one for', price)
                    self.targettown.resourcemanager.resources['gold'] -= price
                    self.gold += price
                    self.targettown.resourcemanager.resources[item] += 1
                    self.inventory[item] -= 1
                else:
                    break
            # print('done selling', item)

    def buy_from_towncenter(self):
        print('getting demand from other town center')
        target_demand = self.targettown.get_current_demand()
        print(target_demand)
        print(self.just_sold)
        for _, item in target_demand:
            if _ <= 0 or item in self.just_sold:
                continue
            for i in range(5):
                price = int(self.town.resourcemanager.get_price(item, mode=0))
                if self.gold >= price and self.targettown.resourcemanager.resources[item] > 0:
                    if item in self.inventory:
                        self.inventory[item] += 1
                    else:
                        self.inventory[item] = 1
                    self.gold -= price
                    self.town.resourcemanager.resources['gold'] += price
                    self.town.resourcemanager.resources[item] -= 1
                else:
                    break

    def buy_from_targettown(self):
        # print('getting demand from own town center')
        target_demand = self.town.get_current_demand()
        # print(target_demand)
        for _, item in target_demand:
            if _ <= 0 or item in self.just_sold:
                continue
            for i in range(5):
                price = int(self.targettown.resourcemanager.get_price(item, mode=0))
                if self.gold >= price and self.targettown.resourcemanager.resources[item] > 0:
                    if item in self.inventory:
                        self.inventory[item] += 1
                    else:
                        self.inventory[item] = 1
                    self.gold -= price
                    self.targettown.resourcemanager.resources['gold'] += price
                    self.targettown.resourcemanager.resources[item] -= 1
                else:
                    break

    def update_merchant(self):
        if self.arrived_at_work:
            self.sell_all_to_towncenter()
            if self.targettown is not None:
                self.buy_from_towncenter()
                self.get_path_to_targettown()
            else:
                if len(self.world.towns) > 1:
                    self.targettown = self.world.towns[1]
        elif self.arrived_at_towncenter:
            self.sell_all_to_targettown()
            self.buy_from_targettown()
            if self.energy <= 25:
                self.pickup_home_needs()
                self.get_path_to_home()
            else:
                self.get_path_to_work()
        elif self.arrived_at_home:
            self.dropoff_at_home()
            if self.energy == 100:
                self.get_path_to_work()
            else:
                now = pg.time.get_ticks()
                if now - self.energycooldown > 500:
                    self.energy += 1
                    self.energycooldown = now
        else:
            self.move()

    def update(self):

        if self.occupation not in ['Beggar', 'Wanderer']:
            now = pg.time.get_ticks()
            if now - self.skillcooldown > 10000:
                self.skillcooldown = now
                self.skills[self.occupation] += 1

        # if the worker is stationary, check if they have arrived at a workplace or at a town center
        if not self.moving:

            if self.occupation == 'Merchant':
                self.update_merchant()
                return

            # if they are at their job, and it is full, collect the resources and head to town
            if self.arrived_at_work:
                # print('I arrived at work')
                if self.collected_for_work:
                    for item in self.workplace.consumption:
                        self.workplace.storage[item] += self.inventory[item]
                        self.inventory[item] = 0
                        self.collected_for_work = False
                if self.collect_from_work():
                    self.get_path_to_towncenter()

            # if they arrived at the town center, sit and wait or drop off goods and return to work
            elif self.arrived_at_towncenter:
                # print('I arrived at the town center')
                if self.workplace is not None:
                    if sum(self.inventory.values()) > 0:
                        self.dropoff_at_towncenter()
                    if not self.collecting_for_work:
                        # only leave town center if all goods are sold
                        if sum([val for val in self.inventory.values()]) == 0:
                            if self.energy >= 25:
                                self.get_path_to_work()
                            else:
                                self.pickup_home_needs()
                                self.get_path_to_home()
                    else:
                        # print('here', self.going_to_towncenter, self.going_home, self.going_to_work, self.arrived_at_towncenter,
                        #       self.arrived_at_home, self.arrived_at_work)
                        if not self.collected_for_work:
                            goods = self.workplace.goods_needed()
                            for g in goods:
                                if g in self.inventory:
                                    self.inventory[g] += min([self.town.resourcemanager.resources[g], goods[g]])
                                else:
                                    self.inventory[g] = min([self.town.resourcemanager.resources[g], goods[g]])
                                self.town.resourcemanager.resources[g] -= min([self.town.resourcemanager.resources[g], goods[g]])
                            self.collected_for_work = True
                            self.collecting_for_work = False
                            self.get_path_to_work()
                        # print(self.going_to_towncenter, self.going_home, self.going_to_work, self.arrived_at_towncenter,
                        #       self.arrived_at_home, self.arrived_at_work)
                else:
                    self.reset_travel_vars()

            elif self.arrived_at_home:
                # print('I arrived at home')
                self.dropoff_at_home()
                if self.energy == 100:
                    self.get_path_to_work()
                else:
                    now = pg.time.get_ticks()
                    if now - self.energycooldown > 500:
                        self.energy += 1
                        self.energycooldown = now
        else:
            self.check_needs_town()
            if self.workplace is not None:
                self.check_work_needs_goods()
            self.move()

    def pickup_home_needs(self):
        needs = self.home.get_needs()
        if needs:
            minval = 1000000000
            minkey = ''
            for key, val in needs.items():
                if val < minval:
                    minkey = key
            if minkey not in self.inventory:
                self.inventory[minkey] = 0
            amount_to_buy = min([self.town.resourcemanager.resources[minkey], needs[minkey]])
            for i in range(int(amount_to_buy)):
                price = self.town.get_sell_price(minkey)
                if self.gold >= price:
                    self.inventory[minkey] += 1
                    self.town.resourcemanager.resources[minkey] -= 1
                    self.gold -= price
                    self.town.resourcemanager.resources['gold'] += price
                else:
                    break

    def dropoff_at_home(self):
        for key in self.inventory:
            if key in self.home.needs:
                self.home.storage[key] += self.inventory[key]
                self.inventory[key] = 0

    def collect_from_work(self):

        if self.workplace.is_full():
            for key in self.workplace.production:
                if key in self.inventory:
                    self.inventory[key] += int(self.workplace.storage[key])
                else:
                    self.inventory[key] = int(self.workplace.storage[key])
                self.workplace.storage[key] -= int(self.workplace.storage[key])
            self.energy -= 15
            self.current_task = 'Taking goods to Town Center'
            return True
        return False

    def dropoff_at_towncenter(self):
        for key, val in self.inventory.items():
            for i in range(val):
                price = self.town.get_buy_price(key)
                if self.town.resourcemanager.resources['gold'] >= price:
                    self.town.resourcemanager.resources[key] += 1
                    self.inventory[key] -= 1
                    self.town.resourcemanager.resources['gold'] -= price
                    self.gold += price
        self.energy -= 15

    def reset_travel_vars(self):
        self.going_to_work = False
        self.arrived_at_work = False
        self.going_to_towncenter = False
        self.arrived_at_towncenter = False
        self.going_home = False
        self.arrived_at_home = False

    def is_visible(self):
        return not (self.arrived_at_home or self.arrived_at_work)

    def get_state_for_savefile(self):
        ret = ''
        ret += f'id={self.id}#'
        ret += f'name={self.name}#'
        ret += f'pos=({self.tile['grid'][0]},{self.tile['grid'][1]})#'
        if self.home is not None:
            ret += f'home={self.home.id}#'
        else:
            ret += 'home=None#'
        if self.workplace is not None:
            ret += f'work={self.workplace.id}#'
        else:
            ret += 'work=None#'
        if self.town is not None:
            ret += f'town={self.town.id}#'
        else:
            ret += 'town=None#'
        ret += f'energy={self.energy}#'
        ret += f'gold={self.gold}#'
        ret += f'currenttask={self.current_task}#'
        ret += f'inventory={','.join([f'{key}:{value}' for key, value in self.inventory.items()])}#'
        ret += f'skills={','.join([f'{key}:{value}' for key, value in self.skills.items()])}#'
        ret += f'aaw={self.arrived_at_work}#'
        ret += f'aah={self.arrived_at_home}#'
        ret += f'aatc={self.arrived_at_towncenter}#'
        ret += f'gtw={self.going_to_work}#'
        ret += f'gh={self.going_home}#'
        ret += f'gttc={self.going_to_towncenter}#'
        ret += f'collected={self.collected_for_work}#'
        ret += f'collecting={self.collecting_for_work}#'
        ret += f'pathidx={self.path_index}#'
        ret += f'path={','.join([str(item) for item in self.path[self.path_index:]])}#'
        if self.occupation == 'Merchant':
            if self.targettown is not None:
                ret += f'targettown={self.targettown.id}#'
        ret = ret[:-1] + '\n'
        return ret

class BasicProductionWorker(Worker):

    def __init__(self):
        pass

class RefinedProductionWorker(Worker):

    def __init__(self):
        pass

class Merchant(Worker):

    def __init__(self):
        pass

class TownWorker(Worker):

    def __init__(self):
        pass