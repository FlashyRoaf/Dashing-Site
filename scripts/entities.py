import pygame
import math
import random
import time
from scripts.particle import Particle
from scripts.projectile import Projectile, Boss_projectile
from scripts.spark import Spark

class PhysicsEntity:
    def __init__(self, game, e_type, pos, speed, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.speed = speed
        self.size = list(size)
        self.velocity = [0,0]
        self.colissions = {"up": False, "down": False, "left": False, "right": False}

        self.action = ""
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action("idle")
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + "/" + self.action].copy()
    
    def update(self, tilemap, movement=(0,0)):
        self.colissions = {"up": False, "down": False, "left": False, "right": False}

        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        self.pos[0] += frame_movement[0] * self.speed
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.colissions["right"] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.colissions["left"] = True
                self.pos[0] = entity_rect.x
                    
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.colissions["down"] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.colissions["up"] = True
                self.pos[1] = entity_rect.y

        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        
        if self.colissions["down"] or self.colissions["up"]:
            self.velocity[1] = 0
        
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
        
        self.animation.update()

    def render(self, screen, offset=(0,0)):
        screen.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0], self.pos[1] - offset[1]))

class Player(PhysicsEntity):
    def __init__(self, game, pos, speed, size):
        super().__init__(game, "player", pos, speed, size)
        
        self.air_time = 0
        self.max_jumps = 1
        self.wall_slide = False
        self.dashing = 0

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement)

        if self.colissions["down"]:
            self.air_time = 0
            self.max_jumps = 1
            if movement[0] != 0 or self.dashing:
                if tilemap.solid_check((self.pos[0], self.pos[1] + 23), ai=False, t_type="grass"):
                    pvelocity = [0, -math.sin(random.random() * 9) * 0.2]
                    luck = random.random() + 0.2 + abs(self.dashing)
                    if luck > 40 if self.dashing else luck > 1.1:
                        if self.flip:
                            self.game.particles.append(Particle(self.game, "leaf", self.rect().bottomright, pvelocity, random.randint(0, 20)))
                        else:
                            self.game.particles.append(Particle(self.game, "leaf", self.rect().bottomleft, pvelocity, random.randint(0, 20)))
                
        else:
            self.air_time += 1
        
        if (self.colissions["left"] or self.colissions["right"]) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            self.velocity[0] = 0
            self.set_action("wall_slide")
        else:
            self.wall_slide = False

        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action("jump")
            elif movement[0] != 0:
                self.set_action("run")
            else:
                self.set_action("idle")
        
        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, "particle", self.rect().center, pvelocity, random.randint(0, 7)))    
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 4
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, "particle", self.rect().center, pvelocity, random.randint(0, 7)))    
                
        
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        if self.velocity[0] < 0:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
        
    def jump(self):
        if self.wall_slide:
            self.velocity[0] = 2.5 if self.flip else -2.5
            self.velocity[1] = -1.5
            self.air_time = 5
            self.max_jumps = max(0, self.max_jumps - 1)
            self.game.sfx["jump"].play()
        elif self.max_jumps:
            self.velocity[1] = -3
            self.max_jumps -= 1
            self.air_time = 5
            self.game.sfx["jump"].play()
    
    def dash(self):
        if not self.dashing:
            self.dashing = -60 if self.flip else 60
            self.game.sfx["dash"].play()
    
    def render(self, screen, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(screen, offset)

class Enemy(PhysicsEntity):
    def __init__(self, game, pos, speed, size):
        super().__init__(game, "enemy", pos, speed, size)

        self.walking = 0
    
    def update(self, tilemap, shoot=True, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.colissions["left"] or self.colissions["right"]):
                    self.flip = not self.flip
                movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)

            if not self.walking and shoot:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                angle = math.atan2(self.game.player.pos[1] - self.pos[1] + 5, self.game.player.pos[0] - self.pos[0] + 7)
                if self.flip and dis[0] < 0:
                    self.game.sfx["shoot"].play()
                    self.game.projectiles.append(Projectile(self.game, [self.rect().centerx - 7, self.rect().centery], 1.5, [math.cos(angle), math.sin(angle)]))
                    for i in range(4):
                        self.game.sparks.append(Spark(self.game.projectiles[-1].pos, random.random() - 0.5 + math.pi, 2 + random.random()))
                if not self.flip and dis[0] > 0:
                    self.game.sfx["shoot"].play()
                    self.game.projectiles.append(Projectile(self.game, [self.rect().centerx + 7, self.rect().centery], 1.5, [math.cos(angle), math.sin(angle)]))
                    for i in range(4):
                        self.game.sparks.append(Spark(self.game.projectiles[-1].pos, random.random() - 0.5, 2 + random.random()))
                    
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        
        if movement[0] != 0:
            self.set_action("run")
        else:
            self.set_action("idle")
        
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.sfx["hit"].play()
                self.game.screen_shake = max(16, self.game.screen_shake)
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, "particle", self.rect().center, [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 1 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 4 + random.random()))
                return True

        super().update(tilemap, movement)
    
    def render(self, screen, offset=(0, 0)):
        super().render(screen, offset)

        if self.flip:
            screen.blit(pygame.transform.flip(self.game.assets["shiruken"], True, False), (self.rect().centerx - offset[0] - 8, self.rect().centery - offset[1] + 1))
        else:
            screen.blit(self.game.assets["shiruken"], (self.rect().centerx - offset[0] + 8, self.rect().centery - offset[1] + 1))

