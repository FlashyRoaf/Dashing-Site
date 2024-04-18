import pygame
import random
import math
from scripts.particle import Particle

class Projectile:
    def __init__(self, game, pos, speed, velocity=[0,0], damage=1):
        self.game = game
        self.pos = list(pos)
        self.velocity = velocity
        self.speed = speed
        self.timer = 0
        self.damage = damage
        self.image = self.game.assets["shiruken"]
    
    def update(self):
        self.pos[0] += self.velocity[0] * self.speed
        self.pos[1] += self.velocity[1] * self.speed
        self.timer += 1

        if self.timer > 360:
            return True
    
    def render(self, screen, offset=(0,0), details=True):
        if details:
            image_copy = pygame.transform.rotate(self.image, self.timer)
            screen.blit(image_copy, (self.pos[0] - (image_copy.get_width() // 2) - offset[0], self.pos[1] - (image_copy.get_height() // 2) - offset[1]))
        else:
            screen.blit(self.image, (self.pos[0] - (self.image.get_width() // 2) - offset[0], self.pos[1] - (self.image.get_height() // 2) - offset[1]))

class Boss_projectile(Projectile):
    def __init__(self, game, pos, speed, version, angle, velocity=[0,0], damage=1):
        super().__init__(game, pos, speed, velocity, damage)

        self.angle = angle
        self.image = self.game.assets["fireball"]
        self.version = version % len(self.image)
    
    def render(self, screen, offset=(0,0), details=True):
        image_copy = pygame.transform.rotate(self.image[self.version], -(self.angle * 180 / math.pi) -180)
        screen.blit(image_copy, (self.pos[0] - (image_copy.get_width() // 2) - offset[0], self.pos[1] - (image_copy.get_height() // 2) - offset[1]))