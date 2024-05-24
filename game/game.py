import pygame as pg
import sys

from .camera import Camera
from .hud import HUD
from .utils import draw_text
from .workers import Worker
from .world import World

from .settings import WORLD_W, WORLD_H


class Game:

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.width, self.height = self.screen.get_size()

        # entities
        self.entities = []

        # hud
        self.hud = HUD(self.width, self.height, self.screen)

        # world
        self.world = World(self.entities, self.hud, WORLD_W, WORLD_H, self.width, self.height)

        # camera
        self.camera = Camera(self.width, self.height)

        self.spawncooldown = pg.time.get_ticks()

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(60)
            self.spawn_worker()
            self.events()
            self.update()
            self.draw()

    def spawn_worker(self):
        now = pg.time.get_ticks()
        if now - self.spawncooldown > 10000:
            x, y = self.world.get_random_position_along_border()
            Worker(self.world.world[x][y], self.world)
            self.spawncooldown = now

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.playing = False
                    self.quit()

    def update(self):
        self.camera.update()
        for e in self.entities: e.update()
        self.hud.update()
        self.world.update(self.camera)

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.world.draw(self.screen, self.camera)
        self.hud.draw()

        draw_text(
            self.screen,
            'fps={}'.format(round(self.clock.get_fps())),
            25,
            (255, 255, 255),
            (10, 10)
        )

        pg.display.flip()

    def quit(self):
        self.world.write_map()
        pg.quit()
        sys.exit()
