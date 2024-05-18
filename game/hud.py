import pygame as pg
import pygame.transform
from .utils import draw_text, load_images

class HUD:

    def __init__(self, manager, width, height):

        self.resourcemanager = manager

        self.width = width
        self.height = height

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

        self.images = load_images()
        self.tiles = self.populate_build_hud()

        self.selected_tile = None
        self.examined_tile = None

        self.town_exists = False

    def populate_build_hud(self):
        render_pos = [self.width * .84 + 10, self.height * .74 + 10]
        surface_w = self.building_panel.get_width() // 5
        leftpos = render_pos[0]

        tiles = []
        horizontal_pos = 0

        # elements to leave out of the build panel
        skip = ['block', 'tree', 'rock', 'water', 'worker']

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

        for tile in self.tiles:
            if self.resourcemanager.is_affordable(tile['name']):
                tile['affordable'] = True
            else:
                tile['affordable'] = False
            if tile['rect'].collidepoint(mouse_pos) and tile['affordable']:
                if mouse_action[0]:
                    self.selected_tile = tile

    def draw(self, screen):

        # if there is a building selected for placement, draw it by the mouse
        if self.selected_tile is not None:
            img = self.selected_tile['image'].copy()
            img.set_alpha(100)

        # place panels on the screen
        screen.blit(self.resources_panel, (0, 0))
        screen.blit(self.building_panel, (self.width * .84, self.height * .74))

        # select hud
        if self.examined_tile is not None:
            w, h = self.select_rect.width, self.select_rect.height
            screen.blit(self.select_panel, (self.width * .35, self.height * .79))
            # img = self.images[self.examined_tile['tile']].copy()
            img = self.examined_tile.image
            img_scale = self.scale_image(img, h=h*.75)
            screen.blit(img_scale, (self.width * .35 + 10,
                                    self.height * .79 + 40))
            # draw_text(screen, self.examined_tile['tile'], 40, (255, 255, 255),
            #           self.select_rect.center)
            draw_text(screen, self.examined_tile.name, 40, (255, 255, 255),
                      self.select_rect.topleft)

        for tile in self.tiles:
            if not self.town_exists:
                if tile['name'] == 'tc':
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

        # draw resource amounts at top of screen
        pos = self.width - 720
        for resource, value in self.resourcemanager.resources.items():
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
