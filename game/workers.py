
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
        image = pg.image.load("assets/graphics/worker.png").convert_alpha()
        self.image = pg.transform.scale(image, (image.get_width()*2, image.get_height()*2))
        self.tile = tile
        self.moving = False
        self.path_index = 0
        self.town = None
        self.workplace = None
        self.selected = False
        self.occupation = 'Wanderer'

        self.inventory = {}
        self.skills = {}

        self.going_to_work = False
        self.arrived_at_work = False
        self.going_to_towncenter = False
        self.arrived_at_towncenter = False

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

    def get_random_path(self):
        self.start = (self.tile["grid"][0], self.tile["grid"][1])
        self.end = self.world.get_random_position()
        self.path = dijkstra_path(self.world.world_network, self.start, self.end)
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

    def move(self):
        now = pg.time.get_ticks()
        if now - self.move_timer > 1000:
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
                self.collect_from_work()
                self.get_path_to_towncenter()

            # if they arrived at the town center, sit and wait or drop off goods and return to work
            elif self.arrived_at_towncenter:
                if self.workplace is not None:
                    self.dropoff_at_towncenter()
                    self.get_path_to_work()
                else:
                    self.reset_travel_vars()
        else:
            self.move()

    def collect_from_work(self):
        if self.workplace.is_full():
            for key, val in self.workplace.storage.items():
                if key in self.inventory:
                    self.inventory[key] += val
                else:
                    self.inventory[key] = val
                self.workplace.storage[key] = 0

    def dropoff_at_towncenter(self):
        for key, val in self.inventory.items():
            self.town.resourcemanager.resources[key] += self.inventory[key]
            self.inventory[key] = 0

    def reset_travel_vars(self):
        self.going_to_work = False
        self.arrived_at_work = False
        self.going_to_towncenter = False
        self.arrived_at_towncenter = False

# A-star was not reading the map right for some reason.  Should figure that one out.
    # For now, just using Dijkstra on a networkx graph of all walkable tiles in the game

    # def create_path(self):
    #     searching_for_path = True
    #     runs = 0
    #     while searching_for_path:
    #         num = random.randint(0, len(self.world.towns) - 1)
    #         print(num, self.world.towns[num].loc)
    #         x, y = self.world.towns[num].loc
    #         self.grid = Grid(matrix=self.world.collision_matrix)
    #         self.start = self.grid.node(self.tile["grid"][0], self.tile["grid"][1])
    #         self.end = self.grid.node(x, y)
    #         finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
    #         self.path_index = 0
    #         self.path, runs = finder.find_path(self.start, self.end, self.grid)
    #         searching_for_path = False
    #         self.moving = True
    #     print('Runs:', runs)
    #     print('Path:', self.path)
            # x = random.randint(0, self.world.grid_length_x - 1)
            # y = random.randint(0, self.world.grid_length_y - 1)
            # dest_tile = self.world.world[x][y]
            # if not dest_tile["collision"]:
            #     self.grid = Grid(matrix=self.world.collision_matrix)
            #     self.start = self.grid.node(self.tile["grid"][0], self.tile["grid"][1])
            #     self.end = self.grid.node(x, y)
            #     finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
            #     self.path_index = 0
            #     self.path, runs = finder.find_path(self.start, self.end, self.grid)
            #     searching_for_path = False