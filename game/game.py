import pygame as pg
import sys
from networkx import dijkstra_path

from .camera import Camera
from .hud import HUD
from .utils import draw_text
from .workers import Worker
from .world import World

from .settings import WORLD_W, WORLD_H, SHOWFPS


class Game:

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.width, self.height = self.screen.get_size()

        # self.spawning = True

        # entities
        self.entities = []

        self.num_characters = 0

        self.camera = Camera(self.width, self.height)

        # hud
        self.hud = HUD(self.width, self.height, self.screen)

        # world
        self.world = World(self.entities, self.hud, self.camera, WORLD_W, WORLD_H, self.width, self.height)

        self.spawncooldown = pg.time.get_ticks()

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(60)
            self.spawn_worker()
            self.events()
            self.update()
            self.draw()

    # consider moving this to World class
    def spawn_worker(self):
        # if not self.spawning:
        #     return
        now = pg.time.get_ticks()
        if now - self.spawncooldown > 10000:
            if self.num_characters > sum([i.housing_capacity for i in self.world.towns]) + 3:
                return
            found = False
            while not found:
                x, y = self.world.get_random_position_along_border()
                try:
                    dijkstra_path(self.world.world_network, (x, y), self.world.towns[0].loc)
                except:
                    continue
                Worker(self.world.world[x][y], self.world)
                self.spawncooldown = now
                found = True
                self.num_characters += 1
                # self.spawning = False

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
        for e in self.entities:
            e.update()
        self.hud.update()
        self.world.update()

    def draw(self):
        self.screen.fill((0, 0, 0))
        # self.screen.fill((179, 255, 255))
        self.world.draw()
        self.hud.draw()

        if SHOWFPS:
            draw_text(self.screen,
                      'fps={}'.format(round(self.clock.get_fps())),
                      25,
                      (255, 255, 255),
                      (10, 10))

        pg.display.flip()

    def quit(self):
        # self.world.write_map()
        # self.world.write_world_network()
        # self.world.write_road_network()
        pg.quit()
        sys.exit()
