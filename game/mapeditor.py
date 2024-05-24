import pygame as pg
import sys
from camera import Camera
from utils import draw_text
import random
import noise
from settings import TILE_SIZE


CHARMAP = {'tree': 't',
           'rock': 'r',
           '': '.',
           'well': 'w',
           'road': '-',
           'water': '^',
           'chopping': 'c',
           'towncenter': 'x'}

R_CHARMAP = {item: key for key, item in CHARMAP.items()}


def load_images():
    rock = pg.image.load('..\\assets\\graphics\\rock.png').convert_alpha()
    tree = pg.image.load('..\\assets\\graphics\\tree.png').convert_alpha()
    well = pg.image.load('..\\assets\\graphics\\well.png').convert_alpha()
    b1 = pg.image.load('../assets/graphics/house.png').convert_alpha()
    b2 = pg.image.load('..\\assets\\graphics\\building2.png').convert_alpha()
    chopping = pg.image.load('..\\assets\\graphics\\choppingblock.png').convert_alpha()
    block = pg.image.load('..\\assets\\graphics\\testblock.png').convert_alpha()
    road = pg.image.load('..\\assets\\graphics\\road.png').convert_alpha()
    water = pg.image.load('..\\assets\\graphics\\water.png').convert_alpha()
    tc = pg.image.load('..\\assets\\graphics\\towncenter.png').convert_alpha()
    worker = pg.image.load('..\\assets\\graphics\\worker.png').convert_alpha()

    images = {'b1': b1,
              'b2': b2,
              'rock': rock,
              'tree': tree,
              'well': well,
              'chopping': chopping,
              'block': block,
              'road': road,
              'water': water,
              'towncenter': tc,
              'worker': worker
              }

    return images


class Hud:

    def __init__(self, width, height):

        self.width = width
        self.height = height

        self.hud_colour = (198, 155, 93, 175)

        # resouces hud
        self.resouces_surface = pg.Surface((width, height * 0.02), pg.SRCALPHA)
        self.resources_rect = self.resouces_surface.get_rect(topleft=(0, 0))
        self.resouces_surface.fill(self.hud_colour)

        # building hud
        self.build_surface = pg.Surface((width * 0.15, height * 0.25), pg.SRCALPHA)
        self.build_rect = self.build_surface.get_rect(topleft=(self.width * 0.84, self.height * 0.74))
        self.build_surface.fill(self.hud_colour)

        # select hud
        self.select_surface = pg.Surface((width * 0.3, height * 0.2), pg.SRCALPHA)
        self.select_rect = self.select_surface.get_rect(topleft=(self.width * 0.35, self.height * 0.79))
        self.select_surface.fill(self.hud_colour)

        self.images = load_images()
        self.tiles = self.create_build_hud()

        self.selected_tile = None
        self.examined_tile = None

    def create_build_hud(self):

        render_pos = [self.width * .84 + 10, self.height * .74 + 10]
        surface_w = self.build_surface.get_width() // 5
        leftpos = render_pos[0]

        tiles = []
        horizontal_pos = 0

        # elements to leave out of the build panel
        skip = ['block', 'worker']

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
            if tile["rect"].collidepoint(mouse_pos):
                if mouse_action[0]:
                    self.selected_tile = tile

    def draw(self, screen):

        # resource hud
        screen.blit(self.resouces_surface, (0, 0))
        # build hud
        screen.blit(self.build_surface, (self.width * 0.84, self.height * 0.74))
        # select hud
        if self.examined_tile is not None:
            w, h = self.select_rect.width, self.select_rect.height
            screen.blit(self.select_surface, (self.width * 0.35, self.height * 0.79))
            img = self.images[self.examined_tile["tile"]].copy()
            img_scale = self.scale_image(img, h=h*0.9)
            screen.blit(img_scale, (self.width * 0.35 + 10, self.height * 0.79 + 10))
            draw_text(screen, self.examined_tile["tile"], 40, (255, 255, 255), self.select_rect.center)

        for tile in self.tiles:
            screen.blit(tile["icon"], tile["rect"].topleft)

        # resources
        pos = self.width - 400
        for resource in ["wood:", "stone:", "gold:"]:
            draw_text(screen, resource, 30, (255, 255, 255), (pos, 0))
            pos += 100

    def scale_image(self, image, w=None, h=None):

        if (w == None) and (h == None):
            pass
        elif h == None:
            scale = w / image.get_width()
            h = scale * image.get_height()
            image = pg.transform.scale(image, (int(w), int(h)))
        elif w == None:
            scale = h / image.get_height()
            w = scale * image.get_width()
            image = pg.transform.scale(image, (int(w), int(h)))
        else:
            image = pg.transform.scale(image, (int(w), int(h)))

        return image


