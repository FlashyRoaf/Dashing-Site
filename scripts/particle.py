import pygame

class Particle:
    def __init__(self, game, p_type, pos, velocity=[0,0], frame=0):
        self.game = game
        self.type = p_type
        self.pos = list(pos)
        self.velocity = velocity
        self.animation = self.game.assets["particles/" + p_type].copy()
        self.animation.frame = frame
    
    def update(self):
        kill = False
        
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

        self.animation.update()
        if self.animation.done:
            kill = True

        return kill

    def render(self, screen, offset=(0,0)):
        img = self.animation.img()
        screen.blit(img, (self.pos[0] - offset[0], self.pos[1] - offset[1]))