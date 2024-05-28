# import pygame as pg
import random
import noise
from .settings import TILE_SIZE
from .buildings import *
from .utils import draw_text, load_images
from .resourcemanager import ResourceManager
from .techmanager import TechManager
import networkx as nx
from matplotlib.pyplot import plot, savefig, scatter, cla


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

    def __init__(self, entities, hud, camera, grid_length_x, grid_length_y, width, height):
        self.resource_manager = ResourceManager()
        self.entities = entities
        self.hud = hud
        self.screen = self.hud.screen
        self.camera = camera
        self.grid_length_x = grid_length_x
        self.grid_length_y = grid_length_y
        self.width = width
        self.height = height

        self.hud.parent = self

        self.perlin_scale = grid_length_x / 2

        self.grass_tiles = pg.Surface((grid_length_x * TILE_SIZE * 2,
                                       grid_length_y * TILE_SIZE + 2 * TILE_SIZE)
                                      ).convert_alpha()
        self.tiles = load_images()
        self.world_network = nx.Graph()
        self.world = self.create_world()

        self.buildings = [[None for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]
        self.workers = [[None for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]

        self.collision_matrix = self.create_collision_matrix()
        self.create_world_network()
        self.create_road_network()

        self.towns = []
        # choose a random spot on the map to place one initial town center
        self.place_towncenter()

        self.temp_tile = None

        self.selected_building = None
        self.selected_worker = None
        self.active_town_center = None
        self.highlights = []

        self.mouse_pos = None
        self.mouse_action = None

    def place_towncenter(self):
        if not LOADMAP:
            x, y = self.get_random_position()
            render_pos = self.world[x][y]['render_pos']
            grid_pos = (x, y)
            ent = TownCenter(render_pos, grid_pos, ResourceManager(), TechManager(), self.tiles)
            self.towns.append(ent)
            self.buildings[x][y] = ent
            self.entities.append(ent)

    def deselect_all(self):
        self.deselect_building()
        self.deselect_worker()
        self.hud.select_panel_visible = False

    def get_temp_tile(self, grid_pos):
        # grab a copy of the image to place over the tile with the mouse
        img = self.hud.structure_to_build['image'].copy()
        img.set_alpha(100)

        render_pos = self.world[grid_pos[0]][grid_pos[1]]['render_pos']
        iso_poly = self.world[grid_pos[0]][grid_pos[1]]['iso_poly']
        collision = self.world[grid_pos[0]][grid_pos[1]]['collision']

        # can't place blocks on spaces containing buildings
        if self.buildings[grid_pos[0]][grid_pos[1]] is not None:
            collision = True

        # can't place blocks on spaces containing workers
        if self.workers[grid_pos[0]][grid_pos[1]] is not None:
            collision = True

        self.temp_tile = {
            'image': img,
            'render_pos': render_pos,
            'iso_poly': iso_poly,
            'collision': collision,
            'grid_pos': grid_pos,
            'name': self.hud.structure_to_build['name']
        }

    def create_towncenter(self, grid_pos):
        if not self.in_any_towncenter_radius(grid_pos):
            ent = TownCenter(self.temp_tile['render_pos'], grid_pos, ResourceManager(), TechManager(), self.tiles)
            ent.techmanager.technologies = self.active_town_center.techmanager.technologies.copy()
            # check to see if merchants need a target town
            for town in self.towns:
                m = town.get_stranded_merchant()
                if m is not None:
                    m.targettown = ent
            self.towns.append(ent)

            return ent

    def create_town_building(self, grid_pos):
        if self.hud.structure_to_build['name'] == 'well':
            return Well(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager)
        elif self.hud.structure_to_build['name'] == 'chopping':
            return ChoppingBlock(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager)
        elif self.hud.structure_to_build['name'] == 'quarry':
            return Quarry(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager)
        elif self.hud.structure_to_build['name'] == 'road':
            return Road(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager)
        elif self.hud.structure_to_build['name'] == 'wheatfield':
            return Wheatfield(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager)
        elif self.hud.structure_to_build['name'] == 'market':
            return Market(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager)
        elif self.hud.structure_to_build['name'] == 'workbench':
            return Workbench(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager)
        elif self.hud.structure_to_build['name'] == 'house':
            return House(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager)

    def add_building_to_town(self, ent):
        self.active_town_center.buildings.append(ent)
        if self.hud.structure_to_build['name'] in self.active_town_center.num_buildings:
            self.active_town_center.num_buildings[self.hud.structure_to_build['name']] += 1
        else:
            self.active_town_center.num_buildings[self.hud.structure_to_build['name']] = 1
        if self.hud.structure_to_build['name'] == 'house':
            self.active_town_center.housing_capacity += 5

    def place_entity(self, ent):
        self.collision_matrix[ent.loc[1]][ent.loc[0]] = 0
        self.entities.append(ent)
        self.buildings[ent.loc[0]][ent.loc[1]] = ent

        # print('placed entity: ', self.buildings[ent.loc[0]][ent.loc[1]], 'at location ', ent.loc)

        # if the building is not a town center, assign it to the currently active one
        if self.hud.structure_to_build['name'] != 'towncenter':
            self.add_building_to_town(ent)
        # build a new town center using the resources of the active one
        else:
            self.active_town_center.resourcemanager.apply_cost('towncenter')
            # self.collision_matrix[grid_pos[1]][grid_pos[0]] = 0

    def handle_structure_to_build(self, grid_pos):
        # if the mouse is over the map and not over a panel, create a temp tile
        if self.can_place_tile(grid_pos):
            self.get_temp_tile(grid_pos)

            # if right click and the building can be placed, do so
            if self.mouse_action[0] and not self.temp_tile['collision']:
                ent = None
                if self.hud.structure_to_build['name'] == 'towncenter':
                    ent = self.create_towncenter(grid_pos)
                else:
                    if self.in_towncenter_radius(grid_pos):
                        ent = self.create_town_building(grid_pos)
                if ent is not None:
                    self.place_entity(ent)
                    if ent.name == 'road':
                        self.update_road_network(grid_pos)

    def check_select_worker(self, grid_pos):
        worker = self.workers[grid_pos[0]][grid_pos[1]]
        if self.mouse_action[0] and (worker is not None):
            if not worker.is_visible():
                return
            # if another worker was already selected, deselect them
            if self.hud.selected_worker is not None:
                self.deselect_worker()
                # self.hud.selected_worker.selected = False

            # set selected worker data
            self.selected_worker = grid_pos
            self.hud.selected_worker = worker
            self.hud.selected_worker.selected = True
            self.hud.select_panel_visible = True

            # if a building was selected, deselect it
            if self.selected_building is not None:
                self.deselect_building()

    def deselect_worker(self):
        if self.selected_worker is not None:
            self.hud.selected_worker.selected = False
        self.selected_worker = None
        self.hud.selected_worker = None
        self.hud.select_panel_visible = False
        self.highlights = []

    def deselect_building(self):
        self.selected_building = None
        self.hud.selected_building = None
        self.hud.select_panel_visible = False
        self.highlights = []

    def check_select_building(self, grid_pos):

        # check if there is a building in this position
        building = self.buildings[grid_pos[0]][grid_pos[1]]
        if self.mouse_action[0]:
            if building is not None:

            # if there is a selected worker, check if it is over the building
            # return if so, otherwise deselect it
                if self.selected_worker is not None:
                    if self.selected_worker == grid_pos:
                        return
                    self.deselect_worker()

                # this part is supposed to let the user double click on a town center and select it
                # instead of using the button.  it wants to select the town center immediately though.
                # need to fix this when I do click and drag.

                # if self.hud.selected_building is not None:
                #     if building.name == 'towncenter' and self.hud.selected_building is building:
                #         self.active_town_center = building

                # update selected building data
                if self.selected_building is not None:
                    self.deselect_building()
                self.selected_building = grid_pos
                self.hud.selected_building = building
                self.hud.select_panel_visible = True

    def handle_select_action(self, grid_pos):
        # make sure user didn't click on a visible panel or outside the screen
        if self.can_place_tile(grid_pos):
            self.check_select_worker(grid_pos)
            self.check_select_building(grid_pos)

    def update(self):

        self.mouse_pos = pg.mouse.get_pos()
        self.mouse_action = pg.mouse.get_pressed()
        self.temp_tile = None

        # if the user left-clicks, deselect anything that is selected
        if self.mouse_action[2]:
            self.deselect_all()

        # get grid coordinates of current mouse position
        grid_pos = self.mouse_to_grid(self.mouse_pos[0], self.mouse_pos[1], self.camera.scroll)

        # user wants to place a tile
        if self.hud.structure_to_build is not None:
            self.handle_structure_to_build(grid_pos)

        # user wants to select a building or worker
        else:
            self.handle_select_action(grid_pos)

    def highlight_active_towncenter(self, building, render_pos):
        mask = pg.mask.from_surface(building.image).outline()
        mask = [(x + render_pos[0] + self.grass_tiles.get_width() / 2 + self.camera.scroll.x,
                 y + render_pos[1] - (building.image.get_height() - TILE_SIZE) + self.camera.scroll.y)
                for x, y in mask]
        pg.draw.polygon(self.screen, (0, 255, 0), mask, 3)

    def highlight_worker(self, worker, color):
        x, y = worker.tile['grid']
        render_pos = [self.world[x][y]['render_pos'][0] + worker.offsets[0],
                      self.world[x][y]['render_pos'][1] + worker.offsets[1]]
        mask = pg.mask.from_surface(worker.image).outline()
        mask = [(x + render_pos[0] + self.grass_tiles.get_width() / 2 + self.camera.scroll.x,
                 y + render_pos[1] - (worker.image.get_height() - TILE_SIZE) + self.camera.scroll.y)
                for x, y in mask]
        pg.draw.polygon(self.screen, color, mask, 3)

    def highlight_selected_building(self, building, render_pos):
        mask = pg.mask.from_surface(building.image).outline()
        mask = [(x + render_pos[0] + self.grass_tiles.get_width() / 2 + self.camera.scroll.x,
                 y + render_pos[1] - (building.image.get_height() - TILE_SIZE) + self.camera.scroll.y)
                for x, y in mask]
        pg.draw.polygon(self.screen, (255, 255, 255), mask, 3)
        if building.name == 'house':
            # get all occupants and highlight them
            for w in building.occupants:
                if w.is_visible():
                    self.highlights.append(w)
                    # self.highlight_worker(w, (0, 0, 255))
        elif building.name in ['chopping', 'well', 'wheatfield', 'quarry']:
            # get all workers and highlight them
            for w in building.workers:
                if w.is_visible():
                    self.highlights.append(w)
                    # self.highlight_worker(w, (0, 0, 255))

    def highlight_building(self, building, color):
        x, y = building.loc
        render_pos = self.world[x][y]['render_pos']
        mask = pg.mask.from_surface(building.image).outline()
        mask = [(x + render_pos[0] + self.grass_tiles.get_width() / 2 + self.camera.scroll.x,
                 y + render_pos[1] - (building.image.get_height() - TILE_SIZE) + self.camera.scroll.y)
                for x, y in mask]
        pg.draw.polygon(self.screen, color, mask, 3)

    def highlight_selected_worker(self, worker, render_pos):
        mask = pg.mask.from_surface(worker.image).outline()
        mask = [(x + render_pos[0] + self.grass_tiles.get_width() / 2 + self.camera.scroll.x,
                 y + render_pos[1] - (worker.image.get_height() - TILE_SIZE) + self.camera.scroll.y)
                for x, y in mask]
        pg.draw.polygon(self.screen, (255, 255, 255), mask, 3)
        if worker.workplace is not None:
            # get workplace and highlight it
            self.highlights.append(worker.workplace)
            # self.highlight_building(worker.workplace, (0, 0, 255))
        if worker.home is not None:
            # get house and highlight it
            self.highlights.append(worker.home)
            # self.highlight_building(worker.home, (0, 0, 255))

    def draw_terrain_tile(self, tile, render_pos):
        if tile != '':
            self.screen.blit(self.tiles[tile],
                             (render_pos[0] + self.grass_tiles.get_width() / 2 + self.camera.scroll.x,
                              render_pos[1] - (self.tiles[tile].get_height() - TILE_SIZE) + self.camera.scroll.y))

    def draw_building(self, x, y, render_pos):
        # draw buildings
        building = self.buildings[x][y]
        if building is not None:
            self.screen.blit(building.image,
                             (render_pos[0] + self.grass_tiles.get_width() / 2 + self.camera.scroll.x,
                              render_pos[1] - (building.image.get_height() - TILE_SIZE) + self.camera.scroll.y))

            # place outline around active town center
            if building is self.active_town_center:
                self.highlight_active_towncenter(building, render_pos)

            if building in self.highlights:
                self.highlight_building(building, (0, 0, 255))

            # draw white outline around selected object
            if self.selected_building is not None:
                if (x, y) == self.selected_building:
                    self.highlight_selected_building(building, render_pos)

                # add masks for workers associated with this building

    def draw_worker(self, x, y, render_pos):
        worker = self.workers[x][y]
        if worker is not None:
            if worker.arrived_at_home or worker.arrived_at_work:
                return
            if worker.arrived_at_towncenter and not worker.moving:
                return
                # if self.selected_worker is worker:
                #     self.deselect_all()
                # return
            self.screen.blit(worker.image,
                             (render_pos[0] + worker.offsets[0] + self.grass_tiles.get_width() / 2 + self.camera.scroll.x,
                              render_pos[1] + worker.offsets[1] - (worker.image.get_height() - TILE_SIZE) + self.camera.scroll.y))

            if self.selected_worker is not None:
                if (x == self.selected_worker[0]) and (y == self.selected_worker[1]):
                    self.highlight_selected_worker(worker, [render_pos[0] + worker.offsets[0],
                                                            render_pos[1] + worker.offsets[1]])

            if worker in self.highlights:
                self.highlight_worker(worker, (0, 0, 255))

                # add masks for workplace associated with worker

    def draw_radius_indicator(self, x, y):
        iso_poly = [(x + self.grass_tiles.get_width() / 2 + self.camera.scroll.x, y + self.camera.scroll.y) for x, y
                    in self.world[x][y]['iso_poly']]

        if self.temp_tile['name'] == 'towncenter':
            self.draw_badradius_indicator(x, y, iso_poly)
        else:
            self.draw_goodradius_indicator(x, y, iso_poly)

    def draw_goodradius_indicator(self, x, y, iso_poly):
        if self.in_towncenter_radius(self.world[x][y]['grid']):
            pg.draw.polygon(self.screen, (255, 255, 255, 255), iso_poly, 3)

    def draw_badradius_indicator(self, x, y, iso_poly):
        if self.in_any_towncenter_radius(self.world[x][y]['grid']):
            pg.draw.polygon(self.screen, (255, 0, 0, 255), iso_poly, 3)

    def draw_build_indicator(self, grid_pos, iso_poly):

        # red indicator if tile cannot be placed
        if self.temp_tile['collision'] or (self.workers[grid_pos[0]][grid_pos[1]] is not None):
            pg.draw.polygon(self.screen, (255, 0, 0, 100), iso_poly, 3)
        else:
            if self.temp_tile['name'] == 'towncenter':
                if self.in_any_towncenter_radius(grid_pos):
                    pg.draw.polygon(self.screen, (255, 0, 0, 100), iso_poly, 3)
                else:
                    pg.draw.polygon(self.screen, (0, 255, 0, 100), iso_poly, 3)
            else:
                if self.in_towncenter_radius(grid_pos):
                    pg.draw.polygon(self.screen, (0, 255, 0, 100), iso_poly, 3)
                else:
                    pg.draw.polygon(self.screen, (255, 0, 0, 100), iso_poly, 3)

    def draw_structure_to_build(self, grid_pos):

        iso_poly = self.temp_tile['iso_poly']
        iso_poly = [(x + self.grass_tiles.get_width() / 2 + self.camera.scroll.x, y + self.camera.scroll.y) for x, y in
                    iso_poly]

        self.draw_build_indicator(grid_pos, iso_poly)

        render_pos = self.temp_tile['render_pos']
        self.screen.blit(self.temp_tile['image'],
                         (render_pos[0] + self.grass_tiles.get_width() / 2 + self.camera.scroll.x,
                          render_pos[1] - (self.temp_tile['image'].get_height() - TILE_SIZE) + self.camera.scroll.y))

    def draw(self):

        # draw the basic terrain
        self.screen.blit(self.grass_tiles, (self.camera.scroll.x, self.camera.scroll.y))

        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):

                # iterate through every tile in the world
                render_pos = self.world[x][y]['render_pos']
                tile = self.world[x][y]['tile']

                free = all([self.workers[x][y] is None,
                            self.buildings[x][y] is None,
                            tile == ''])

                if free and self.temp_tile is not None:
                    self.draw_radius_indicator(x, y)

                # if it is not a grass tile, mark it as not free and draw the tile
                self.draw_terrain_tile(tile, render_pos)
                # draw buildings
                self.draw_building(x, y, render_pos)
                # draw workers
                self.draw_worker(x, y, render_pos)

        # place a building
        if self.temp_tile is not None:

            self.mouse_pos = pg.mouse.get_pos()
            grid_pos = self.mouse_to_grid(self.mouse_pos[0], self.mouse_pos[1], self.camera.scroll)

            self.draw_structure_to_build(grid_pos)

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
                # add a node to the walkable network for any building or grass tile
                if self.buildings[x][y] is not None or self.world[x][y]['tile'] == '':
                    self.world_network.add_node((x, y))

        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):
                # for each node, check all neighbors and add edges between open ones
                for i, j in [[-1, 0], [1, 0], [0, -1], [0, 1]]:
                    nbrx = x + i
                    nbry = y + j

                    # continue if out of bounds
                    if nbrx < 0 or nbrx >= self.grid_length_x or nbry < 0 or nbry >= self.grid_length_y:
                        continue

                    # if both the current tile and the neighbor are walkable, add an edge between them
                    if self.world[x][y]['tile'] in ['', 'towncenter'] and \
                            self.world[nbrx][nbry]['tile'] in ['', 'towncenter']:
                        self.world_network.add_edge((x, y), (nbrx, nbry), weight=1)

    def create_road_network(self):
        self.road_network = nx.Graph()

    def update_road_network(self, pos):
        print('Updating road network')
        self.road_network.add_node((pos[0], pos[1]))
        print(self.road_network.nodes)
        nbrs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for i in range(len(self.buildings)):
            for j in range(len(self.buildings[i])):
                if self.buildings[i][j] is not None:
                    print(f'{self.buildings[i][j]} {(i, j)}')
        for nbr in nbrs:
            if 0 <= pos[0] + nbr[0] < self.grid_length_x and 0 <= pos[1] + nbr[1] < self.grid_length_y:
                print('nbr is good: ', pos[0] + nbr[0], ',', pos[1] + nbr[1])
                print('nbr bldg: ', self.buildings[pos[0] + nbr[0]][pos[1] + nbr[1]])
                if self.buildings[pos[0] + nbr[0]][pos[1] + nbr[1]] is not None:
                    if self.buildings[pos[0] + nbr[0]][pos[1] + nbr[1]].name == 'road':
                        self.road_network.add_edge(pos, (pos[0] + nbr[0], pos[1] + nbr[1]))

    def cart_to_iso(self, x, y):
        # get isometric coordinates from cartesian ones
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
        # check if mouse is on resources or building panel
        mouse_on_panel = False
        self.mouse_pos = pg.mouse.get_pos()
        for rect in [self.hud.resources_rect]:
            if rect.collidepoint(self.mouse_pos):
                mouse_on_panel = True

        # only check if mouse is over select panel when it is showing
        if self.hud.select_panel_visible:
            if self.hud.select_rect.collidepoint(self.mouse_pos):
                mouse_on_panel = True

        if self.active_town_center is not None:
            if self.hud.town_actions_rect.collidepoint(self.mouse_pos):
                mouse_on_panel = True

        # check if mouse is outside of the map
        world_bounds = (0 <= grid_pos[0] < self.grid_length_x) and (0 <= grid_pos[1] < self.grid_length_x)

        if world_bounds and not mouse_on_panel:
            return True
        else:
            return False

    def write_world_network(self):
        xs = []
        ys = []
        colors = []
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
            xs.append(x)
            ys.append(self.grid_length_y - 1 - y)
            colors.append(color)

        scatter(xs, ys, c=colors)

        for n1, n2 in self.world_network.edges:
            x1, y1 = n1
            # x1 = self.grid_length_x - 1 - x1
            y1 = self.grid_length_y - y1 - 1
            x2, y2 = n2
            # x2 = self.grid_length_x - 1 - x2
            y2 = self.grid_length_y - y2 - 1

            plot([x1, x2], [y1, y2], 'k')


        # nx.draw_networkx(self.world_network, with_labels=True)
        savefig('world_network.png')
        cla()

    def write_road_network(self):
        xs = []
        ys = []
        colors = []
        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):
                if (x, y) in self.road_network.nodes:
                    color = (.5, .5, 0)
                    print('Node: ', (x, y))
                    # scatter([y], [self.grid_length_x - 1 - x], c=(color,))
                else:
                    color = (1., 1., 1.)
                    # scatter([y], [self.grid_length_x - 1 - x], c=(color,))
                # xs.append(self.grid_length_x - 1 - x)
                xs.append(x)
                ys.append(self.grid_length_y - 1 - y)
                # ys.append(y)
                colors.append(color)
        # scatter(ys, xs, c=colors)
        scatter(xs, ys, c=colors)

        for n1, n2 in self.road_network.edges:
            x1, y1 = n1
            y1 = self.grid_length_y - 1 - y1
            # x1 = self.grid_length_x - 1 - x1
            x2, y2 = n2
            y2 = self.grid_length_y - 1 - y2
            # x2 = self.grid_length_x - 1 - x2

            print((x1, y1), (x2, y2))

            # plot([y1, y2], [x1, x2], 'k')
            plot([x1, x2], [y1, y2], 'k')

        # nx.draw_networkx(self.world_network, with_labels=True)
        print(self.road_network.edges)
        savefig('road_network.png')

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
        # find a random unoccupied tile on the map
        found = False
        x, y = None, None
        while not found:
            x = random.randint(0, self.grid_length_x - 1)
            y = random.randint(0, self.grid_length_y - 1)
            if self.world[x][y]['collision']:
                continue
            found = True
        return x, y

    def get_random_position_along_border(self):
        # find a random unoccupied tile on the edge of the map
        found = False
        x, y = None, None
        while not found:
            num1 = random.randint(0, self.grid_length_x - 1)
            num2 = random.randint(0, self.grid_length_x - 1)

            if self.world[num1][0]['collision'] and self.world[0][num2]['collision']:
                continue
            elif not self.world[num1][0]['collision']:
                found = True
                x = num1
                y = 0
            elif not self.world[0][num2]['collision']:
                found = True
                x = 0
                y = num2
        return x, y

    def dist(self, pos1, pos2):
        # get the simple hamming distance between two tiles
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