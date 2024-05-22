import pygame as pg
import pygame.transform
from .utils import draw_text, load_images

class HUD:

    def __init__(self, width, height):

        self.width = width
        self.height = height

        self.parent = None

        self.panel_color = (198, 155, 93, 175)

        # resources panel
        self.resources_panel = pg.Surface((self.width, self.height * .02), pg.SRCALPHA)
        self.resources_panel.fill(self.panel_color)
        self.resources_rect = self.resources_panel.get_rect(topleft=(0, 0))

        # building panel
        self.building_panel = pg.Surface((self.width * .15, self.height * .25), pg.SRCALPHA)
        self.building_panel.fill(self.panel_color)
        self.building_rect = self.building_panel.get_rect(topleft=(self.width * .84, self.height * .74))

        # select panel
        self.select_panel = pg.Surface((self.width * .3, self.height * .2), pg.SRCALPHA)
        self.select_panel.fill(self.panel_color)
        self.select_rect = self.select_panel.get_rect(topleft=(self.width * .35, self.height * .79))
        self.select_panel_visible = False

        self.activate_town_center_button = pg.Surface((self.width * .1, self.height * .05), pg.SRCALPHA)
        self.activate_town_center_button.fill((0, 0, 200, 175))
        self.activate_town_center_rect = self.activate_town_center_button.get_rect(topleft=(self.width * .5,
                                                                                            self.height * .84))

        self.current_town_center_panel = pg.Surface((self.width * .1, self.height * .05), pg.SRCALPHA)
        self.current_town_center_panel.fill((150, 255, 0, 175))
        self.current_town_center_rect = self.current_town_center_panel.get_rect(topleft=(self.width * .85,
                                                                                         self.height * .1))

        self.deselect_town_center_button = pg.Surface((self.width * .02, self.height * .02), pg.SRCALPHA)
        self.deselect_town_center_button.fill((255, 0, 0, 175))
        self.deselect_town_center_rect = self.current_town_center_panel.get_rect(topleft=(self.width * .96,
                                                                                          self.height * .1))

        self.images = load_images()
        self.tiles = self.populate_build_hud()

        self.selected_tile = None
        self.examined_tile = None

        self.town_exists = False
        self.town_center_selected = False

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

    def update(self):
        mouse_pos = pg.mouse.get_pos()
        mouse_action = pg.mouse.get_pressed()

        if mouse_action[2]:
            self.selected_tile = None

        # check to see if the user selected the current town center
        if self.examined_tile is not None:
            if self.examined_tile.name == 'towncenter':
                if self.activate_town_center_rect.collidepoint(mouse_pos):
                    if mouse_action[0]:
                        self.parent.active_town_center = self.examined_tile

        # check to see if the user wants to deselect the current town center
        if self.parent.active_town_center is not None:
            if self.deselect_town_center_rect.collidepoint(mouse_pos):
                if mouse_action[0]:
                    self.parent.active_town_center = None
                    self.selected_tile = None

        # only update build tiles based on affordability if a town center is active
        if self.parent.active_town_center is not None:
            for tile in self.tiles:
                if self.parent.active_town_center.resourcemanager.is_affordable(tile['name']):
                    tile['affordable'] = True
                else:
                    tile['affordable'] = False
                if tile['rect'].collidepoint(mouse_pos) and tile['affordable']:
                    if mouse_action[0]:
                        self.selected_tile = tile
                        self.parent.examine_tile = None
                        self.examined_tile = None
                        self.select_panel_visible = False

    def draw(self, screen):

        # if there is a building selected for placement, draw it by the mouse
        if self.selected_tile is not None:
            img = self.selected_tile['image'].copy()
            img.set_alpha(100)

        # select hud
        if self.examined_tile is not None:
            w, h = self.select_rect.width, self.select_rect.height
            screen.blit(self.select_panel, (self.width * .35, self.height * .79))
            # img = self.images[self.examined_tile['tile']].copy()
            img = self.examined_tile.image
            img_scale = self.scale_image(img, h=h*.75)
            screen.blit(img_scale, (self.width * .35 + 10,
                                    self.height * .79 + 40))
            draw_text(screen, self.examined_tile.name, 40, (255, 255, 255),
                      self.select_rect.topleft)

            if self.examined_tile.name != 'towncenter':
                x = self.width * .5
                y = self.height * .84
                draw_text(screen, f'Workers: {len(self.examined_tile.workers)} / {self.examined_tile.workers_needed}',
                          20, (255, 255, 255), (x, y))

            # if a town center is selected and the World doesn't currently have an active one,
            # draw a button for making it the active town center
            elif self.examined_tile.name == 'towncenter' and (self.parent.active_town_center is None or
                                                            self.examined_tile is not self.parent.active_town_center):
                screen.blit(self.activate_town_center_button, (self.width * .5, self.height * .84))
                draw_text(screen, 'Select', 30, (255, 255, 255),
                          self.activate_town_center_rect.topleft)
            elif (self.examined_tile.name == 'towncenter') and (self.examined_tile is self.parent.active_town_center):
                x = self.width * .5
                y = self.height * .84
                draw_text(screen,
                          f'Villagers: {len(self.examined_tile.villagers)} / {self.examined_tile.housing_capacity}',
                          20, (255, 255, 255), (x, y)
                          )
                y += 20
                for name, count in self.parent.active_town_center.num_buildings.items():
                    draw_text(screen, f'{name}: {count}', 20, (255, 255, 255), (x, y))
                    y += 20

        # draw active town center panel and deselect button
        if self.parent.active_town_center is not None:
            screen.blit(self.current_town_center_panel, (self.width * .85, self.height * .1))
            draw_text(screen, self.parent.active_town_center.name, 30, (0, 0, 0),
                      self.current_town_center_rect.topleft)
            screen.blit(self.deselect_town_center_button, (self.width * .96, self.height * .1))
            draw_text(screen, 'X', 20, (0, 0, 0), self.deselect_town_center_rect.topleft)

        # only draw build tiles when a town center is active
        if self.parent.active_town_center is not None:
            screen.blit(self.building_panel, (self.width * .84, self.height * .74))
            for tile in self.tiles:
                # require town center before building other things
                if not self.town_exists:
                    if tile['name'] == 'towncenter':
                        screen.blit(tile['icon'], tile['rect'].topleft)
                    else:
                        icon = tile['icon'].copy()
                        icon.set_alpha(100)
                        screen.blit(icon, tile['rect'].topleft)
                    continue
                elif not tile['affordable']:
                    icon = tile['icon'].copy()
                    icon.set_alpha(100)
                    screen.blit(icon, tile['rect'].topleft)

                    # this section is to make sure that you cannot place another copy of a building when you
                    # run out of resources
                    # when you run out, it does take the building away from your cursor, but it selects the last one
                    # you built
                    if self.selected_tile is not None:
                        if self.selected_tile['name'] == tile['name']:
                            self.selected_tile = None
                else:
                    screen.blit(tile['icon'], tile['rect'].topleft)

        screen.blit(self.resources_panel, (0, 0))

        # draw resource amounts at top of screen
        if self.parent.active_town_center is not None:
            pos = self.width - 720
            for resource, value in self.parent.active_town_center.resourcemanager.resources.items():
                text = f'{resource}: {value}'
                draw_text(screen, text, 30, (0, 0, 0), (pos, 0))
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
