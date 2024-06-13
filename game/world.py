# import pygame as pg
import random
import noise
from .settings import TILE_SIZE, LOAD
from .buildings import *
from .utils import load_images, load_sounds
from .resourcemanager import ResourceManager
from .techmanager import TechManager
from .workers import Worker
import networkx as nx
from matplotlib.pyplot import plot, savefig, scatter, cla


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

    def __init__(self, entities, hud, camera, grid_length_x, grid_length_y, width, height,
                 savedata=None):
        self.entities = entities
        self.hud = hud
        self.screen = self.hud.screen
        self.camera = camera
        self.grid_length_x = grid_length_x
        self.grid_length_y = grid_length_y
        self.width = width
        self.height = height
        self.ready_to_delete = False

        self.bldg_ctr = 0
        self.wrkr_ctr = 0

        self.hud.parent = self

        if savedata:
            self.perlin_scale = float(savedata['world']['perlin'])
        else:
            self.perlin_scale = grid_length_x / 2

        self.grass_tiles = pg.Surface((grid_length_x * TILE_SIZE * 2,
                                       grid_length_y * TILE_SIZE + 2 * TILE_SIZE)
                                      ).convert_alpha()
        self.tiles = load_images()
        self.sounds = load_sounds()
        self.world_network = nx.Graph()
        self.world = self.create_world()

        self.buildings = [[None for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]
        self.workers = [[None for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]

        self.collision_matrix = self.create_collision_matrix()
        self.create_world_network()
        # for edge in self.world_network.edges:
        #     print(self.world_network.edges[edge]['weight'])
        self.create_road_network()

        self.towns = []

        # choose a random spot on the map to place one initial town center

        if savedata is None:
            self.place_towncenter()
        else:
            self.load_savedata(savedata)

        self.temp_tile = None

        self.selected_building = None
        self.selected_worker = None
        self.active_town_center = None
        self.highlights = []

        self.mouse_pos = None
        self.mouse_action = None

    def place_towncenter(self):
        x, y = self.get_random_position()
        render_pos = self.world[x][y]['render_pos']
        grid_pos = (x, y)
        self.bldg_ctr += 1
        ent = TownCenter(render_pos, grid_pos, ResourceManager(), TechManager(), self.tiles, f'blgd{self.bldg_ctr}')
        self.towns.append(ent)
        self.buildings[x][y] = ent
        self.entities.append(ent)

        for nbr in [[0, 1], [1, 0], [0, -1], [-1, 0]]:
            nbrx, nbry = x + nbr[0], y + nbr[1]
            if not (0 <= nbrx < self.grid_length_x) or not (0 <= nbry < self.grid_length_y):
                continue
            if self.world[nbrx][nbry]['tile'] == '':
                self.world_network.edges[((x, y), (nbrx, nbry))]['weight'] = 1000

        # for edge in self.world_network.edges:
        #     print(self.world_network.edges[edge]['weight'])

    def load_savedata(self, savedata):
        data = savedata['buildings']
        town_bldgs = {}
        towns = {}
        # instantiate town centers
        for d in data:
            if d['name'] == 'towncenter':
                loc = d['loc'][1:-1].split(',')
                x, y = int(loc[0]), int(loc[1])
                render = d['pos'][1:-1].split(',')
                rx, ry = float(render[0]), float(render[1])
                ent = TownCenter((rx, ry), (x, y), ResourceManager(), TechManager(), self.tiles,
                                 d['id'])
                goodslist = d['inventory'].split(',')
                for entry in goodslist:
                    splitline = entry.split(':')
                    ent.resourcemanager.resources[splitline[0]] = int(splitline[1])
                techs = d.get('technologies', None)
                if techs is not None:
                    ent.techmanager.technologies = techs.split(',')
                techcooldowns = d.get('cooldowns', None)
                if techcooldowns is not None:
                    cooldownlist = techcooldowns.split(',')
                    for item in cooldownlist:
                        splitline = item.split(':')
                        ent.techmanager.researchcooldowns[splitline[0]] = 0
                techresearch = d.get('currentresearch', None)
                if techresearch is not None:
                    cooldownlist = techresearch.split(',')
                    for item in cooldownlist:
                        splitline = item.split(':')
                        ent.techmanager.current_research[splitline[0]] = int(splitline[1])
                ent.techmanager.update_unlock_status()
                bldgs = d['buildings'].split(',')
                town_bldgs[d['id']] = bldgs
                towns[d['id']] = ent

                self.bldg_ctr += 1
                self.towns.append(ent)
                self.buildings[x][y] = ent
                self.entities.append(ent)

        bldgs = {}

        # instantiate other buildings
        for d in data:
            if d['name'] != 'towncenter':
                loc = d['loc'][1:-1].split(',')
                x, y = int(loc[0]), int(loc[1])
                render = d['pos'][1:-1].split(',')
                rx, ry = float(render[0]), float(render[1])
                self.bldg_ctr += 1

                rm = towns[d['town']].resourcemanager

                ent = None
                if d['name'] == 'well':
                    ent = Well((rx, ry), (x, y), rm, d['id'])
                elif d['name'] == 'chopping':
                    ent = ChoppingBlock((rx, ry), (x, y), rm, d['id'])
                elif d['name'] == 'quarry':
                    ent = Quarry((rx, ry), (x, y), rm, d['id'])
                elif d['name'] == 'road':
                    ent = Road(self.temp_tile['render_pos'], (x, y), rm, d['id'])
                elif d['name'] == 'wheatfield':
                    ent = Wheatfield((rx, ry), (x, y), rm, d['id'])
                elif ['name'] == 'market':
                    ent = Market((rx, ry), (x, y), rm, d['id'])
                elif d['name'] == 'workbench':
                    ent = Workbench((rx, ry), (x, y), rm, d['id'])
                elif d['name'] == 'house':
                    ent = House((rx, ry), (x, y), rm, d['id'])
                elif d['name'] == 'temple':
                    ent = Temple((rx, ry), (x, y), rm, d['id'])

                if 'inventory' in d:
                    inv = d['inventory'].split(',')
                    for item in inv:
                        splitline = item.split(':')
                        ent.storage[splitline[0]] = float(splitline[1])

                bldgs[d['id']] = ent
                self.buildings[x][y] = ent
                self.entities.append(ent)
                for t in self.towns:
                    if t.id == d['town']:
                        t.buildings.append(ent)
                        if ent.name in t.num_buildings:
                            t.num_buildings[ent.name] += 1
                        else:
                            t.num_buildings[ent.name] = 1
                        if ent.name == 'house':
                            t.housing_capacity += 5
                        break

        data = savedata['workers']
        for d in data:
            unique_id = d['id']
            name = d['name']
            loc = d['pos'][1:-1].split(',')
            x, y = int(loc[0]), int(loc[1])
            home = d['home']
            work = d['work']
            inv = d['inventory']
            skills = d['skills']
            town = d['town']
            energy = int(d['energy'])

            w = Worker(self.world[x][y], self, unique_id)
            w.name = name
            w.energy = energy
            if town != 'None':
                w.town = towns[town]
                w.town.villagers.append(w)
            if home != 'None':
                w.home = bldgs[home]
                w.home.occupants.append(w)
            if work != 'None':
                w.workplace = bldgs[work]
                if w.workplace.name == 'well':
                    w.occupation = 'Water Carrier'
                    w.image = pg.transform.scale(self.tiles['watercarrier'],
                                                 (self.tiles['watercarrier'].get_width() * 2,
                                                  self.tiles['watercarrier'].get_height() * 2))
                if w.workplace.name == 'wheatfield':
                    w.occupation = 'Farmer'
                    w.image = pg.transform.scale(self.tiles['farmer'],
                                                 (self.tiles['farmer'].get_width() * 2,
                                                  self.tiles['farmer'].get_height() * 2))
                if w.workplace.name == 'chopping':
                    w.occupation = 'Woodcutter'
                    w.image = pg.transform.scale(self.tiles['woodcutter'],
                                                 (self.tiles['woodcutter'].get_width() * 2,
                                                  self.tiles['woodcutter'].get_height() * 2))
                if w.workplace.name == 'quarry':
                    w.occupation = 'Quarryman'
                    w.image = pg.transform.scale(self.tiles['quarryman'],
                                                 (self.tiles['quarryman'].get_width() * 2,
                                                  self.tiles['quarryman'].get_height() * 2))
                if w.workplace.name == 'workbench':
                    w.occupation = 'Tool Maker'
                    w.image = pg.transform.scale(self.tiles['farmer'],
                                                 (self.tiles['farmer'].get_width() * 2,
                                                  self.tiles['farmer'].get_height() * 2))
                if w.workplace.name == 'market':
                    w.occupation = 'Merchant'
                    w.image = pg.transform.scale(self.tiles['merchant'],
                                                 (self.tiles['merchant'].get_width() * 2,
                                                  self.tiles['merchant'].get_height() * 2))
                    if d['targettown'] != 'None':
                        w.targettown = towns[d['targettown']]
                w.workplace.workers.append(w)

            # assign travel variables and get a path
            w.arrived_at_towncenter = True if d['aatc'] == 'True' else False
            w.arrived_at_work = True if d['aaw'] == 'True' else False
            w.arrived_at_home = True if d['aah'] == 'True' else False
            w.going_to_towncenter = True if d['gttc'] == 'True' else False
            w.going_to_work = True if d['gtw'] == 'True' else False
            w.going_home = True if d['gh'] == 'True' else False
            w.collected_for_work = True if d['collected'] == 'True' else False
            w.collecting_for_work = True if d['collecting'] == 'True' else False

            w.path_index = 0
            w.path = []
            rawpath = d['path'].split(',')
            for i in range(0, len(rawpath), 2):
                x, y = rawpath[i], rawpath[i+1]
                x = x.replace('(', '')
                x = x.replace(' ', '')
                x = x.replace(')', '')
                y = y.replace('(', '')
                y = y.replace(' ', '')
                y = y.replace(')', '')
                w.path.append((int(x), int(y)))

            w.check_end_of_path()

            if inv:
                splitline = inv.split(',')
                for item in splitline:
                    key, value = item.split(':')
                    value = int(value)
                    w.inventory[key] = value
            if skills:
                splitline = skills.split(',')
                for item in splitline:
                    key, value = item.split(':')
                    value = int(value)
                    w.skills[key] = value

        # final updates on building stats
        for b in bldgs:
            bldgs[b].currently_in_building = len([w for w in bldgs[b].workers if w.arrived_at_work])
            bldgs[b].resourcecooldown = 0
            bldgs[b].update_percent_employed()

    def deselect_all(self):
        self.deselect_building()
        self.deselect_worker()
        self.hud.select_panel_visible = False
        self.ready_to_delete = False

    def get_temp_tile(self, grid_pos):

        # TODO: this doesn't need to be updated every time, we can just update the grid/rendering position until
        #  it is built

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
            self.bldg_ctr += 1
            ent = TownCenter(self.temp_tile['render_pos'], grid_pos, ResourceManager(), TechManager(), self.tiles,
                             f'bldg{self.bldg_ctr}')
            ent.techmanager.technologies = self.active_town_center.techmanager.technologies.copy()
            # check to see if merchants need a target town
            for town in self.towns:
                m = town.get_stranded_merchant()
                if m is not None:
                    m.targettown = ent
            self.towns.append(ent)

            self.sounds['towncenter'].play()

            return ent

    def create_town_building(self, grid_pos):
        name = self.hud.structure_to_build['name']
        ent = None
        if name == 'well':
            ent = Well(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager, f'bldg{self.bldg_ctr}')
        elif name == 'chopping':
            ent = ChoppingBlock(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager, f'bldg{self.bldg_ctr}')
        elif name == 'quarry':
            ent = Quarry(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager, f'bldg{self.bldg_ctr}')
        elif name == 'road':
            ent = Road(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager, f'bldg{self.bldg_ctr}')
        elif name == 'wheatfield':
            ent = Wheatfield(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager, f'bldg{self.bldg_ctr}')
        elif name == 'market':
            ent = Market(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager, f'bldg{self.bldg_ctr}')
        elif name == 'workbench':
            ent = Workbench(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager, f'bldg{self.bldg_ctr}')
        elif name == 'house':
            ent = House(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager, f'bldg{self.bldg_ctr}')
        elif name == 'temple':
            ent = Temple(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager,
                        f'bldg{self.bldg_ctr}')
        elif name == 'coalmine':
            ent = Coalmine(self.temp_tile['render_pos'], grid_pos, self.active_town_center.resourcemanager,
                         f'bldg{self.bldg_ctr}')

        if ent is not None:
            self.bldg_ctr += 1
            if name in self.sounds:
                self.sounds[name].play()
        return ent

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

            if self.mouse_action[0]:
                if not self.ready_to_delete:

                    # if left click and the building can be placed, do so
                    if not self.temp_tile['collision']:
                        ent = None
                        if self.hud.structure_to_build['name'] == 'towncenter':
                            ent = self.create_towncenter(grid_pos)
                        else:
                            if self.in_towncenter_radius(grid_pos):
                                ent = self.create_town_building(grid_pos)
                        if ent is not None:
                            ent.town = self.active_town_center.id
                            self.place_entity(ent)
                            if ent.name == 'road':
                                self.update_road_network(grid_pos)

                # delete the building
                else:
                    bldg = self.buildings[grid_pos[0]][grid_pos[1]]
                    if bldg is not None:
                        if bldg.name == 'house':
                            self.active_town_center.housing_capacity -= 5
                            for w in bldg.occupants:
                                w.home = None
                                w.reset_travel_vars()
                        else:
                            for w in bldg.workers:
                                w.workplace = None

                                # this only changes the image, needs to do the whole job of unassigning a worker
                                self.active_town_center.unassign_worker(w)
                                w.reset_travel_vars()

                        # remove it from the face of the earth
                        self.active_town_center.buildings.remove(bldg)
                        self.active_town_center.num_buildings[bldg.name] -= 1
                        self.entities.remove(bldg)
                        self.buildings[grid_pos[0]][grid_pos[1]] = None
                        self.world[grid_pos[0]][grid_pos[1]]['collision'] = False
                        del bldg
                        # self.ready_to_delete = False
                        self.sounds['delete'].play()


    def check_select_worker(self, grid_pos):
        worker = self.workers[grid_pos[0]][grid_pos[1]]
        if (worker is not None):
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
        if self.mouse_action[0]:
            if self.can_place_tile(grid_pos):
                self.check_select_worker(grid_pos)
                self.check_select_building(grid_pos)

    def update(self):

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
        elif building.name in ['chopping', 'well', 'wheatfield', 'quarry']:
            # get all workers and highlight them
            for w in building.workers:
                if w.is_visible():
                    self.highlights.append(w)

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
        if worker.home is not None:
            # get house and highlight it
            self.highlights.append(worker.home)

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

        if self.ready_to_delete:
            building = self.buildings[grid_pos[0]][grid_pos[1]]
            if building is not None:
                pg.draw.polygon(self.screen, (0, 255, 0), iso_poly, 3)
            else:
                pg.draw.polygon(self.screen, (255, 0, 0, 100), iso_poly, 3)
            return

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

        if self.ready_to_delete:
            if self.buildings[grid_pos[0]][grid_pos[1]] is not None:
                render_pos = self.temp_tile['render_pos']
                self.temp_tile['image'] = self.buildings[grid_pos[0]][grid_pos[1]].image.copy()
                self.temp_tile['image'].fill((190, 0, 0, 100), special_flags=pg.BLEND_ADD)
                self.screen.blit(self.temp_tile['image'],
                                 (render_pos[0] + self.grass_tiles.get_width() / 2 + self.camera.scroll.x,
                                  render_pos[1] - (
                                              self.temp_tile['image'].get_height() - TILE_SIZE) + self.camera.scroll.y))
        if not self.ready_to_delete:
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

                if free and self.temp_tile is not None and not self.ready_to_delete:
                    self.draw_radius_indicator(x, y)

                # if it is not a grass tile, mark it as not free and draw the tile
                self.draw_terrain_tile(tile, render_pos)
                # draw buildings
                self.draw_building(x, y, render_pos)
                # draw workers
                self.draw_worker(x, y, render_pos)

        # place a building
        if self.temp_tile is not None:

            # self.mouse_pos = pg.mouse.get_pos()
            grid_pos = self.mouse_to_grid(self.mouse_pos[0], self.mouse_pos[1], self.camera.scroll)

            self.draw_structure_to_build(grid_pos)

    def create_world(self):

        matrix = None
        if LOAD:
            f = open(MAPNAME, 'r')
            matrix = [i[:-1].split(',') for i in f.readlines()]
            f.close()

        world = []

        for grid_x in range(self.grid_length_x):
            world.append([])
            for grid_y in range(self.grid_length_y):
                world_tile = self.grid_to_world(grid_x, grid_y)

                if LOAD:
                    # char = R_CHARMAP[matrix[grid_x][grid_y]]
                    if matrix[grid_x][grid_y] == 'r':
                        char = 'rock'
                    elif matrix[grid_x][grid_y] == 't':
                        char = 'tree'
                    else:
                        char = ''
                    world_tile['tile'] = char
                    if char != '':
                        world_tile['collision'] = True
                    else:
                        world_tile['collision'] = False

                world[grid_x].append(world_tile)

                render_pos = world_tile['render_pos']
                grass = [self.tiles['grass1'], self.tiles['grass2'], self.tiles['grass3']]
                self.grass_tiles.blit(random.choice(grass),
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
        if not LOAD:
            if (perlin >= 20) or (perlin <= -50):
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
                    if self.world[x][y]['tile'] == '' and self.world[nbrx][nbry]['tile'] == '':
                    # if self.world[x][y]['tile'] in ['', 'towncenter'] and \
                    #         self.world[nbrx][nbry]['tile'] in ['', 'towncenter']:
                        self.world_network.add_edge((x, y), (nbrx, nbry), weight=100)
                    elif self.world[x][y]['tile'] == 'towncenter' and self.world[nbrx][nbry]['tile'] == '':
                        self.world_network.add_edge((x, y), (nbrx, nbry), weight=1000)

    def create_road_network(self):
        self.road_network = nx.Graph()

    def update_road_network(self, pos):
        self.road_network.add_node((pos[0], pos[1]))
        nbrs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for nbr in nbrs:
            nbrx, nbry = pos[0] + nbr[0], pos[1] + nbr[1]
            if 0 <= nbrx < self.grid_length_x and 0 <= nbry < self.grid_length_y:
                if self.buildings[nbrx][nbry] is not None:
                    if self.buildings[nbrx][nbry].name == 'road':
                        self.world_network.edges[(pos, (nbrx, nbry))]['weight'] = 1
                        self.road_network.add_edge(pos, (nbrx, nbry))


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
        # self.mouse_pos = pg.mouse.get_pos()
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
            y1 = self.grid_length_y - y1 - 1
            x2, y2 = n2
            y2 = self.grid_length_y - y2 - 1

            plot([x1, x2], [y1, y2], 'k')

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
                else:
                    color = (1., 1., 1.)
                xs.append(x)
                ys.append(self.grid_length_y - 1 - y)
                colors.append(color)
        scatter(xs, ys, c=colors)

        for n1, n2 in self.road_network.edges:
            x1, y1 = n1
            y1 = self.grid_length_y - 1 - y1
            x2, y2 = n2
            y2 = self.grid_length_y - 1 - y2

            plot([x1, x2], [y1, y2], 'k')

        savefig('road_network.png')

    def write_map(self):
        f = open('map.txt', 'w')
        for x in range(self.grid_length_x):
            string = ','.join([CHARMAP[self.world[x][y]['tile']] for y in range(self.grid_length_y)])
            # string = ''
            # for y in range(self.grid_length_y):
            #     string += CHARMAP[self.world[x][y]['tile']]
            #     string += ','
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
                x, y = num1, 0
            elif not self.world[0][num2]['collision']:
                found = True
                x, y = 0, num2
        return x, y

    def dist(self, pos1, pos2):
        # get the simple hamming distance between two tiles
        return abs(pos2[0] - pos1[0]) + abs(pos2[1] - pos1[1])

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

    def get_state_for_savefile(self):
        ret = ''
        ret += f'x={self.grid_length_x}#'
        ret += f'y={self.grid_length_y}#'
        ret += f'perlin={self.perlin_scale}#'
        ret += f'villagers={','.join([w.id for w in self.entities if isinstance(w, Worker)])}#'
        ret = ret[:-1] + '\n'
        return ret