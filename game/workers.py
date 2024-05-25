
import pygame as pg
import random
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from networkx import dijkstra_path


class Worker:

    def __init__(self, tile, world):
        self.world = world
        self.world.entities.append(self)
        self.name = "worker"
        image = pg.image.load("assets/graphics/characters/worker.png").convert_alpha()
        self.image = pg.transform.scale(image, (image.get_width()*2, image.get_height()*2))
        self.tile = tile
        self.moving = False
        self.path_index = 0
        self.town = None
        self.workplace = None
        self.home = None
        self.selected = False
        self.occupation = 'Wanderer'

        self.energy = 100
        self.energycooldown = pg.time.get_ticks()

        self.inventory = {}
        self.skills = {}

        self.going_to_work = False
        self.arrived_at_work = False
        self.going_to_towncenter = False
        self.arrived_at_towncenter = False
        self.going_home = False
        self.arrived_at_home = False

        # pathfinding
        self.world.workers[tile["grid"][0]][tile["grid"][1]] = self
        self.move_timer = pg.time.get_ticks()
        self.create_path()

    def create_path(self):

        newtown = self.world.find_town_with_vacancy()
        if newtown is None:
            self.get_random_path()
        else:
            self.town = newtown
            self.moving = True
            self.town.villagers.append(self)
            self.get_path_to_towncenter()
            self.going_to_towncenter = True
            self.occupation = 'Beggar'

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
        if self.path_index == len(self.path) - 1:
            self.moving = False
            if self.going_to_towncenter:
                self.going_to_towncenter = False
                self.arrived_at_towncenter = True
            if self.going_to_work:
                self.going_to_work = False
                self.arrived_at_work = True
            if self.going_home:
                self.going_home = False
                self.arrived_at_home = True

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

    def assign_town(self, newtown):
        self.town = newtown
        self.town.villagers.append(self)
        self.get_path_to_towncenter()
        self.going_to_towncenter = True
        self.town.num_villagers += 1

    def move(self):
        now = pg.time.get_ticks()
        if now - self.move_timer > 500:
            # update position in the world
            new_pos = self.path[self.path_index]
            new_tile = self.world.world[new_pos[0]][new_pos[1]]
            self.change_tile(new_tile)
            self.path_index += 1
            self.move_timer = now

            self.check_end_of_path()

    def update(self):

        # if the worker is stationary, check if they have arrived at a workplace or at a town center
        if not self.moving:

            # if they are at their job, and it is full, collect the resources and head to town
            if self.arrived_at_work:
                if self.collect_from_work():
                    self.get_path_to_towncenter()

            # if they arrived at the town center, sit and wait or drop off goods and return to work
            elif self.arrived_at_towncenter:
                if self.workplace is not None:
                    self.dropoff_at_towncenter()
                    if self.energy >= 30:
                        self.get_path_to_work()
                    else:
                        self.pickup_home_needs()
                        self.get_path_to_home()
                else:
                    self.reset_travel_vars()

            elif self.arrived_at_home:
                if self.energy == 100:
                    self.get_path_to_work()
                else:
                    now = pg.time.get_ticks()
                    if now - self.energycooldown > 500:
                        self.energy += 1
                        self.energycooldown = now
        else:
            self.check_needs_town()
            self.move()

    def pickup_home_needs(self):
        pass

    def collect_from_work(self):
        if self.workplace.is_full():
            for key, val in self.workplace.storage.items():
                if key in self.inventory:
                    self.inventory[key] += val
                else:
                    self.inventory[key] = val
                self.workplace.storage[key] = 0
            self.energy -= 15
            return True
        return False

    def dropoff_at_towncenter(self):
        for key, val in self.inventory.items():
            self.town.resourcemanager.resources[key] += self.inventory[key]
            self.inventory[key] = 0
        self.energy -= 15

    def reset_travel_vars(self):
        self.going_to_work = False
        self.arrived_at_work = False
        self.going_to_towncenter = False
        self.arrived_at_towncenter = False
        self.going_home = False
        self.arrived_at_home = False
