import pygame as pg
import pygame.transform
from .utils import draw_text, load_images


BLDG = ['towncenter', 'well', 'chopping', 'quarry', 'wheatfield',
        'house', 'road', 'workbench', 'market']
TECH = ['simpletools_tech', 'agriculture']
RSRC = ['wood', 'stone', 'water', 'wheat', 'simpletools']

class HUD:

    def __init__(self, width, height, screen):

        self.width = width
        self.height = height
        self.screen = screen
        self.parent = None
        self.panel_color = (198, 155, 93, 175)

        self.panel_positions = {}
        self.panel_dimensions = {}
        self.get_panel_positions_and_dimensions()

        self.images = load_images()

        # resources panel
        self.create_resources_panel()
        # building panel
        self.create_town_actions_panel()

        self.create_building_panel()
        self.create_tech_panel()
        self.create_buildmode_button()
        self.create_techmode_button()
        self.context_display = 'building'
        # select panel
        self.create_select_panel()

        self.create_current_towncenter_panel()
        self.create_activate_towncenter_button()
        self.create_deactivate_towncenter_button()

        # self.tiles = self.populate_build_hud()
        self.build_tiles = self.get_buildtile_dict()
        self.tech_tiles = self.get_techtile_dict()
        self.resource_tiles = self.get_resources_tiledict()

        self.structure_to_build = None
        self.selected_building = None
        self.selected_worker = None
        self.town_center_selected = False

        self.mouse_pos = None
        self.mouse_action = None

    def get_panel_positions_and_dimensions(self):
        self.panel_positions = {'resources_panel': (0, 0),
                                # 'select_panel': (self.width * .35, self.height * .79)}
                                'select_panel': (self.width * .01, self.height * .03)}
        self.panel_dimensions = {'resources_panel': (self.width, self.height * .02),
                                 # 'select_panel': (self.width * .2, self.height * .2),
                                 'select_panel': (self.width * .2, self.height * .96),
                                 'activate_town_center_button': (self.width * .07, self.height * .05)}
        self.panel_positions['activate_town_center_button'] = (self.panel_positions['select_panel'][0] + .5 * self.panel_dimensions['select_panel'][0],
                                                               self.panel_positions['select_panel'][1] + .05 * self.panel_dimensions['select_panel'][1])
        self.panel_positions['selected_building'] = (self.panel_positions['select_panel'][0] + .02 * self.panel_dimensions['select_panel'][0],
                                                     self.panel_positions['select_panel'][1] + .03 * self.panel_dimensions['select_panel'][1])

        self.panel_dimensions['town_actions_panel'] = (.98 * self.panel_dimensions['select_panel'][0],
                                                       .43 * self.panel_dimensions['select_panel'][1])
        self.panel_positions['town_actions_panel'] = (self.panel_positions['select_panel'][0] + .01 * self.panel_dimensions['select_panel'][0],
                                                      self.panel_positions['select_panel'][1] + .56 * self.panel_dimensions['select_panel'][1])

        self.panel_dimensions['buildmode_button'] = (.48 * self.panel_dimensions['town_actions_panel'][0],
                                                     .05 * self.panel_dimensions['town_actions_panel'][1])
        self.panel_dimensions['techmode_button'] = (.48 * self.panel_dimensions['town_actions_panel'][0],
                                                     .05 * self.panel_dimensions['town_actions_panel'][1])
        self.panel_positions['buildmode_button'] = (self.panel_positions['town_actions_panel'][0] + .01 * self.panel_dimensions['town_actions_panel'][0],
                                                    self.panel_positions['town_actions_panel'][1] + .01 * self.panel_dimensions['town_actions_panel'][1])
        self.panel_positions['techmode_button'] = (self.panel_positions['town_actions_panel'][0] + .51 * self.panel_dimensions['town_actions_panel'][0],
                                                   self.panel_positions['town_actions_panel'][1] + .01 * self.panel_dimensions['town_actions_panel'][1])

        self.panel_dimensions['building_panel'] = (.98 * self.panel_dimensions['town_actions_panel'][0],
                                                   .75 * self.panel_dimensions['town_actions_panel'][1])
        self.panel_positions['building_panel'] = (self.panel_positions['town_actions_panel'][0] + .01 * self.panel_dimensions['town_actions_panel'][0],
                                                  self.panel_positions['town_actions_panel'][1] + .06 * self.panel_dimensions['town_actions_panel'][1])
        self.panel_dimensions['tech_panel'] = (.98 * self.panel_dimensions['town_actions_panel'][0],
                                               .75 * self.panel_dimensions['town_actions_panel'][1])
        self.panel_positions['tech_panel'] = (self.panel_positions['town_actions_panel'][0] + .01 * self.panel_dimensions['town_actions_panel'][0],
                                              self.panel_positions['town_actions_panel'][1] + .06 * self.panel_dimensions['town_actions_panel'][1])

        for i in range(1, 10):
            self.panel_positions[f'selected_text_{i}'] = (self.panel_positions['select_panel'][0] + .4 * self.panel_dimensions['select_panel'][0],
                                                          self.panel_positions['select_panel'][1] + .03 * self.panel_dimensions['select_panel'][1] + (.02 * i) * self.panel_dimensions['select_panel'][1])

    def create_resources_panel(self):
        self.resources_panel = pg.Surface(self.panel_dimensions['resources_panel'], pg.SRCALPHA)
        self.resources_panel.fill(self.panel_color)
        self.resources_rect = self.resources_panel.get_rect(topleft=self.panel_positions['resources_panel'])

    def create_building_panel(self):
        self.building_panel = pg.Surface(self.panel_dimensions['building_panel'], pg.SRCALPHA)
        self.building_panel.fill((155, 200, 100, 175))
        self.building_rect = self.building_panel.get_rect(topleft=self.panel_positions['building_panel'])

    def create_tech_panel(self):
        self.tech_panel = pg.Surface(self.panel_dimensions['tech_panel'], pg.SRCALPHA)
        self.tech_panel.fill((200, 100, 100, 175))
        self.tech_rect = self.tech_panel.get_rect(topleft=self.panel_positions['tech_panel'])

    def create_select_panel(self):
        self.select_panel = pg.Surface(self.panel_dimensions['select_panel'], pg.SRCALPHA)
        self.select_panel.fill(self.panel_color)
        self.select_rect = self.select_panel.get_rect(topleft=self.panel_positions['select_panel'])
        self.select_panel_visible = False

    def create_town_actions_panel(self):
        self.town_actions_panel = pg.Surface(self.panel_dimensions['town_actions_panel'], pg.SRCALPHA)
        self.town_actions_panel.fill((155, 155, 155, 155))
        self.town_actions_rect = self.town_actions_panel.get_rect(topleft=self.panel_positions['town_actions_panel'])

    def create_buildmode_button(self):
        self.buildmode_button = pg.Surface(self.panel_dimensions['buildmode_button'], pg.SRCALPHA)
        self.buildmode_button.fill((155, 200, 100, 175))
        self.buildmode_button_rect = self.buildmode_button.get_rect(topleft=self.panel_positions['buildmode_button'])

    def create_techmode_button(self):
        self.techmode_button = pg.Surface(self.panel_dimensions['techmode_button'], pg.SRCALPHA)
        self.techmode_button.fill((200, 100, 100, 175))
        self.techmode_button_rect = self.techmode_button.get_rect(topleft=self.panel_positions['techmode_button'])

    def create_current_towncenter_panel(self):
        self.current_town_center_panel = pg.Surface((self.width * .075, self.height * .04), pg.SRCALPHA)
        self.current_town_center_panel.fill((150, 255, 0, 175))
        self.current_town_center_rect = self.current_town_center_panel.get_rect(topleft=(self.width * .87,
                                                                                         self.height * .075))

    def create_activate_towncenter_button(self):
        self.activate_town_center_button = pg.Surface(self.panel_dimensions['activate_town_center_button'], pg.SRCALPHA)
        self.activate_town_center_button.fill((0, 0, 200, 175))
        self.activate_town_center_rect = self.activate_town_center_button.get_rect(topleft=self.panel_positions['activate_town_center_button'])

    def create_deactivate_towncenter_button(self):
        self.deselect_town_center_button = self.images['deselect_button']
        self.deselect_town_center_rect = self.deselect_town_center_button.get_rect(topleft=(self.width * .96,
                                                                                            self.height * .075))

    def get_buildtile_dict(self):
        render_pos = list(self.panel_positions['building_panel'])
        render_pos[0] += .05 * self.panel_dimensions['building_panel'][0]
        render_pos[1] += .05 * self.panel_dimensions['building_panel'][1]
        surface_w = self.building_panel.get_width() // 5
        leftpos = render_pos[0]
        horizontalpos = 0
        tiles = {}

        i = 0
        for name in BLDG:
            pos = render_pos.copy()
            img = self.images[name]
            img_scale = self.scale_image(img, w=surface_w)
            rect = img_scale.get_rect(topleft=pos)
            tiles[i] = {'name': name,
                        'icon': img_scale,
                        'image': self.images[name],
                        'rect': rect,
                        'affordable': True,
                        'unlocked': False}
            horizontalpos += 1
            if not horizontalpos % 4:
                render_pos[0] = leftpos
                render_pos[1] += img_scale.get_height() + 10
            else:
                render_pos[0] += surface_w + 10
            i += 1

        return tiles

    def get_techtile_dict(self):
        render_pos = list(self.panel_positions['building_panel'])
        render_pos[0] += .05 * self.panel_dimensions['building_panel'][0]
        render_pos[1] += .05 * self.panel_dimensions['building_panel'][1]
        surface_w = self.building_panel.get_width() // 5
        leftpos = render_pos[0]
        horizontalpos = 0
        tiles = {}

        i = 0
        for name in TECH:
            pos = render_pos.copy()
            img = self.images[name]
            img_scale = self.scale_image(img, w=surface_w)
            rect = img_scale.get_rect(topleft=pos)
            tiles[i] = {'name': name,
                        'icon': img_scale,
                        'image': self.images[name],
                        'rect': rect,
                        'affordable': True,
                        'unlocked': False}
            horizontalpos += 1
            if not horizontalpos % 4:
                render_pos[0] = leftpos
                render_pos[1] += img_scale.get_height() + 10
            else:
                render_pos[0] += surface_w + 10
            i += 1

        return tiles

    def get_resources_tiledict(self):
        render_pos = list(self.panel_positions['select_panel'])
        render_pos[0] += .05 * self.panel_dimensions['select_panel'][0]
        render_pos[1] += .15 * self.panel_dimensions['select_panel'][1]
        surface_w = self.select_panel.get_width() // 10
        leftpos = render_pos[0]
        horizontalpos = 0
        tiles = {}

        for name in RSRC:
            pos = render_pos.copy()
            img = self.images[name]
            img_scale = self.scale_image(img, w=surface_w)
            rect = img_scale.get_rect(topleft=pos)
            tiles[name] = {'name': name,
                           'icon': img_scale,
                           'image': self.images[name],
                           'rect': rect,
                           'affordable': True,
                           'unlocked': False,
                           'textpos': [render_pos[0] + 1.1 * surface_w, render_pos[1]]}
            horizontalpos += 1
            if not horizontalpos % 3:
                render_pos[0] = leftpos
                render_pos[1] += img_scale.get_height() + 10
            else:
                render_pos[0] += 3 * surface_w

        return tiles

        # for i in range(4):
        #     for j in range(4):
        #         pos = render_pos.copy()
        #         img = pg.Surface((surface_w, surface_h), pg.SRCALPHA)
        #         img.fill((0, 0, 0))
        #         rect = img.get_rect(topleft=pos)
        #         tiles[(i, j)] = {'name': '',
        #                       'icon': img,
        #                       'image': img,
        #                       'rect': rect,
        #                       'affordable': True,
        #                       'unlocked': False}
        #         horizontalpos += 1
        #         if not horizontalpos % 4:
        #             render_pos[0] = leftpos
        #             render_pos[1] += surface_h + 10
        #         else:
        #             render_pos[0] += surface_w + 10
        # return tiles

    def check_activate_towncenter(self):
        if self.selected_building is not None:
            if self.selected_building.name == 'towncenter':
                if self.activate_town_center_rect.collidepoint(self.mouse_pos):
                    if self.mouse_action[0]:
                        self.parent.active_town_center = self.selected_building

    def check_deselect_towncenter(self):
        if self.parent.active_town_center is not None:
            if self.deselect_town_center_rect.collidepoint(self.mouse_pos):
                if self.mouse_action[0]:
                    self.parent.active_town_center = None
                    self.structure_to_build = None

    def check_context_display_mode(self):
        if self.parent.active_town_center is not None:
            if self.buildmode_button_rect.collidepoint(self.mouse_pos):
                if self.mouse_action[0]:
                    self.context_display = 'building'
            if self.techmode_button_rect.collidepoint(self.mouse_pos):
                if self.mouse_action[0]:
                    self.context_display = 'tech'

    def check_deselect_structure_to_build(self):
        if self.mouse_action[2]:
            self.structure_to_build = None

    def check_towncenter_inactive(self):
        return self.parent.active_town_center is None or self.selected_building is not self.parent.active_town_center

    def check_structure_to_build_affordable(self, name):
        if self.structure_to_build is not None:
            if self.structure_to_build['name'] == name:
                self.structure_to_build = None

    def update_build_tiles(self):
        if self.parent.active_town_center is not None:
            for key in self.build_tiles:
                tile = self.build_tiles[key]
                if self.parent.active_town_center.resourcemanager.is_affordable(tile['name']):
                    tile['affordable'] = True
                else:
                    tile['affordable'] = False
                if self.parent.active_town_center.techmanager.building_unlock_status[tile['name']]:
                    tile['unlocked'] = True
                if self.context_display == 'building':
                    if tile['rect'].collidepoint(self.mouse_pos) and tile['affordable'] and tile['unlocked']:
                        if self.mouse_action[0]:
                            self.structure_to_build = tile
                            self.parent.selected_building = None
                            self.selected_building = None
                            self.select_panel_visible = False

    def update_tech_tiles(self):
        if self.parent.active_town_center is not None:
            for key in self.tech_tiles:
                tile = self.tech_tiles[key]
                if self.parent.active_town_center.techmanager.tech_unlock_status[tile['name']]:
                    tile['unlocked'] = True
                else:
                    tile['unlocked'] = False
                if self.parent.active_town_center.resourcemanager.is_affordable(tile['name']):
                    tile['affordable'] = True
                else:
                    tile['affordable'] = False

                if self.context_display == 'tech':
                    if tile['rect'].collidepoint(self.mouse_pos) and tile['affordable'] and tile['unlocked']:
                        if self.mouse_action[0]:
                            self.parent.active_town_center.resourcemanager.apply_cost(tile['name'])
                            self.parent.active_town_center.techmanager.start_research(tile['name'])

    def update(self):
        self.mouse_pos = pg.mouse.get_pos()
        self.mouse_action = pg.mouse.get_pressed()

        if self.selected_worker is not None:
            if self.selected_worker.arrived_at_home or self.selected_worker.arrived_at_work:
                self.parent.deselect_all()

        # check if user wants to unselect a structure they were going to build
        self.check_deselect_structure_to_build()
        # check to see if the user activated the current town center
        self.check_activate_towncenter()
        # check to see if the user wants to deselect the current town center
        self.check_deselect_towncenter()
        # check to see if the user wants to switch the context menu
        self.check_context_display_mode()
        # only update build tiles based on affordability if a town center is active

        self.update_build_tiles()
        self.update_tech_tiles()

    def draw_selected_building_image(self):
        w, h = self.select_rect.width, self.select_rect.height
        img_scale = self.scale_image(self.selected_building.image, h=h * .1)
        self.screen.blit(img_scale, self.panel_positions['selected_building'])
        draw_text(self.screen, self.selected_building.name, 40, (255, 255, 255),
                  [i + 5 for i in self.select_rect.topleft])

    def draw_selected_building_employment(self):
        draw_text(self.screen,
                  f'Workers: {len(self.selected_building.workers)} / {self.selected_building.workers_needed}',
                  20, (255, 255, 255), self.panel_positions[f'selected_text_1'])
        draw_text(self.screen,
                  f'Workers in building: {self.selected_building.check_currently_in_building()} / {self.selected_building.workers_needed}',
                  20, (255, 255, 255), self.panel_positions[f'selected_text_2'])

    def draw_selected_building_storage(self):
        i = 3
        for item in self.selected_building.storage:
            color = (255, 255, 255) if not self.selected_building.is_full() else (255, 0, 0)
            draw_text(self.screen,
                      f'{item}: {self.selected_building.storage[item]} / {self.selected_building.capacity}',
                      20, color, self.panel_positions[f'selected_text_{i}'])
            i += 1

    def draw_activate_towncenter_button(self):
        self.screen.blit(self.activate_town_center_button, self.panel_positions['activate_town_center_button'])
        draw_text(self.screen, 'Select', 30, (255, 255, 255),
                  self.activate_town_center_rect.topleft)

    def draw_buildmode_button(self):
        self.screen.blit(self.buildmode_button, self.panel_positions['buildmode_button'])
        draw_text(self.screen, 'Build', 30, (255, 255, 255),
                  self.buildmode_button_rect.topleft)

    def draw_techmode_button(self):
        self.screen.blit(self.techmode_button, self.panel_positions['techmode_button'])
        draw_text(self.screen, 'Tech', 30, (255, 255, 255),
                  self.techmode_button_rect.topleft)

    def draw_activate_towncenter_button(self):
        self.screen.blit(self.activate_town_center_button, self.panel_positions['activate_town_center_button'])
        draw_text(self.screen, 'Select', 30, (255, 255, 255),
                  self.activate_town_center_rect.topleft)

    def draw_town_occupancy(self):

        draw_text(self.screen,
                  f'Villagers: {self.selected_building.num_villagers} / {self.selected_building.housing_capacity}',
                  20, (255, 255, 255), self.panel_positions['selected_text_1'])

    def draw_town_building_counts(self):
        i = 2
        for tech, progress in self.parent.active_town_center.techmanager.current_research.items():
            draw_text(self.screen, f'{tech}: {progress}', 20, (255, 255, 255), self.panel_positions[f'selected_text_{i}'])
        # for name, count in self.parent.active_town_center.num_buildings.items():
        #     draw_text(self.screen, f'{name}: {count}', 20, (255, 255, 255), self.panel_positions[f'selected_text_{i}'])
            i += 1
        for tech in self.parent.active_town_center.techmanager.technologies:
            draw_text(self.screen, f'{tech}', 20, (255, 255, 255),
                      self.panel_positions[f'selected_text_{i}'])
            i += 1

    def draw_selected_worker_image(self):
        w, h = self.select_rect.width, self.select_rect.height
        img_scale = self.scale_image(self.selected_worker.image, h=h * .1)
        self.screen.blit(img_scale, self.panel_positions[f'selected_building'])
        draw_text(self.screen, self.selected_worker.occupation, 40, (255, 255, 255),
                  [i + 5 for i in self.select_rect.topleft])

        self.draw_selected_worker_inventory()

    def draw_selected_worker_inventory(self):
        draw_text(self.screen, f'Energy: {self.selected_worker.energy} / 100', 20,
                  (255, 255, 255), self.panel_positions[f'selected_text_1'])
        draw_text(self.screen, 'Inventory', 20, (255, 255, 255), self.panel_positions[f'selected_text_2'])
        draw_text(self.screen, f'Gold: {self.selected_worker.gold}', 20, (255, 255, 255), self.panel_positions[f'selected_text_3'])
        i = 4
        for name, count in self.selected_worker.inventory.items():
            draw_text(self.screen, f'{name}: {count}', 20, (255, 255, 255), self.panel_positions[f'selected_text_{i}'])
            i += 1
        # current_task = 'Wandering'
        # if self.selected_worker.going_to_work:
        #     current_task = 'Going to work'
        #     if self.selected_worker.collected_for_work:
        #         current_task += ' with supplies'
        # if self.selected_worker.going_home:
        #     current_task = 'Going home'
        #     if sum(self.selected_worker.inventory.values()) > 0:
        #         current_task += ' with goods'
        # if self.selected_worker.going_to_towncenter:
        #     current_task = 'Going to town center'
        #     if sum(self.selected_worker.inventory.values()) > 0:
        #         current_task += ' with goods'
        # if self.selected_worker.arrived_at_work:
        #     current_task = 'Working'
        # if self.selected_worker.arrived_at_home:
        #     current_task = 'Resting'
        # if self.selected_worker.arrived_at_towncenter:
        #     current_task = 'Trading'
        # draw_text(self.screen, f'{current_task}', 20, (255, 255, 255), self.panel_positions[f'selected_text_{i}'])

    def draw_selected_building_occupancy(self):
        draw_text(self.screen,
                  f'Occupants: {self.selected_building.num_occupants} / {self.selected_building.housing_capacity}',
                  20, (255, 255, 255), self.panel_positions[f'selected_text_1']
                  )
        draw_text(self.screen,
                  f'Occupants in building: {self.selected_building.check_currently_in_building()} / {self.selected_building.housing_capacity}',
                  20, (255, 255, 255), self.panel_positions[f'selected_text_2'])

    def draw_selected_building_needs(self):
        i = 3
        for name in self.selected_building.needs:
            draw_text(self.screen, f'{name}: {self.selected_building.storage[name]} / {self.selected_building.needs[name]}',
                      20, (255, 255, 255), self.panel_positions[f'selected_text_{i}'])
            i += 1

    def draw_select_panel(self):
        # select hud
        if self.select_panel_visible:

            self.screen.blit(self.select_panel, self.panel_positions['select_panel'])

            # if a building is selected, draw it on the panel
            if self.selected_building is not None:
                self.draw_selected_building_image()

                # draw employment and resources for production buildings
                if self.selected_building.name != 'towncenter':
                    if self.selected_building.name == 'house':
                        self.draw_selected_building_occupancy()
                        self.draw_selected_building_needs()
                    else:
                        self.draw_selected_building_employment()
                        self.draw_selected_building_storage()

                # if a town center is selected and the World doesn't currently have an active one,
                # draw a button for making it the active town center
                else:
                    if not self.check_towncenter_inactive():
                        self.draw_town_occupancy()
                        self.draw_town_building_counts()
                    else:
                        self.draw_activate_towncenter_button()

            elif self.selected_worker is not None:
                self.draw_selected_worker_image()
                self.draw_selected_worker_inventory()

    def draw_active_town_center_title(self):
        self.screen.blit(self.current_town_center_panel, (self.width * .87, self.height * .075))
        draw_text(self.screen, self.parent.active_town_center.name, 30, (0, 0, 0),
                  self.current_town_center_rect.topleft)

    def draw_deselect_towncenter_button(self):
        self.screen.blit(self.deselect_town_center_button, (self.width * .96, self.height * .075))

    def draw_building_panel(self):
        self.screen.blit(self.building_panel, self.panel_positions['building_panel'])
        self.draw_building_panel_tiles()

    def draw_tech_panel(self):
        self.screen.blit(self.tech_panel, self.panel_positions['tech_panel'])
        self.draw_tech_panel_tiles()

    def draw_tech_panel_tiles(self):
        for key in self.tech_tiles:

            tile = self.tech_tiles[key]

            # darken the current tile if it isn't affordable
            if not tile['affordable'] or not tile['unlocked']:
                icon = tile['icon'].copy()
                icon.set_alpha(100)
                self.screen.blit(icon, tile['rect'].topleft)

            # place the tile for an affordable building
            else:
                self.screen.blit(tile['icon'], tile['rect'].topleft)

    def draw_building_panel_tiles(self):
        for key in self.build_tiles:

            tile = self.build_tiles[key]

            # darken the current tile if it isn't affordable
            if not tile['affordable'] or not tile['unlocked']:
                icon = tile['icon'].copy()
                icon.set_alpha(100)
                self.screen.blit(icon, tile['rect'].topleft)

                # this section is to make sure that you cannot place another copy of a building when you
                # run out of resources
                # when you run out, it does take the building away from your cursor, but it selects the last one
                # you built

                self.check_structure_to_build_affordable(tile['name'])

            # place the tile for an affordable building
            else:
                self.screen.blit(tile['icon'], tile['rect'].topleft)

            if tile['name'] in self.parent.active_town_center.num_buildings:
                draw_text(self.screen, str(self.parent.active_town_center.num_buildings[tile['name']]),
                          25, (0, 0, 0), tile['rect'].topleft)

    def draw_resource_panel_tiles(self):
        if self.selected_building is not None:
            if self.parent.active_town_center is self.selected_building:
                for key in self.resource_tiles:
                    tile = self.resource_tiles[key]
                    self.screen.blit(tile['icon'], tile['rect'].topleft)
                    draw_text(self.screen, f'{self.parent.active_town_center.resourcemanager.resources[key]}',
                              20, (255, 255, 255), tile['textpos'])
            else:
                for key in self.resource_tiles:
                    if key in self.selected_building.storage:
                        tile = self.resource_tiles[key]
                        self.screen.blit(tile['icon'], tile['rect'].topleft)
                        draw_text(self.screen, f'{self.selected_building.storage[key]}',
                                  20, (255, 255, 255), tile['textpos'])
        if self.selected_worker is not None:
            for key in self.resource_tiles:
                if key not in self.selected_worker.inventory:
                    continue
                if self.selected_worker.inventory[key] > 0:
                    tile = self.resource_tiles[key]
                    self.screen.blit(tile['icon'], tile['rect'].topleft)
                    draw_text(self.screen, f'{self.selected_worker.inventory[key]}',
                              20, (255, 255, 255), tile['textpos'])

    def draw(self):

        self.draw_select_panel()

        # draw active town center panel and deselect button
        if self.parent.active_town_center is not None:
            self.draw_active_town_center_title()
            self.draw_deselect_towncenter_button()
            self.draw_resource_panel_tiles()
            self.screen.blit(self.town_actions_panel, self.panel_positions['town_actions_panel'])
            self.draw_buildmode_button()
            self.draw_techmode_button()
            if self.context_display == 'building':
                self.draw_building_panel()
            elif self.context_display == 'tech':
                self.draw_tech_panel()

        self.screen.blit(self.resources_panel, (0, 0))

        # draw resource amounts at top of screen
        if self.parent.active_town_center is not None:
            pos = self.width * .85
            # for resource, value in self.parent.active_town_center.resourcemanager.resources.items():
            text = f'Gold: {self.parent.active_town_center.resourcemanager.resources['gold']}'
            draw_text(self.screen, text, 30, (0, 0, 0), (pos, 0))
            # pos += 120

    def scale_image(self, image, w=None, h=None):
        if w is None and h is None:
            pass
        elif h is None:
            scale = w / image.get_width()
            h = scale * image.get_height()
            image = pygame.transform.scale(image, (int(w), int(h)))
        elif w is None:
            scale = h / image.get_height()
            w = scale * image.get_width()
            image = pygame.transform.scale(image, (int(w), int(h)))
        else:
            image = pygame.transform.scale(image, (int(w), int(h)))

        return image
