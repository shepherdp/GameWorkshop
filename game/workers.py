
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
        image = pg.image.load("assets/graphics/worker.png").convert_alpha()
        self.name = "worker"
        self.image = pg.transform.scale(image, (image.get_width()*2, image.get_height()*2))
        self.tile = tile
        self.moving = False
        self.path_index = 0
        self.town = None
        self.workplace = None

        # pathfinding
        self.world.workers[tile["grid"][0]][tile["grid"][1]] = self
        self.move_timer = pg.time.get_ticks()

        self.create_path()

    def create_path(self):
        random_path = True
        for i in range(len(self.world.towns)):
            if len(self.world.towns[i].villagers) < self.world.towns[i].housing_capacity:
                random_path = False
                break

        if random_path:
            self.get_random_path()

        else:
            # towns = list(range(len(self.world.towns)))
            # random.shuffle(towns)
            found = False
            while not found:
                num = random.randint(0, len(self.world.towns) - 1)
                # num = towns.pop(0)
                if len(self.world.towns[num].villagers) == self.world.towns[num].housing_capacity:
                    continue
                found = True
                self.town = self.world.towns[num]
                x, y = self.town.loc
                self.start = (self.tile["grid"][0], self.tile["grid"][1])
                self.end = (x, y)
                self.path = dijkstra_path(self.world.world_network, self.start, self.end)
                self.moving = True
                self.town.villagers.append(self)

    def get_path_to_work(self):
        self.start = (self.tile["grid"][0], self.tile["grid"][1])
        self.end = self.workplace.loc
        self.path = dijkstra_path(self.world.world_network, self.start, self.end)
        self.path_index = 0
        self.moving = True

    def get_random_path(self):
        self.start = (self.tile["grid"][0], self.tile["grid"][1])
        self.end = self.world.get_random_position()
        self.path = dijkstra_path(self.world.world_network, self.start, self.end)
        self.path_index = 0
        self.moving = True

    def change_tile(self, new_tile):
        self.world.workers[self.tile["grid"][0]][self.tile["grid"][1]] = None
        self.world.workers[new_tile['grid'][0]][new_tile['grid'][1]] = self
        self.tile = self.world.world[new_tile['grid'][0]][new_tile['grid'][1]]

    def update(self):
        if not self.moving:
            return
        now = pg.time.get_ticks()
        if now - self.move_timer > 1000:
            try:
                new_pos = self.path[self.path_index]
            except:
                # self.create_path()
                return
            # update position in the world

            new_tile = self.world.world[new_pos[0]][new_pos[1]]
            self.change_tile(new_tile)
            self.path_index += 1
            self.move_timer = now

            # if worker reaches the destination, stop if it is a building and make a new random path if they
            # are still just wandering
            if self.path_index == len(self.path) - 1:
                self.moving = False
                if self.town is None:
                    self.get_random_path()




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