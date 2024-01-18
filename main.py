import pygame
import sys
import random
import math
import os
from pygame.locals import *
from scripts.entities import PhysicsEntity, Player, Enemy, Boss
from scripts.utils import load_image, current_fps, load_images, Animation, load_sound, Fast_Rect, Text, saving, loading_save, Level_selector
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark


class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.mixer.set_num_channels(64)
        pygame.display.set_caption("Dashing Site")
        self.screen = pygame.display.set_mode((1280, 720), RESIZABLE | FULLSCREEN)
        self.display = pygame.Surface((400, 240), SRCALPHA)
        self.nonoutline_display = pygame.Surface((400, 240))
        self.mainClock = pygame.time.Clock()
        self.game_font = pygame.font.Font(None, 25)
        pygame.mouse.set_visible(True)

        self.movement = [False, False]
        self.pickup = False

        self.assets = {
            'decor': load_images("tiles/decor", True),
            'large_decor': load_images("tiles/large_decor", True),
            'grass': load_images("tiles/grass", False),
            'stone': load_images("tiles/stone", True),
            'spawners': load_images("tiles/spawners", True),
            'background': load_image("background.png", "y"),
            'cloud': load_images("clouds", True),
            'player/idle': Animation(load_images("entities/player/idle", True, True), fps=18),
            'player/run': Animation(load_images("entities/player/run", True, True), fps=7),
            'player/jump': Animation(load_images("entities/player/jump", True, True), fps=4),
            'player/wall_slide': Animation(load_images("entities/player/wall_slide", True, True), fps=4),
            'enemy/idle': Animation(load_images("entities/enemy/idle", True, True), fps=24),
            'enemy/run': Animation(load_images("entities/enemy/run", True, True), fps=7),
            'boss/idle': Animation(load_images("entities/boss/idle", True, True), fps=7),
            'boss/run': Animation(load_images("entities/boss/run", True, True), fps=7),
            'boss/attack': Animation(load_images("entities/boss/attack", True, True), fps=7),
            'particles/leaf': Animation(load_images("particles/leaf", False), fps=20, loop=False),
            'particles/particle': Animation(load_images("particles/particle", False), fps=12, loop=False),
            'shiruken': load_image("shiruken.png", "y"),
            'fireball': load_images("fireball", True),
            'life': pygame.Surface((20, 10)),
            'title': load_image("title.png", "y"),
        }

        self.sfx = {
            'jump': load_sound("./data/sfx/jump.wav", 0.3),
            'dash': load_sound("./data/sfx/dash.wav", 0.5),
            'hit': load_sound("./data/sfx/hit.wav", 0.8),
            'shoot': load_sound("./data/sfx/shoot.wav", 0.5),
        }


        self.data = {
            "highest_score": 0,
            "stage": 0,
        }

        try:
            self.data = loading_save("./data/save.json")
        except FileNotFoundError:
            pass

        self.player = Player(self, (100,10), 2, (16,15))
        

        self.tilemap = Tilemap(self, tile_size=16)
        self.level = 0


        self.clouds = Clouds(self.assets["cloud"], 12)
        self.screen_shake = 0

        self.show_fps = False
    
    def load_level(self, map_id, path=None):
        self.assets["life"].fill("red")
        self.tilemap.load_map(str(path) + str(map_id) + ".json")

        self.leaf_spawners = []
        for tree in self.tilemap.extract([("large_decor", 1), ("large_decor", 4)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 13))

        self.enemies = []
        self.bosses = []
        for spawner in self.tilemap.extract([("spawners", 0), ("spawners", 1), ("spawners", 2)]):
            if spawner["variant"] == 0:
                self.player.pos = spawner["pos"]
                self.player.air_time = 0
            elif spawner["variant"] == 1:
                self.enemies.append(Enemy(self, spawner["pos"], 1, (12,15)))
            else:
                self.bosses.append(Boss(self, spawner["pos"], 2, (15,30)))

        self.particles = []
        self.projectiles = []
        self.sparks = []
        self.life = 3

        self.scroll = [0, 0]
        self.transition = -30

        
    def run(self, level):
        MAPS_PATH = "./data/maps/"
        self.load_level(level, MAPS_PATH)
        self.level = level

        while True:
            self.display.fill((0, 0, 0, 0))
            self.nonoutline_display.blit(pygame.transform.scale(self.assets["background"], self.display.get_size()), (0,0))

            self.screen_shake = max(0, self.screen_shake - 1)

            if not len(self.enemies) and not len(self.bosses):
                self.transition += 1
                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir("./data/maps")) - 1)
                    self.load_level(self.level, MAPS_PATH)
            if self.transition < 0:
                self.transition += 1
            
            if self.life <= 0:
                self.player.velocity[0] = 0
                self.player.velocity[1] = 0
                self.life -= 1
                if self.life <= 10:
                    self.transition = min(30, self.transition + 1)

            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, "leaf", pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.clouds.update()
            self.clouds.render(self.nonoutline_display, offset=render_scroll)
            self.tilemap.render(self.display, offset=render_scroll)

            
            for boss in self.bosses.copy():
                kill = boss.update(self.tilemap)
                boss.render(self.display, offset=render_scroll)
                
                if kill:
                    self.bosses.remove(boss)

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap)
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if self.life > 0:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)

            for projectile in self.projectiles.copy():
                kill = projectile.update()
                projectile.render(self.display, offset=render_scroll)

                if abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile.pos):
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, "particle", self.player.rect().center, [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], random.randint(0, 7)))

                        self.life -= projectile.damage
                        self.projectiles.remove(projectile)
                        self.screen_shake = max(16, self.screen_shake)
                        self.sfx["hit"].play()
                
                if kill:
                    self.projectiles.remove(projectile)
                        

            if self.player.air_time > 400 or self.life <= -60:
                self.load_level(self.level, MAPS_PATH)
                self.player.dashing = 0
            
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, render_scroll)
                if kill:
                    self.sparks.remove(spark)
            
            display_mask = pygame.mask.from_surface(self.display)
            display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1,0), (1,0), (0,-1), (0,1)]:
                self.nonoutline_display.blit(display_silhouette, offset)


            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)

                if particle.type == "leaf":
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                
                if kill:
                    self.particles.remove(particle)
            
            for i in range(self.life):
                self.display.blit(self.assets["life"], (21 * (i - 1) + 26, 5)) 

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.main_menu()
                    if event.key == K_a:
                        self.movement[0] = True
                    if event.key == K_d:
                        self.movement[1] = True
                    if event.key == K_SPACE:
                        self.player.jump()
                    if event.key == K_k:
                        self.player.dash()
                    if event.key == K_k:
                        self.pickup = True
                    if event.key == K_F2:
                        self.show_fps = not self.show_fps
                if event.type == KEYUP:
                    if event.key == K_a:
                        self.movement[0] = False
                    if event.key == K_d:
                        self.movement[1] = False
                    if event.key == K_k:
                        self.pickup = False
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.player.dash()
        
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0,0))
        
            self.nonoutline_display.blit(self.display, (0,0))
        
            screenshake_offset = (random.random() * self.screen_shake - self.screen_shake / 2, random.random() * self.screen_shake - self.screen_shake / 2)
            self.screen.blit(pygame.transform.scale(self.nonoutline_display, self.screen.get_size()), screenshake_offset)
        
            current_fps(self.mainClock, self.game_font, self.screen, "black", self.show_fps)
            pygame.display.update()
            self.mainClock.tick(60)

    def main_menu(self):
        screen = pygame.Surface((400, 240))
        game_font = pygame.font.Font(None, 20)

        stage_button = Fast_Rect((80, 180), (80, 40), self.game_font,  text="Stage")
        dodging_button = Fast_Rect((240, 180), (80, 40), self.game_font, text="Dodging")

        self.tilemap.load_map("./map1.json")

        leaf_spawners = []
        particles = []
        enemies = []
        levels = []

        scroll = [0, 0]
        flip_scroll = [False, False]

        clicking = False
        picking_stage = False

        for i in range(len(sorted(os.listdir("data/maps")))):
            levels.append(Level_selector(self, (23 * (i - 1) + 72, self.display.get_height() // 2 - 20), (20, 20), game_font, int(i)))

        for tree in self.tilemap.extract([("large_decor", 1), ("large_decor", 4)], keep=True):
            leaf_spawners.append(pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 13))

        for spawner in self.tilemap.extract([("spawners", 1)]):
            enemies.append(Enemy(self, spawner["pos"], 1, (12,15)))
        
        pygame.mixer.music.load("./data/music.wav")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        while True:
            mouse_pos = pygame.mouse.get_pos()
            mouse_pos = (mouse_pos[0] / 3.2, mouse_pos[1] / 3)

            if stage_button.rect.collidepoint(mouse_pos) and clicking:
                picking_stage = True
            
            if dodging_button.rect.collidepoint(mouse_pos) and clicking:
                self.dodge_mode()
            
            self.display.fill((0, 0, 0, 0))
            self.nonoutline_display.blit(pygame.transform.scale(self.assets["background"], self.display.get_size()), (0,0))

            
            if not flip_scroll[0]:
                scroll[0] += 0.2
            else:
                scroll[0] -= 0.2
            if not flip_scroll[1]:
                scroll[1] += 0.1
            else:
                scroll[1] -= 0.1
            
            if (scroll[0] > 150 or scroll[0] < -50):
                flip_scroll[0] = not flip_scroll[0]
            if (scroll[1] > 100 or scroll[1] < -50):
                flip_scroll[1] = not flip_scroll[1]
            
            render_scroll = (int(scroll[0]), int(scroll[1]))

            self.clouds.update()
            self.clouds.render(self.nonoutline_display, render_scroll)
            self.tilemap.render(self.display, render_scroll)

            
            for enemy in enemies.copy():
                kill = enemy.update(self.tilemap, shoot=False)
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    enemies.remove(enemy)

            for rect in leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    particles.append(Particle(self, "leaf", pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
            
            display_mask = pygame.mask.from_surface(self.display)
            display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1,0), (1,0), (0,-1), (0,1)]:
                self.nonoutline_display.blit(display_silhouette, offset)
            
            for particle in particles.copy():
                kill = particle.update()
                particle.render(self.display, render_scroll)

                if particle.type == "leaf":
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                
                if kill:
                    particles.remove(particle)
            
            if picking_stage:
                for level in levels:
                    level.update(mouse_pos, clicking)
                    level.render(self.display, (3,4))
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        clicking = True
                if event.type == MOUSEBUTTONUP:
                    if event.button == 1:
                        clicking = False
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == K_F2:
                        self.show_fps = not self.show_fps

            stage_button.render(self.display)
            dodging_button.render(self.display, (2.5,4))
            self.display.blit(self.assets["title"], (self.display.get_width() // 2 - self.assets["title"].get_width() // 2, 20))

            self.nonoutline_display.blit(self.display, (0,0))
            
            self.screen.blit(pygame.transform.scale(self.nonoutline_display, self.screen.get_size()), (0,0))
            
            current_fps(self.mainClock, self.game_font, self.screen, "black", self.show_fps)
            pygame.display.update()
            self.mainClock.tick(60)
    
    def dodge_mode(self):
        MAPS_PATH = "./data/dodging_maps/"
        SAVE_PATH = "./data/save.json"

        picked_map = 0

        score = 0
        current_score = 0
        score_text = Text((10, self.display.get_height() - 20), self.game_font, score, "white")
        
        highest_score = self.data["highest_score"]

        result_popup = Fast_Rect((20,20), (360, 200), self.game_font, text=f"Highest Score : {highest_score}")
        current_tscore = Text((result_popup.rect.centerx - result_popup.size[0] / 4, result_popup.rect.centery), self.game_font, current_score, "black")

        clicking = False
        
        self.load_level(picked_map, MAPS_PATH)
        while True:
            mouse_pos = pygame.mouse.get_pos()
            mouse_pos = (mouse_pos[0] / 3.2, mouse_pos[1] / 3)

            self.display.fill((0, 0, 0, 0))
            self.nonoutline_display.blit(pygame.transform.scale(self.assets["background"], self.display.get_size()), (0,0))

            self.screen_shake = max(0, self.screen_shake - 1)

            if not len(self.enemies):
                pass
            if self.transition < 0:
                self.transition += 1

            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, "leaf", pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.clouds.update()
            self.clouds.render(self.nonoutline_display, offset=render_scroll)
            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap)
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if self.life > 0:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)

            for projectile in self.projectiles.copy():
                kill = projectile.update()
                projectile.render(self.display, offset=render_scroll)

                if abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile.pos):
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, "particle", self.player.rect().center, [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], random.randint(0, 7)))

                        self.projectiles.remove(projectile)
                        self.life -= 1
                        self.screen_shake = max(16, self.screen_shake)
                        self.sfx["hit"].play()
                
                if kill:
                    score += 100
                    self.projectiles.remove(projectile)
                        
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, render_scroll)
                if kill:
                    self.sparks.remove(spark)
            
            display_mask = pygame.mask.from_surface(self.display)
            display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1,0), (1,0), (0,-1), (0,1)]:
                self.nonoutline_display.blit(display_silhouette, offset)


            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)

                if particle.type == "leaf":
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                
                if kill:
                    self.particles.remove(particle)
            
            for i in range(self.life):
                self.display.blit(self.assets["life"], (21 * (i - 1) + 26, 5)) 
            
            if self.life <= 0 or self.player.air_time > 400:
                if score > self.data["highest_score"]:
                    self.data["highest_score"] = score
                    saving(SAVE_PATH, self.data)
                    highest_score = self.data["highest_score"]
                self.player.velocity[0] = 0
                self.player.velocity[1] = 0
                score = 0
                result_popup.render(self.display)
                current_tscore.update(f"Score : {current_score}")
                current_tscore.render(self.display)
                self.life -= 1
                if result_popup.rect.collidepoint(mouse_pos) and clicking:
                    if self.life <= 10:
                        self.transition = min(30, self.transition + 1)
                    if self.life <= -60:
                        self.load_level(picked_map, MAPS_PATH)
                        current_score = 0
            
            if current_score < score:
                current_score = score
            score_text.update(score)
            score_text.render(self.display)

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.main_menu()
                    if event.key == K_a:
                        self.movement[0] = True
                    if event.key == K_d:
                        self.movement[1] = True
                    if event.key == K_SPACE:
                        self.player.jump()
                    if event.key == K_k:
                        self.player.dash()
                    if event.key == K_k:
                        self.pickup = True
                    if event.key == K_F2:
                        self.show_fps = not self.show_fps
                if event.type == KEYUP:
                    if event.key == K_a:
                        self.movement[0] = False
                    if event.key == K_d:
                        self.movement[1] = False
                    if event.key == K_k:
                        self.pickup = False
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.player.dash()
                        clicking = True
                if event.type == MOUSEBUTTONUP:
                    if event.button == 1:
                        clicking = False
        
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0,0))
        
            self.nonoutline_display.blit(self.display, (0,0))
        
            screenshake_offset = (random.random() * self.screen_shake - self.screen_shake / 2, random.random() * self.screen_shake - self.screen_shake / 2)
            self.screen.blit(pygame.transform.scale(self.nonoutline_display, self.screen.get_size()), screenshake_offset)
        
            current_fps(self.mainClock, self.game_font, self.screen, "black", self.show_fps)
            pygame.display.update()
            self.mainClock.tick(60)

Game().main_menu()