class World:

    def __init__(self, hud, grid_length_x, grid_length_y, width, height, load=False):
        self.hud = hud
        self.grid_length_x = grid_length_x
        self.grid_length_y = grid_length_y
        self.width = width
        self.height = height

        self.perlin_scale = grid_length_x / 2

        self.grass_tiles = pg.Surface(
            (grid_length_x * TILE_SIZE * 2, grid_length_y * TILE_SIZE + 2 * TILE_SIZE)).convert_alpha()
        self.tiles = load_images()
        self.world = self.create_world(load)

        self.temp_tile = None
        self.examine_tile = None

    def update(self, camera):

        mouse_pos = pg.mouse.get_pos()
        mouse_action = pg.mouse.get_pressed()

        if mouse_action[2]:
            self.examine_tile = None
            self.hud.examined_tile = None

        self.temp_tile = None
        if self.hud.selected_tile is not None:

            grid_pos = self.mouse_to_grid(mouse_pos[0], mouse_pos[1], camera.scroll)

            if self.can_place_tile(grid_pos):
                img = self.hud.selected_tile["image"].copy()
                img.set_alpha(100)

                render_pos = self.world[grid_pos[0]][grid_pos[1]]["render_pos"]
                iso_poly = self.world[grid_pos[0]][grid_pos[1]]["iso_poly"]
                collision = self.world[grid_pos[0]][grid_pos[1]]["collision"]

                self.temp_tile = {
                    "image": img,
                    "render_pos": render_pos,
                    "iso_poly": iso_poly,
                    "collision": collision
                }

                if mouse_action[0] and not collision:
                    self.world[grid_pos[0]][grid_pos[1]]["tile"] = self.hud.selected_tile["name"]
                    self.world[grid_pos[0]][grid_pos[1]]["collision"] = True
                    # self.hud.selected_tile = None

        else:

            grid_pos = self.mouse_to_grid(mouse_pos[0], mouse_pos[1], camera.scroll)

            if self.can_place_tile(grid_pos):

                collision = self.world[grid_pos[0]][grid_pos[1]]["collision"]

                if mouse_action[0] and collision:
                    self.examine_tile = grid_pos
                    self.hud.examined_tile = self.world[grid_pos[0]][grid_pos[1]]

    def draw(self, screen, camera):

        screen.blit(self.grass_tiles, (camera.scroll.x, camera.scroll.y))

        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):
                render_pos = self.world[x][y]["render_pos"]
                tile = self.world[x][y]["tile"]
                if tile != "":
                    screen.blit(self.tiles[tile],
                                (render_pos[0] + self.grass_tiles.get_width() / 2 + camera.scroll.x,
                                 render_pos[1] - (self.tiles[tile].get_height() - TILE_SIZE) + camera.scroll.y))
                    if self.examine_tile is not None:
                        if (x == self.examine_tile[0]) and (y == self.examine_tile[1]):
                            mask = pg.mask.from_surface(self.tiles[tile]).outline()
                            mask = [(x + render_pos[0] + self.grass_tiles.get_width() / 2 + camera.scroll.x,
                                     y + render_pos[1] - (self.tiles[tile].get_height() - TILE_SIZE) + camera.scroll.y)
                                    for x, y in mask]
                            pg.draw.polygon(screen, (255, 255, 255), mask, 3)

        if self.temp_tile is not None:
            iso_poly = self.temp_tile["iso_poly"]
            iso_poly = [(x + self.grass_tiles.get_width() / 2 + camera.scroll.x, y + camera.scroll.y) for x, y in
                        iso_poly]
            if self.temp_tile["collision"]:
                pg.draw.polygon(screen, (255, 0, 0), iso_poly, 3)
            else:
                pg.draw.polygon(screen, (255, 255, 255), iso_poly, 3)
            render_pos = self.temp_tile["render_pos"]
            screen.blit(
                self.temp_tile["image"],
                (
                    render_pos[0] + self.grass_tiles.get_width() / 2 + camera.scroll.x,
                    render_pos[1] - (self.temp_tile["image"].get_height() - TILE_SIZE) + camera.scroll.y
                )
            )

    def create_world(self, load):

        matrix = None
        if load:
            f = open('map.txt', 'r')
            matrix = [i[:-1].split(',') for i in f.readlines()]
            f.close()

        world = []

        for grid_x in range(self.grid_length_x):
            world.append([])
            for grid_y in range(self.grid_length_y):

                world_tile = self.grid_to_world(grid_x, grid_y, load=load)
                if load:
                    char = R_CHARMAP[matrix[grid_x][grid_y]]
                    world_tile['tile'] = char
                    if char != '':
                        world_tile['collision'] = True
                    else:
                        world_tile['collision'] = False

                world[grid_x].append(world_tile)

                render_pos = world_tile["render_pos"]
                self.grass_tiles.blit(self.tiles["block"],
                                      (render_pos[0] + self.grass_tiles.get_width() / 2, render_pos[1]))

        return world

    def grid_to_world(self, grid_x, grid_y, load=False):

        rect = [
            (grid_x * TILE_SIZE, grid_y * TILE_SIZE),
            (grid_x * TILE_SIZE + TILE_SIZE, grid_y * TILE_SIZE),
            (grid_x * TILE_SIZE + TILE_SIZE, grid_y * TILE_SIZE + TILE_SIZE),
            (grid_x * TILE_SIZE, grid_y * TILE_SIZE + TILE_SIZE)
        ]

        iso_poly = [self.cart_to_iso(x, y) for x, y in rect]

        minx = min([x for x, y in iso_poly])
        miny = min([y for x, y in iso_poly])

        tile = ''
        if not load:
            r = random.randint(1, 100)
            perlin = 100 * noise.pnoise2(grid_x / self.perlin_scale, grid_y / self.perlin_scale)

            if (perlin >= 15) or (perlin <= -35):
                tile = "tree"
            else:
                if r == 1:
                    tile = "tree"
                elif r == 2:
                    tile = "rock"

        out = {
            "grid": [grid_x, grid_y],
            "cart_rect": rect,
            "iso_poly": iso_poly,
            "render_pos": [minx, miny],
            "tile": tile,
            "collision": False if tile == "" else True
        }

        return out

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
        for rect in [self.hud.resources_rect, self.hud.build_rect, self.hud.select_rect]:
            if rect.collidepoint(pg.mouse.get_pos()):
                mouse_on_panel = True
        world_bounds = (0 <= grid_pos[0] < self.grid_length_x) and (0 <= grid_pos[1] < self.grid_length_y)

        if world_bounds and not mouse_on_panel:
            return True
        else:
            return False

    def write_map(self):
        f = open('map.txt', 'w')
        for row in self.world:
            f.write(','.join([CHARMAP[i['tile']] for i in row]) + '\n')
        f.close()


class Game:

    def __init__(self, screen, clock, load=False):
        self.screen = screen
        self.clock = clock
        self.width, self.height = self.screen.get_size()

        # hud
        self.hud = Hud(self.width, self.height)

        # world
        self.world = World(self.hud, 50, 50, self.width, self.height, load=load)

        # camera
        self.camera = Camera(self.width, self.height)

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(60)
            self.events()
            self.update()
            self.draw()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()

    def quit(self):
        self.world.write_map()
        pg.quit()
        sys.exit()

    def update(self):
        self.camera.update()
        self.hud.update()
        self.world.update(self.camera)

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.world.draw(self.screen, self.camera)
        self.hud.draw(self.screen)

        draw_text(
            self.screen,
            'fps={}'.format(round(self.clock.get_fps())),
            25,
            (255, 255, 255),
            (10, 10)
        )

        pg.display.flip()


if __name__ == '__main__':
    pg.init()
    pg.mixer.init()
    screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
    clock = pg.time.Clock()
    game = Game(screen, clock, load=True)

    running, playing = True, True
    while running:
        while playing:
            game.run()
