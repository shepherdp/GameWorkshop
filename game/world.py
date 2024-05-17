import pygame as pg
import random
import noise
from .settings import TILE_SIZE
from .utils import load_images


class World:

    def __init__(self, hud, grid_length_x, grid_length_y, width, height):
        self.hud = hud
        self.grid_length_x = grid_length_x
        self.grid_length_y = grid_length_y
        self.width = width
        self.height = height

        self.perlin_scale = grid_length_x / 2

        self.grass_tiles = pg.Surface(
            (grid_length_x * TILE_SIZE * 2,
             grid_length_y * TILE_SIZE + 2 * TILE_SIZE)
        ).convert_alpha()

        self.tiles = self.hud.images
        self.world = self.create_world()

        self.temp_tile = None
        self.examine_tile = None

    def update(self, camera):

        mouse_pos = pg.mouse.get_pos()
        mouse_action = pg.mouse.get_pressed()

        if mouse_action[2]:
            self.examine_tile = None
            self.hud.examined_tile = None

        self.temp_tile = None

        # if there is an element ready to be build
        if self.hud.selected_tile is not None:
            # find grid coordinates of mouse
            grid_pos = self.mouse_to_grid(mouse_pos[0], mouse_pos[1], camera.scroll)

            if self.can_place_tile(grid_pos):
                # make transparent copy of image to hover with mouse
                img = self.hud.selected_tile["image"].copy()
                img.set_alpha(100)

                render_pos = self.world[grid_pos[0]][grid_pos[1]]["render_pos"]
                iso_poly = self.world[grid_pos[0]][grid_pos[1]]["iso_poly"]
                collision = self.world[grid_pos[0]][grid_pos[1]]["collision"]

                # create temp tile for use in draw method
                self.temp_tile = {
                    "image": img,
                    "render_pos": render_pos,
                    "iso_poly": iso_poly,
                    "collision": collision
                }

                # place the building down if the user left-clicked
                if mouse_action[0] and not collision:
                    self.world[grid_pos[0]][grid_pos[1]]["tile"] = self.hud.selected_tile["name"]
                    self.world[grid_pos[0]][grid_pos[1]]["collision"] = True
                    self.hud.selected_tile = None

        # the user has clicked on a tile with a blank cursor
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
                    # check if this tile was clicked
                    if self.examine_tile is not None:
                        if x == self.examine_tile[0] and y == self.examine_tile[1]:
                            mask = pg.mask.from_surface(self.tiles[tile]).outline()
                            mask = [(x + render_pos[0] +  self.grass_tiles.get_width() / 2 + camera.scroll.x,
                                     y + render_pos[1] - (self.tiles[tile].get_height() - TILE_SIZE) + camera.scroll.y)
                                    for x, y in mask]
                            pg.draw.polygon(screen, (255, 255, 255), mask, 3)


        # if there is a building ready to be placed
        if self.temp_tile is not None:

            # grab the vertices for the indicator square
            iso_poly = self.temp_tile["iso_poly"]
            iso_poly = [(x + self.grass_tiles.get_width() / 2 + camera.scroll.x, y + camera.scroll.y) for x, y in
                        iso_poly]

            # draw red square
            if self.temp_tile["collision"]:
                pg.draw.polygon(screen, (255, 0, 0), iso_poly, 3)
            # draw green square
            else:
                pg.draw.polygon(screen, (0, 255, 0), iso_poly, 3)

            # make object float with mouse
            # screen.blit(img, pg.mouse.get_pos())

            # make object snap to grid spaces
            render_pos = self.temp_tile["render_pos"]
            screen.blit(
                self.temp_tile["image"],
                (
                    render_pos[0] + self.grass_tiles.get_width() / 2 + camera.scroll.x,
                    render_pos[1] - (self.temp_tile["image"].get_height() - TILE_SIZE) + camera.scroll.y
                )
            )

    def create_world(self):

        world = []

        for grid_x in range(self.grid_length_x):
            world.append([])
            for grid_y in range(self.grid_length_y):
                world_tile = self.grid_to_world(grid_x, grid_y)
                world[grid_x].append(world_tile)

                render_pos = world_tile["render_pos"]
                self.grass_tiles.blit(self.tiles["block"],
                                      (render_pos[0] + self.grass_tiles.get_width() / 2, render_pos[1]))

        return world

    def grid_to_world(self, grid_x, grid_y):

        # find corner coordinates
        rect = [
            (grid_x * TILE_SIZE, grid_y * TILE_SIZE),
            (grid_x * TILE_SIZE + TILE_SIZE, grid_y * TILE_SIZE),
            (grid_x * TILE_SIZE + TILE_SIZE, grid_y * TILE_SIZE + TILE_SIZE),
            (grid_x * TILE_SIZE, grid_y * TILE_SIZE + TILE_SIZE)
        ]

        # convert to display coordinates
        iso_poly = [self.cart_to_iso(x, y) for x, y in rect]

        # get top-left corner
        minx = min([x for x, y in iso_poly])
        miny = min([y for x, y in iso_poly])

        # populate tiles with random elements
        r = random.randint(1, 100)
        perlin = 100 * noise.pnoise2(grid_x / self.perlin_scale, grid_y / self.perlin_scale)

        if (perlin >= 15) or (perlin <= -35):
            tile = "tree"
        else:
            if r == 1:
                tile = "tree"
            elif r == 2:
                tile = "rock"
            else:
                tile = ""

        # return dictionary
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
        # convert cartesian coordinates to display coordinates
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

    def is_in_bounds(self, x, y):
        return (0 <= x < self.grid_length_x) and (0 <= y < self.grid_length_y)

    def can_place_tile(self, grid_pos):
        # check if mouse collides with one of the HUD panels
        mouse_on_panel = False
        for rect in [self.hud.resources_rect, self.hud.building_rect, self.hud.select_rect]:
            if rect.collidepoint(pg.mouse.get_pos()):
                mouse_on_panel = True

        # check if mouse position is on the map
        world_bounds = self.is_in_bounds(grid_pos[0], grid_pos[1])

        if world_bounds and not mouse_on_panel:
            return True
        else:
            return False
