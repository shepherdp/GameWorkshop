import pygame as pg
import sys
from .world import World
from .settings import TILE_SIZE
from .utils import draw_text
from .camera import Camera
from .hud import HUD

from math import sin, pi

WORLD_W = 100
WORLD_H = 100

DRAW_GRID = False
SHOW_FPS = True

class Game:

    def __init__(self, screen, clock):

        self.screen = screen
        self.clock = clock

        self.width, self.height = self.screen.get_size()

        self.world = World(WORLD_W, WORLD_H, self.width, self.height)
        self.camera = Camera(self.width, self.height)
        self.HUD = HUD(self.width, self.height)

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick()
            self.events()
            self.update()
            self.draw()

    def quit(self):
        pg.quit()
        sys.exit()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()

    def update(self):
        self.camera.update()
        self.HUD.update()

    def draw(self):
        self.screen.fill((0, 0, 0))

        # self.screen.blit(self.world.surface, (0, 0))
        self.screen.blit(self.world.surface, (self.camera.scroll.x,
                                              self.camera.scroll.y)
                         )

        for x in range(self.world.grid_length_x):
            for y in range(self.world.grid_length_y):

                r_pos = self.world.world[x][y]['render_pos']
                # self.screen.blit(self.world.tiles['block'],
                #                  (r_pos[0] + self.width/2,
                #                   r_pos[1] + self.height/4)
                #                  )

                if DRAW_GRID:
                    # put isometric grid on screen
                    poly = self.world.world[x][y]['iso_poly']
                    poly = [(x + self.world.surface.get_width()/2 + self.camera.scroll.x,
                             y + self.camera.scroll.y) for x, y in poly]
                    pg.draw.polygon(self.screen, (255, 0, 0), poly, 1)

                t = self.world.world[x][y]['tile']
                offset = 0
                if t == 'rock':
                    offset = self.world.tiles[t].get_height() - TILE_SIZE
                if t == 'tree':
                    offset = (self.world.tiles[t].get_height() - 3*TILE_SIZE/4)
                if t:
                    self.screen.blit(self.world.tiles[t],
                                     (r_pos[0] + self.world.surface.get_width()/2 + self.camera.scroll.x,
                                      r_pos[1] - offset + self.camera.scroll.y)
                                     )

        self.HUD.draw(self.screen)

        if SHOW_FPS:
            draw_text(self.screen, f'FPS: {round(self.clock.get_fps())}',
                      25, (255, 255, 255), (10, 10))
        pg.display.flip()