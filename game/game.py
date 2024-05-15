import pygame as pg
import sys
from .world import World
from .settings import TILE_SIZE

class Game:

    def __init__(self, screen, clock):

        self.screen = screen
        self.clock = clock

        self.width, self.height = self.screen.get_size()

        self.world = World(10, 10, self.width, self.height)

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick()
            self.events()
            self.update()
            self.draw()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    sys.exit()

    def update(self):
        pass

    def draw(self):
        self.screen.fill((0, 0, 0))

        for x in range(self.world.grid_length_x):
            for y in range(self.world.grid_length_y):

                sq = self.world.world[x][y]['cart_rect']
                rect = pg.Rect(sq[0][0], sq[0][1], TILE_SIZE, TILE_SIZE)
                pg.draw.rect(self.screen, (0, 0, 255), rect, 1)

                poly = self.world.world[x][y]['iso_poly']
                poly = [(x + self.width / 2, y + self.height / 4) for x, y in poly]
                pg.draw.polygon(self.screen, (255, 0, 0), poly, 1)

        pg.display.flip()