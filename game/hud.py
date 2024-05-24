import pygame as pg
import pygame.transform
from .utils import draw_text, load_images


# need to add code up here to calculate panel positions only once

class HUD:

    def __init__(self, width, height, screen):

        self.width = width
        self.height = height
        self.screen = screen
        self.parent = None
        self.panel_color = (198, 155, 93, 175)

        # resources panel
        self.create_resources_panel()
        # building panel
        self.create_building_panel()
        # select panel
        self.create_select_panel()

        self.create_current_towncenter_panel()
        self.create_activate_towncenter_button()
        self.create_deactivate_towncenter_button()

        self.images = load_images()
        self.tiles = self.populate_build_hud()

        self.structure_to_build = None
        self.selected_building = None
        self.selected_worker = None

        self.town_exists = False
        self.town_center_selected = False

        self.mouse_pos = None
        self.mouse_action = None

    def create_resources_panel(self):
        self.resources_panel = pg.Surface((self.width, self.height * .02), pg.SRCALPHA)
        self.resources_panel.fill(self.panel_color)
        self.resources_rect = self.resources_panel.get_rect(topleft=(0, 0))

    def create_building_panel(self):
        self.building_panel = pg.Surface((self.width * .15, self.height * .25), pg.SRCALPHA)
        self.building_panel.fill(self.panel_color)
        self.building_rect = self.building_panel.get_rect(topleft=(self.width * .84, self.height * .74))

    def create_select_panel(self):
        self.select_panel = pg.Surface((self.width * .3, self.height * .2), pg.SRCALPHA)
        self.select_panel.fill(self.panel_color)
        self.select_rect = self.select_panel.get_rect(topleft=(self.width * .35, self.height * .79))
        self.select_panel_visible = False

    def create_current_towncenter_panel(self):
        self.current_town_center_panel = pg.Surface((self.width * .1, self.height * .05), pg.SRCALPHA)
        self.current_town_center_panel.fill((150, 255, 0, 175))
        self.current_town_center_rect = self.current_town_center_panel.get_rect(topleft=(self.width * .85,
                                                                                         self.height * .1))

    def create_activate_towncenter_button(self):
        self.activate_town_center_button = pg.Surface((self.width * .1, self.height * .05), pg.SRCALPHA)
        self.activate_town_center_button.fill((0, 0, 200, 175))
        self.activate_town_center_rect = self.activate_town_center_button.get_rect(topleft=(self.width * .5,
                                                                                            self.height * .84))

    def create_deactivate_towncenter_button(self):
        self.deselect_town_center_button = pg.Surface((self.width * .02, self.height * .02), pg.SRCALPHA)
        self.deselect_town_center_button.fill((255, 0, 0, 175))
        self.deselect_town_center_rect = self.current_town_center_panel.get_rect(topleft=(self.width * .96,
                                                                                          self.height * .1))

    def populate_build_hud(self):
        render_pos = [self.width * .84 + 10, self.height * .74 + 10]
        surface_w = self.building_panel.get_width() // 5
        leftpos = render_pos[0]

        tiles = []
        horizontal_pos = 0

        # elements to leave out of the build panel
        skip = ['block', 'tree', 'rock', 'water', 'worker', 'grass1', 'grass2',
                'water_icon', 'wood_icon']

        for name, img in self.images.items():
            if name in skip:
                continue
            pos = render_pos.copy()
            img_scale = self.scale_image(img, w=surface_w)
            rect = img_scale.get_rect(topleft=pos)
            tiles.append({'name': name,
                          'icon': img_scale,
                          'image': self.images[name],
                          'rect': rect,
                          'affordable': True}
                         )
            horizontal_pos += 1
            if not horizontal_pos % 4:
                render_pos[0] = leftpos
                render_pos[1] += img_scale.get_height() + 10
            else:
                render_pos[0] += img_scale.get_width() + 10
        return tiles

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

    def update_build_tiles(self):
        if self.parent.active_town_center is not None:
            for tile in self.tiles:
                if self.parent.active_town_center.resourcemanager.is_affordable(tile['name']):
                    tile['affordable'] = True
                else:
                    tile['affordable'] = False
                if tile['rect'].collidepoint(self.mouse_pos) and tile['affordable']:
                    if self.mouse_action[0]:
                        self.structure_to_build = tile
                        self.parent.selected_building = None
                        self.selected_building = None
                        self.select_panel_visible = False

    def check_deselect_structure_to_build(self):
        if self.mouse_action[2]:
            self.structure_to_build = None

    def update(self):
        self.mouse_pos = pg.mouse.get_pos()
        self.mouse_action = pg.mouse.get_pressed()

        # check if user wants to unselect a structure they were going to build
        self.check_deselect_structure_to_build()
        # check to see if the user selected the current town center
        self.check_activate_towncenter()
        # check to see if the user wants to deselect the current town center
        self.check_deselect_towncenter()
        # only update build tiles based on affordability if a town center is active
        self.update_build_tiles()

    def draw_selected_building_image(self):
        w, h = self.select_rect.width, self.select_rect.height
        self.screen.blit(self.select_panel, (self.width * .35, self.height * .79))
        # img = self.images[self.selected_building['tile']].copy()
        img = self.selected_building.image
        img_scale = self.scale_image(img, h=h * .75)
        self.screen.blit(img_scale, (self.width * .35 + 10,
                                     self.height * .79 + 40))
        draw_text(self.screen, self.selected_building.name, 40, (255, 255, 255),
                  self.select_rect.topleft)

    def draw_selected_building_employment(self):
        x = self.width * .5
        y = self.height * .84
        draw_text(self.screen,
                  f'Workers: {len(self.selected_building.workers)} / {self.selected_building.workers_needed}',
                  20, (255, 255, 255), (x, y))

    def draw_selected_building_storage(self):
        x = self.width * .5
        y = self.height * .84 + 25
        for item in self.selected_building.storage:
            color = (255, 255, 255) if not self.selected_building.is_full() else (255, 0, 0)
            draw_text(self.screen,
                      f'{item}: {self.selected_building.storage[item]} / {self.selected_building.capacity}',
                      20, color, (x, y))
            y += 25

    def check_towncenter_inactive(self):
        return self.parent.active_town_center is None or self.selected_building is not self.parent.active_town_center

    def draw_activate_towncenter_button(self):
        self.screen.blit(self.activate_town_center_button, (self.width * .5, self.height * .84))
        draw_text(self.screen, 'Select', 30, (255, 255, 255),
                  self.activate_town_center_rect.topleft)

    def draw_town_occupancy(self):
        x = self.width * .5
        y = self.height * .84
        draw_text(self.screen,
                  f'Villagers: {len(self.selected_building.villagers)} / {self.selected_building.housing_capacity}',
                  20, (255, 255, 255), (x, y)
                  )

    def draw_town_building_counts(self):
        x = self.width * .5
        y = self.height * .84 + 25
        for name, count in self.parent.active_town_center.num_buildings.items():
            draw_text(self.screen, f'{name}: {count}', 20, (255, 255, 255), (x, y))
            y += 25

    def draw_select_panel(self):
        # select hud
        if self.select_panel_visible:

            # if a building is selected, draw it on the panel
            if self.selected_building is not None:
                self.draw_selected_building_image()

                # draw employment and resources for production buildings
                if self.selected_building.name != 'towncenter':
                    self.draw_selected_building_employment()
                    self.draw_selected_building_storage()

                # if a town center is selected and the World doesn't currently have an active one,
                # draw a button for making it the active town center
                else:
                    if self.check_towncenter_inactive():
                        self.draw_activate_towncenter_button()
                    else:
                        self.draw_town_occupancy()
                        self.draw_town_building_counts()

            elif self.selected_worker is not None:
                w, h = self.select_rect.width, self.select_rect.height
                self.screen.blit(self.select_panel, (self.width * .35, self.height * .79))
                img = self.selected_worker.image
                img_scale = self.scale_image(img, h=h * .75)
                self.screen.blit(img_scale, (self.width * .35 + 10,
                                        self.height * .79 + 40))
                draw_text(self.screen, self.selected_worker.occupation, 40, (255, 255, 255),
                          self.select_rect.topleft)

                x = self.width * .5
                y = self.height * .84
                draw_text(self.screen, 'Inventory', 20, (255, 255, 255), (x, y))
                x += 10
                for name, count in self.selected_worker.inventory.items():
                    y += 20
                    draw_text(self.screen, f'{name}: {count}', 20, (255, 255, 255), (x, y))

    def draw(self):

        self.draw_select_panel()

        # draw active town center panel and deselect button
        if self.parent.active_town_center is not None:
            self.screen.blit(self.current_town_center_panel, (self.width * .85, self.height * .1))
            draw_text(self.screen, self.parent.active_town_center.name, 30, (0, 0, 0),
                      self.current_town_center_rect.topleft)
            self.screen.blit(self.deselect_town_center_button, (self.width * .96, self.height * .1))
            draw_text(self.screen, 'X', 20, (0, 0, 0), self.deselect_town_center_rect.topleft)

        # only draw build tiles when a town center is active
        if self.parent.active_town_center is not None:
            self.screen.blit(self.building_panel, (self.width * .84, self.height * .74))
            for tile in self.tiles:
                # require town center before building other things
                if not self.town_exists:
                    if tile['name'] == 'towncenter':
                        self.screen.blit(tile['icon'], tile['rect'].topleft)
                    else:
                        icon = tile['icon'].copy()
                        icon.set_alpha(100)
                        self.screen.blit(icon, tile['rect'].topleft)
                    continue
                elif not tile['affordable']:
                    icon = tile['icon'].copy()
                    icon.set_alpha(100)
                    self.screen.blit(icon, tile['rect'].topleft)

                    # this section is to make sure that you cannot place another copy of a building when you
                    # run out of resources
                    # when you run out, it does take the building away from your cursor, but it selects the last one
                    # you built
                    if self.structure_to_build is not None:
                        if self.structure_to_build['name'] == tile['name']:
                            self.structure_to_build = None
                else:
                    self.screen.blit(tile['icon'], tile['rect'].topleft)

        self.screen.blit(self.resources_panel, (0, 0))

        # draw resource amounts at top of screen
        if self.parent.active_town_center is not None:
            pos = self.width - 720
            for resource, value in self.parent.active_town_center.resourcemanager.resources.items():
                text = f'{resource}: {value}'
                draw_text(self.screen, text, 30, (0, 0, 0), (pos, 0))
                pos += 120

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
