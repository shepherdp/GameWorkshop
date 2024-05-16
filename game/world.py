import pygame as pg
from .settings import TILE_SIZE
import random
import noise

class World:

    def __init__(self, grid_length_x, grid_length_y, width, height):
        self.grid_length_x = grid_length_x
        self.grid_length_y = grid_length_y
        self.width = width
        self.height = height
        self.p_scale = self.grid_length_x / 2
        self.tiles = self.load_images()

        self.surface = pg.Surface((grid_length_x * TILE_SIZE * 2,
                                   grid_length_y * TILE_SIZE + 2 * TILE_SIZE)).convert_alpha()

        self.world = self.create_world()

    def create_world(self):

        # container for objects representing world spaces
        world = []

        for x in range(self.grid_length_x):
            world.append([])
            for y in range(self.grid_length_y):
                tile = self.grid_to_world(x, y)
                world[x].append(tile)

                render_pos = tile['render_pos']
                self.surface.blit(self.tiles['block'], (render_pos[0] + self.surface.get_width() / 2,
                                                        render_pos[1]))

        return world

    def populate_tile_simple(self, x, y):
        r = random.random()
        if r < .05:
            return 'tree'
        elif r < .1:
            return 'rock'
        else:
            return ''

    def populate_tile_perlin(self, x, y):
        r = noise.pnoise2(x / self.p_scale, y / self.p_scale)
        if (r >= .15) or (r <= -.35):
            return 'tree'
        else:
            if abs(r - .01) <= .001:
                return 'tree'
            elif abs(r - .02) <= .001:
                return 'rock'
            else:
                return ''

    def grid_to_world(self, x, y):
        rect = [(x * TILE_SIZE, y * TILE_SIZE),
                (x * TILE_SIZE + TILE_SIZE, y * TILE_SIZE),
                (x * TILE_SIZE + TILE_SIZE, y * TILE_SIZE + TILE_SIZE),
                (x * TILE_SIZE, y * TILE_SIZE + TILE_SIZE)]

        iso_poly = [self.cart_to_iso(x, y) for x, y in rect]

        minx = min([x for x, y in iso_poly])
        miny = min([y for x, y in iso_poly])

        # tile = self.populate_tile_simple(x, y)
        tile = self.populate_tile_perlin(x, y)

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

        block = pg.image.load('assets\\graphics\\testblock.png').convert_alpha()
        rock = pg.image.load('assets\\graphics\\testrock.png').convert_alpha()
        tree = pg.image.load('assets\\graphics\\testtree.png').convert_alpha()

        return {'block': block,
                'rock': rock,
                'tree': tree}