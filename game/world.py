# import pygame as pg
import random
import noise
from .settings import TILE_SIZE
from .buildings import *
from .utils import draw_text, load_images
from .resourcemanager import ResourceManager
import networkx as nx
from matplotlib.pyplot import plot, savefig, scatter


LOADMAP = False
MAPNAME = 'map.txt'

CHARMAP = {'tree': 't',
           'rock': 'r',
           '': '.',
           'well': 'w',
           'road': 'p',
           'water': '^',
           'chopping': 'c',
           'towncenter': 'x',
           'quarry': 'q',
           'wheatfield': 'v',
           'house': 'h'}

R_CHARMAP = {item: key for key, item in CHARMAP.items()}

class World:

    def __init__(self, entities, hud, grid_length_x, grid_length_y, width, height):
        self.resource_manager = ResourceManager()
        self.entities = entities
        self.hud = hud
        self.grid_length_x = grid_length_x
        self.grid_length_y = grid_length_y
        self.width = width
        self.height = height

        self.hud.parent = self

        self.perlin_scale = grid_length_x / 2

        self.grass_tiles = pg.Surface(
            (grid_length_x * TILE_SIZE * 2, grid_length_y * TILE_SIZE + 2 * TILE_SIZE)).convert_alpha()
        self.tiles = load_images()
        self.world_network = nx.Graph()
        self.world = self.create_world()

        self.buildings = [[None for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]
        self.workers = [[None for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]

        self.collision_matrix = self.create_collision_matrix()
        self.create_world_network()

        self.towns = []
        # choose a random spot on the map to place one initial town center
        if not LOADMAP:
            x, y = self.get_random_position()
            render_pos = self.world[x][y]['render_pos']
            grid_pos = (x, y)
            ent = TownCenter(render_pos, grid_pos, ResourceManager())
            self.towns.append(ent)
            self.buildings[x][y] = ent
            self.entities.append(ent)
            self.hud.town_exists = True

        self.temp_tile = None
        self.examine_tile = None

        self.active_town_center = None

    def update(self, camera):

        mouse_pos = pg.mouse.get_pos()
        mouse_action = pg.mouse.get_pressed()

        # if the user left-clicks, deselect anything that is selected
        if mouse_action[2]:
            self.examine_tile = None
            self.hud.examined_tile = None
            self.hud.select_panel_visible = False

        # user wants to place a tile
        self.temp_tile = None
        if self.hud.selected_tile is not None:

            # get grid coordinates of current mouse position
            grid_pos = self.mouse_to_grid(mouse_pos[0], mouse_pos[1], camera.scroll)


            if self.can_place_tile(grid_pos):

                # grab a copy of the image to place over the tile with the mouse
                img = self.hud.selected_tile['image'].copy()
                img.set_alpha(100)

                render_pos = self.world[grid_pos[0]][grid_pos[1]]['render_pos']
                iso_poly = self.world[grid_pos[0]][grid_pos[1]]['iso_poly']
                collision = self.world[grid_pos[0]][grid_pos[1]]['collision']

                # can't place blocks on spaces containing workers
                if self.workers[grid_pos[0]][grid_pos[1]] is not None:
                    collision = True

                self.temp_tile = {
                    'image': img,
                    'render_pos': render_pos,
                    'iso_poly': iso_poly,
                    'collision': collision,
                    'grid_pos': grid_pos,
                    'name': self.hud.selected_tile['name']
                }

                if mouse_action[0] and not collision:
                    valid = True
                    if self.active_town_center is None:
                        raise Exception('Placing building with no town center active.')
                    ent = None
                    if self.hud.selected_tile['name'] == 'towncenter':
                        valid = not self.in_any_towncenter_radius(grid_pos)
                        if valid:
                            ent = TownCenter(render_pos, grid_pos, ResourceManager())
                            self.towns.append(ent)
                            # when this is false, no other buildings can be made
                            self.hud.town_exists = True
                    else:
                        valid = self.in_towncenter_radius(grid_pos)
                        if self.hud.selected_tile['name'] == 'well':
                            if valid:
                                ent = Well(render_pos, grid_pos, self.active_town_center.resourcemanager)
                        elif self.hud.selected_tile['name'] == 'chopping':
                            if valid:
                                ent = ChoppingBlock(render_pos, grid_pos, self.active_town_center.resourcemanager)
                        elif self.hud.selected_tile['name'] == 'quarry':
                            if valid:
                                ent = Quarry(render_pos, grid_pos, self.active_town_center.resourcemanager)
                        elif self.hud.selected_tile['name'] == 'road':
                            if valid:
                                ent = Road(render_pos, grid_pos, self.active_town_center.resourcemanager)
                        elif self.hud.selected_tile['name'] == 'wheatfield':
                            if valid:
                                ent = Wheatfield(render_pos, grid_pos, self.active_town_center.resourcemanager)
                        elif self.hud.selected_tile['name'] == 'house':
                            if valid:
                                ent = House(render_pos, grid_pos, self.active_town_center.resourcemanager)
                    if valid and (ent is not None):
                        self.world[grid_pos[0]][grid_pos[1]]['collision'] = True
                        self.collision_matrix[grid_pos[1]][grid_pos[0]] = 0
                        self.entities.append(ent)
                        self.buildings[grid_pos[0]][grid_pos[1]] = ent

                        # if the building is not a town center, assign it to the currently active one
                        if self.hud.selected_tile['name'] != 'towncenter':
                            self.active_town_center.buildings.append(ent)
                            if self.hud.selected_tile['name'] in self.active_town_center.num_buildings:
                                self.active_town_center.num_buildings[self.hud.selected_tile['name']] += 1
                            else:
                                self.active_town_center.num_buildings[self.hud.selected_tile['name']] = 1
                            if self.hud.selected_tile['name'] == 'house':
                                self.active_town_center.housing_capacity += 5
                        else:
                            self.active_town_center.resourcemanager.apply_cost('towncenter')
                            # self.collision_matrix[grid_pos[1]][grid_pos[0]] = 0

                    # self.hud.selected_tile = None

        # user wants to select a building
        else:

            grid_pos = self.mouse_to_grid(mouse_pos[0], mouse_pos[1], camera.scroll)

            if self.can_place_tile(grid_pos):
                building = self.buildings[grid_pos[0]][grid_pos[1]]
                if mouse_action[0] and (building is not None):
                    self.examine_tile = grid_pos
                    self.hud.examined_tile = building
                    self.hud.select_panel_visible = True

    def draw(self, screen, camera):

        screen.blit(self.grass_tiles, (camera.scroll.x, camera.scroll.y))

        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):
                render_pos = self.world[x][y]['render_pos']
                # draw world tiles
                tile = self.world[x][y]['tile']

                free = True
                if tile != '':
                    free = False
                    screen.blit(self.tiles[tile],
                                (render_pos[0] + self.grass_tiles.get_width() / 2 + camera.scroll.x,
                                 render_pos[1] - (self.tiles[tile].get_height() - TILE_SIZE) + camera.scroll.y))

                # draw buildings
                building = self.buildings[x][y]
                if building is not None:
                    free = False
                    screen.blit(building.image,
                                (render_pos[0] + self.grass_tiles.get_width() / 2 + camera.scroll.x,
                                 render_pos[1] - (building.image.get_height() - TILE_SIZE) + camera.scroll.y))

                    # place outline around active town center
                    if building is self.active_town_center:
                        mask = pg.mask.from_surface(building.image).outline()
                        mask = [(x + render_pos[0] + self.grass_tiles.get_width() / 2 + camera.scroll.x,
                                 y + render_pos[1] - (building.image.get_height() - TILE_SIZE) + camera.scroll.y)
                                for x, y in mask]
                        pg.draw.polygon(screen, (0, 255, 0), mask, 3)

                    # draw white outline around selected object
                    if self.examine_tile is not None:
                        if (x == self.examine_tile[0]) and (y == self.examine_tile[1]):
                            mask = pg.mask.from_surface(building.image).outline()
                            mask = [(x + render_pos[0] + self.grass_tiles.get_width() / 2 + camera.scroll.x,
                                     y + render_pos[1] - (building.image.get_height() - TILE_SIZE) + camera.scroll.y)
                                    for x, y in mask]
                            pg.draw.polygon(screen, (255, 255, 255), mask, 3)

                # draw workers
                worker = self.workers[x][y]
                if worker is not None:
                    free = False
                    screen.blit(worker.image,
                                (render_pos[0] + self.grass_tiles.get_width() / 2 + camera.scroll.x,
                                 render_pos[1] - (worker.image.get_height() - TILE_SIZE) + camera.scroll.y))

                if free and self.temp_tile is not None:
                    iso_poly = [(x + self.grass_tiles.get_width() / 2 + camera.scroll.x, y + camera.scroll.y) for x, y
                                in self.world[x][y]['iso_poly']]

                    # if self.active_town_center is not None:
                    #     if self.in_towncenter_radius(self.world[x][y]['grid']):
                    #         pg.draw.polygon(screen, (125, 125, 125, 150), iso_poly, 3)

                    if self.temp_tile['name'] == 'towncenter':
                        if self.in_any_towncenter_radius(self.world[x][y]['grid']):
                            pg.draw.polygon(screen, (125, 0, 0, 150), iso_poly, 3)
                    else:
                        if self.in_towncenter_radius(self.world[x][y]['grid']):
                            pg.draw.polygon(screen, (125, 125, 125, 150), iso_poly, 3)

        # place a building
        if self.temp_tile is not None:

            mouse_pos = pg.mouse.get_pos()
            grid_pos = self.mouse_to_grid(mouse_pos[0], mouse_pos[1], camera.scroll)

            iso_poly = self.temp_tile['iso_poly']
            iso_poly = [(x + self.grass_tiles.get_width() / 2 + camera.scroll.x, y + camera.scroll.y) for x, y in
                        iso_poly]
            if self.temp_tile['collision'] or (self.workers[grid_pos[0]][grid_pos[1]] is not None):
                pg.draw.polygon(screen, (255, 0, 0), iso_poly, 3)
            else:
                if self.temp_tile['name'] == 'towncenter':
                    if self.in_any_towncenter_radius(grid_pos):
                        pg.draw.polygon(screen, (255, 0, 0), iso_poly, 3)
                    else:
                        pg.draw.polygon(screen, (255, 255, 255), iso_poly, 3)
                else:
                    if self.in_towncenter_radius(grid_pos):
                        pg.draw.polygon(screen, (255, 255, 255), iso_poly, 3)
                    else:
                        pg.draw.polygon(screen, (255, 0, 0), iso_poly, 3)

            render_pos = self.temp_tile['render_pos']
            screen.blit(
                self.temp_tile['image'],
                (
                    render_pos[0] + self.grass_tiles.get_width() / 2 + camera.scroll.x,
                    render_pos[1] - (self.temp_tile['image'].get_height() - TILE_SIZE) + camera.scroll.y
                )
            )

        # for x in range(self.grid_length_x):
        #     for y in range(self.grid_length_y):
        #         if (x, y) in self.world_network.nodes:
        #             iso_poly = [(x + self.grass_tiles.get_width() / 2 + camera.scroll.x, y + camera.scroll.y) for x, y
        #                         in self.world[x][y]['iso_poly']]
        #             pg.draw.polygon(screen, (0, 0, 50), iso_poly, 3)

        # for x in range(self.grid_length_x):
        #     for y in range(self.grid_length_y):
        #         if (x, y) not in self.world_network:
        #             continue
        #         render_pos = self.world[x][y]['render_pos']
        #         tile = self.world[x][y]['tile']
        #         iso_poly = [(x + self.grass_tiles.get_width() / 2 + camera.scroll.x, y + camera.scroll.y) for x, y
        #                     in self.world[x][y]['iso_poly']]
        #         pg.draw.polygon(screen, (0, 0, 150, 150), iso_poly, 3)

    def create_world(self):

        matrix = None
        if LOADMAP:
            f = open(MAPNAME, 'r')
            matrix = [i[:-1].split(',') for i in f.readlines()]
            f.close()

        world = []

        for grid_x in range(self.grid_length_x):
            world.append([])
            for grid_y in range(self.grid_length_y):
                world_tile = self.grid_to_world(grid_x, grid_y)

                if LOADMAP:
                    char = R_CHARMAP[matrix[grid_x][grid_y]]
                    world_tile['tile'] = char
                    if char != '':
                        world_tile['collision'] = True
                    else:
                        world_tile['collision'] = False

                world[grid_x].append(world_tile)

                render_pos = world_tile['render_pos']
                self.grass_tiles.blit(random.choice([self.tiles['grass1'], self.tiles['grass2']]),
                                      (render_pos[0] + self.grass_tiles.get_width() / 2, render_pos[1]))

        return world

    def grid_to_world(self, grid_x, grid_y):

        rect = [
            (grid_x * TILE_SIZE, grid_y * TILE_SIZE),
            (grid_x * TILE_SIZE + TILE_SIZE, grid_y * TILE_SIZE),
            (grid_x * TILE_SIZE + TILE_SIZE, grid_y * TILE_SIZE + TILE_SIZE),
            (grid_x * TILE_SIZE, grid_y * TILE_SIZE + TILE_SIZE)
        ]

        iso_poly = [self.cart_to_iso(x, y) for x, y in rect]

        minx = min([x for x, y in iso_poly])
        miny = min([y for x, y in iso_poly])

        r = random.randint(1, 100)
        perlin = 100 * noise.pnoise2(grid_x / self.perlin_scale, grid_y / self.perlin_scale)

        tile = ''
        if not LOADMAP:
            if (perlin >= 15) or (perlin <= -35):
                tile = 'tree'
            else:
                if r == 1:
                    tile = 'tree'
                elif r == 2:
                    tile = 'rock'

        out = {
            'grid': [grid_x, grid_y],
            'cart_rect': rect,
            'iso_poly': iso_poly,
            'render_pos': [minx, miny],
            'tile': tile,
            'collision': False if tile == '' else True
        }

        return out

    def create_collision_matrix(self):
        collision_matrix = [[1 for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]
        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):
                if self.world[x][y]['collision']:
                    collision_matrix[y][x] = 0
        return collision_matrix

    def create_world_network(self):
        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):
                if self.buildings[x][y] is not None or self.world[x][y]['tile'] == '':
                    self.world_network.add_node((x, y))

        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):
                # for each node from the 1th row/column, check all neighbors and add edges between open ones
                for i, j in [[-1, 0], [1, 0], [0, -1], [0, 1]]:
                    nbrx = x + i
                    nbry = y + j
                    if nbrx < 0 or nbrx >= self.grid_length_x or nbry < 0 or nbry >= self.grid_length_y:
                        continue
                    if self.world[x][y]['tile'] in ['', 'towncenter'] and \
                            self.world[nbrx][nbry]['tile'] in ['', 'towncenter']:
                        self.world_network.add_edge((x, y), (nbrx, nbry))

    def cart_to_iso(self, x, y):
        iso_x = x - y
        iso_y = (x + y) / 2
        return iso_x, iso_y

    def mouse_to_grid(self, x, y, scroll):
        # transform to world position (removing camera scroll and offset)
        world_x = x - scroll.x - self.grass_tiles.get_width() / 2
        world_y = y - scroll.y
        # transform to cart (inverse of cart_to_iso)
        cart_y = (2 * world_y - world_x) / 2
        cart_x = cart_y + world_x
        # transform to grid coordinates
        grid_x = int(cart_x // TILE_SIZE)
        grid_y = int(cart_y // TILE_SIZE)
        return grid_x, grid_y

    def can_place_tile(self, grid_pos):
        mouse_on_panel = False
        for rect in [self.hud.resources_rect, self.hud.building_rect]:
            if rect.collidepoint(pg.mouse.get_pos()):
                mouse_on_panel = True

        if self.hud.select_panel_visible and self.hud.select_rect.collidepoint(pg.mouse.get_pos()):
                mouse_on_panel = True

        world_bounds = (0 <= grid_pos[0] < self.grid_length_x) and (0 <= grid_pos[1] < self.grid_length_x)

        if world_bounds and not mouse_on_panel:
            return True
        else:
            return False

    def write_world_network(self):
        for x, y in self.world_network.nodes:
            color = ''
            if self.buildings[x][y] is not None:
                color = (.5, .5, 0)
            elif self.world[x][y]['tile'] == '':
                color = (0, 1, 0)
            elif self.world[x][y]['tile'] == 'tree':
                color = (0, 1, 1)
            elif self.world[x][y]['tile'] == 'rock':
                color = (0, 0, 0)

            # scatter([self.grid_length_x - 1 - x], [y], c=(color,))
            scatter([y], [self.grid_length_x - 1 - x], c=(color,))
            # scatter([x], [self.grid_length_y - 1 - y], c=(color,))

        for n1, n2 in self.world_network.edges:
            x1, y1 = n1
            x1 = self.grid_length_x - 1 - x1
            # y1 = self.grid_length_y - 1 - y1
            x2, y2 = n2
            x2 = self.grid_length_x - 1 - x2
            # y2 = self.grid_length_y - 1 - y2


            # plot([x1, x2], [y1, y2], 'k')
            plot([y1, y2], [x1, x2], 'k')

        # nx.draw_networkx(self.world_network, with_labels=True)
        savefig('world_network.png')

    def write_map(self):
        f = open('map.txt', 'w')
        for x in range(self.grid_length_x):
            string = ''
            for y in range(self.grid_length_y):
                if self.buildings[x][y] is not None:
                    string += CHARMAP[self.buildings[x][y].name]
                else:
                    string += CHARMAP[self.world[x][y]['tile']]
                string += ','
            f.write(string[:-1] + '\n')

        f.close()

    def get_random_position(self):
        found = False
        x, y = None, None
        while not found:
            x = random.randint(0, self.grid_length_x - 1)
            y = random.randint(0, self.grid_length_y - 1)
            if self.world[x][y]['collision']:
                continue
            found = True
        return x, y

    def dist(self, pos1, pos2):
        x1, y1 = pos1[0], pos1[1]
        x2, y2 = pos2[0], pos2[1]
        return abs(x2 - x1) + abs(y2 - y1)

    def in_any_towncenter_radius(self, pos):
        for tc in self.towns:
            d = self.dist(pos, tc.loc)
            if d <= 16:
                return True
            for b in tc.buildings:
                d = self.dist(pos, b.loc)
                if d <= 16:
                    return True
        return False

    def in_towncenter_radius(self, pos, newtc=False):
        d = self.dist(pos, self.active_town_center.loc)
        if d <= 8:
            return True
        for b in self.active_town_center.buildings:
            d = self.dist(pos, b.loc)
            if newtc:
                if d <= 16:
                    return True
            else:
                if d <= 8:
                    return True
        return False

    def find_town_with_vacancy(self):
        for t in self.towns:
            if len(t.villagers) < t.housing_capacity:
                return t