import pygame as pg
from .settings import TILE_SIZE

class World:

    def __init__(self, grid_length_x, grid_length_y, width, height):
        self.grid_length_x = grid_length_x
        self.grid_length_y = grid_length_y
        self.width = width
        self.height = height

        self.world = self.create_world()

    def create_world(self):

        world = []

        for x in range(self.grid_length_x):
            world.append([])
            for y in range(self.grid_length_y):
                tile = self.grid_to_world(x, y)
                world[x].append(tile)

        return world

    def grid_to_world(self, x, y):
        rect = [(x * TILE_SIZE, y * TILE_SIZE),
                (x * TILE_SIZE + TILE_SIZE, y * TILE_SIZE),
                (x * TILE_SIZE + TILE_SIZE, y * TILE_SIZE + TILE_SIZE),
                (x * TILE_SIZE, y * TILE_SIZE + TILE_SIZE)]

        iso_poly = [self.cart_to_iso(x, y) for x, y in rect]

        out = {
            'grid': [x, y],
            'cart_rect': rect,
            'iso_poly': iso_poly,
        }

        return out

    def cart_to_iso(self, x, y):
        iso_x = x - y
        iso_y = (x + y) / 2
        return iso_x, iso_y