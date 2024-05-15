import pygame as pg
from .settings import TILE_SIZE
import random

class World:

    def __init__(self, grid_length_x, grid_length_y, width, height):
        self.grid_length_x = grid_length_x
        self.grid_length_y = grid_length_y
        self.width = width
        self.height = height
        self.tiles = self.load_images()

        self.surface = pg.Surface((width, height))

        self.world = self.create_world()

    def create_world(self):

        # conrtainer for objects representing world spaces
        world = []

        for x in range(self.grid_length_x):
            world.append([])
            for y in range(self.grid_length_y):
                tile = self.grid_to_world(x, y)
                world[x].append(tile)

                render_pos = tile['render_pos']
                self.surface.blit(self.tiles['block'], (render_pos[0] + self.width / 2,
                                                        render_pos[1] + self.height / 4))

        return world

    def grid_to_world(self, x, y):
        rect = [(x * TILE_SIZE, y * TILE_SIZE),
                (x * TILE_SIZE + TILE_SIZE, y * TILE_SIZE),
                (x * TILE_SIZE + TILE_SIZE, y * TILE_SIZE + TILE_SIZE),
                (x * TILE_SIZE, y * TILE_SIZE + TILE_SIZE)]

        iso_poly = [self.cart_to_iso(x, y) for x, y in rect]

        minx = min([x for x, y in iso_poly])
        miny = min([y for x, y in iso_poly])

        r = random.random()
        if r < .05:
            tile = 'tree'
        elif r < .1:
            tile = 'rock'
        else:
            tile = ''

        out = {
            'grid': [x, y],
            'cart_rect': rect,
            'iso_poly': iso_poly,
            'render_pos': [minx, miny],
            'tile': tile
        }

        return out

    def cart_to_iso(self, x, y):
        iso_x = x - y
        iso_y = (x + y) / 2
        return iso_x, iso_y

    def load_images(self):

        block = pg.image.load('assets\\graphics\\testblock.png')
        rock = pg.image.load('assets\\graphics\\testrock.png')
        tree = pg.image.load('assets\\graphics\\testtree.png')

        return {'block': block,
                'rock': rock,
                'tree': tree}