import pygame
import sys
from pygame.locals import *
from scripts.utils import load_image, load_images, current_fps
from scripts.tilemap import Tilemap

class Editor:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Game Name")
        self.screen = pygame.display.set_mode((1280, 720), RESIZABLE | FULLSCREEN)
        self.display = pygame.Surface((400, 240))
        self.cursor = pygame.Surface((2,2))
        self.cursor.fill("white")
        self.mainClock = pygame.time.Clock()
        self.game_font = pygame.font.Font(None, 30)
        pygame.mouse.set_visible(False)

        self.assets = {
            'decor': load_images("tiles/decor", True),
            'large_decor': load_images("tiles/large_decor", True),
            'grass': load_images("tiles/grass", True),
            'stone': load_images("tiles/stone", True),
            'spawners': load_images("tiles/spawners", True)
        }

        self.movement = [False, False, False, False]
        self.scroll = [0, 0]
        self.tilemap = Tilemap(self, tile_size=16)
        self.picked_map = "./data/maps/ownmap.json"
        try:
            self.tilemap.load_map(self.picked_map)
        except FileNotFoundError:
            pass
        
        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True
        self.speed = 2

    def run(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()
            self.display.fill("black")
            
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)

            self.scroll[0] += (self.movement[1] - self.movement[0]) * self.speed
            self.scroll[1] += (self.movement[3] - self.movement[2]) * self.speed
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)
            self.display.blit(pygame.transform.scale(current_tile_img, (current_tile_img.get_width() * 1.4, current_tile_img.get_height() * 1.4)), (10, 200))

            mouse_pos = (mouse_pos[0] / 3.2, mouse_pos[1] / 3)
            self.display.blit(self.cursor, mouse_pos)
            
            tile_pos = (int((mouse_pos[0]  + self.scroll[0]) // self.tilemap.tile_size), int((mouse_pos[1] + self.scroll[1]) // self.tilemap.tile_size))

            if self.ongrid:
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_img, (mouse_pos[0] - (current_tile_img.get_width() / 2), mouse_pos[1] - (current_tile_img.get_height() / 2)))

            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {"type": self.tile_list[self.tile_group], "variant": self.tile_variant, "pos": tile_pos}
            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile["type"]][tile["variant"]]
                    tile_r = pygame.Rect(tile["pos"][0] - self.scroll[0], tile["pos"][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mouse_pos):
                        self.tilemap.offgrid_tiles.remove(tile)

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True

                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append({"type": self.tile_list[self.tile_group], "variant": self.tile_variant, "pos": (mouse_pos[0] - (current_tile_img.get_width() / 2) + self.scroll[0], mouse_pos[1] - (current_tile_img.get_height() / 2) + self.scroll[1])})
                    if event.button == 3:
                        self.right_clicking = True
                    if event.button == 4:
                        if self.shift:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        else:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0

                    if event.button == 5:
                        if self.shift:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                        else:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0
                if event.type == MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == K_LSHIFT:
                        self.shift = True
                    if event.key == K_a:
                        self.movement[0] = True
                    if event.key == K_d:
                        self.movement[1] = True
                    if event.key == K_w:
                        self.movement[2] = True
                    if event.key == K_s:
                        self.movement[3] = True
                    if event.key == K_g:
                        self.ongrid = not self.ongrid
                    if event.key == K_F2:
                        self.tilemap.save_map(self.picked_map)
                    if event.key == K_t:
                        self.tilemap.autotile()
                    if event.key == K_EQUALS:
                        self.speed += 1
                    if event.key == K_MINUS:
                        self.speed -= 1
                if event.type == KEYUP:
                    if event.key == K_LSHIFT:
                        self.shift = False
                    if event.key == K_a:
                        self.movement[0] = False
                    if event.key == K_d:
                        self.movement[1] = False
                    if event.key == K_w:
                        self.movement[2] = False
                    if event.key == K_s:
                        self.movement[3] = False

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0,0))
        
            current_fps(self.mainClock, self.game_font, self.screen, "white")
            pygame.display.update()
            self.mainClock.tick(60)

Editor().run()