class Boss(PhysicsEntity):
    def __init__(self, game, pos, speed, size):
        super().__init__(game, "boss", pos, speed, size)

        self.walking = 0
        self.iframe = 0
        self.life = 5
        self.ult = True
    
    def update(self, tilemap, shoot=True, movement=(0, 0)):
        self.iframe -= 1
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-10 if self.flip else 10), self.pos[1] + 32)):
                if (self.colissions["left"] or self.colissions["right"]):
                    self.flip = not self.flip
                movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)

            if not self.walking and shoot:
                self.set_action("attack")
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                angle = math.atan2(self.game.player.pos[1] - self.pos[1] - 5, self.game.player.pos[0] - self.pos[0] + 2)
                if self.flip:
                    self.shooting = True
                    self.game.sfx["shoot"].play()
                    self.game.projectiles.append(Boss_projectile(self.game, [self.rect().centerx - 10, self.rect().centery], 1.5, 0, angle, [math.cos(angle), math.sin(angle)]))
                    self.game.projectiles.append(Boss_projectile(self.game, (self.game.projectiles[-1].pos[0] - math.cos(angle) * 8, self.game.projectiles[-1].pos[1] - math.sin(angle) * 8), 1.5, 1, angle, [math.cos(angle), math.sin(angle)], 2))
                    if self.life == 1:
                        self.game.projectiles.append(Boss_projectile(self.game, (self.game.projectiles[-1].pos[0] - math.cos(angle) * 8, self.game.projectiles[-1].pos[1] - math.sin(angle) * 8), 1.5, 0, angle, [math.cos(angle), math.sin(angle)]))
                    for i in range(4):
                        self.game.sparks.append(Spark(self.game.projectiles[-1].pos, random.random() - 0.5 + math.pi, 2 + random.random()))
                if not self.flip:
                    self.shooting = True
                    self.game.sfx["shoot"].play()
                    self.game.projectiles.append(Boss_projectile(self.game, [self.rect().centerx + 7, self.rect().centery], 1.5, 0, angle, [math.cos(angle), math.sin(angle)]))
                    self.game.projectiles.append(Boss_projectile(self.game, (self.game.projectiles[-1].pos[0] - math.cos(angle) * 8, self.game.projectiles[-1].pos[1] - math.sin(angle) * 8), 1.5, 1, angle, [math.cos(angle), math.sin(angle)], 2))
                    if self.life == 1:
                        self.game.projectiles.append(Boss_projectile(self.game, (self.game.projectiles[-1].pos[0] - math.cos(angle) * 8, self.game.projectiles[-1].pos[1] - math.sin(angle) * 8), 1.5, 0, angle, [math.cos(angle), math.sin(angle)]))
                    for i in range(4):
                        self.game.sparks.append(Spark(self.game.projectiles[-1].pos, random.random() - 0.5, 2 + random.random()))
        
        if self.life == 1 and self.ult:
            angle = math.atan2(self.game.player.pos[1] - self.pos[1] - 5, self.game.player.pos[0] - self.pos[0] + 2)
            for i in range(100):
                self.game.projectiles.append(Boss_projectile(self.game, [self.rect().centerx, self.rect().centery], 1.5, i, angle + (i / 2), [math.cos(angle + (i / 2)), math.sin(angle + (i / 2))]))
            self.ult = False
                    
        elif random.random() < 0.02:
            self.walking = random.randint(10, 40)
        
        if movement[0] != 0:
            self.set_action("run")
        else:
            self.set_action("idle")
        
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                if self.iframe <= 0:
                    self.game.sfx["hit"].play()
                    self.game.screen_shake = max(16, self.game.screen_shake)
                    self.life -= 1
                    for i in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                        self.game.particles.append(Particle(self.game, "particle", self.rect().center, [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], random.randint(0, 7)))
                    self.game.sparks.append(Spark(self.rect().center, 0, 1 + random.random()))
                    self.game.sparks.append(Spark(self.rect().center, math.pi, 4 + random.random()))
                    self.iframe = 20
            
            if self.life <= 0:
                return True

        super().update(tilemap, movement)