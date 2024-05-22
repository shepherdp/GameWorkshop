
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

        # pathfinding
        self.world.workers[tile["grid"][0]][tile["grid"][1]] = self
        self.move_timer = pg.time.get_ticks()

        self.create_path()

    def create_path(self):
        num = random.randint(0, len(self.world.towns) - 1)
        x, y = self.world.towns[num].loc
        print('In network: ', (x, y) in self.world.world_network.nodes, (x, y))
        print('Spawn: ', (self.tile['grid'][0], self.tile['grid'][1]) in self.world.world_network.nodes, self.tile['grid'])
        self.start = (self.tile["grid"][0], self.tile["grid"][1])
        self.end = (x, y)
        self.path = dijkstra_path(self.world.world_network, self.start, self.end)
        print('Path: ', self.path)

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

    def change_tile(self, new_tile):
        self.world.workers[self.tile["grid"][0]][self.tile["grid"][1]] = None
        self.world.workers[new_tile.x][new_tile.y] = self
        self.tile = self.world.world[new_tile.x][new_tile.y]

    def update(self):
        if not self.moving:
            return
        now = pg.time.get_ticks()
        if now - self.move_timer > 1000:
            try:
                new_pos = self.path[self.path_index]
            except:
                self.create_path()
                return
            # update position in the world
            self.change_tile(new_pos)
            self.path_index += 1
            self.move_timer = now
            if self.path_index == len(self.path) - 1:
                self.moving = False
                # self.create_path()

