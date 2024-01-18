import random

class Cloud:
    def __init__(self, pos, image, speed, depth):
        self.pos = list(pos)
        self.image = image
        self.speed = speed
        self.depth = depth
        self.rect = self.image.get_rect(topleft=(self.pos))
    
    def update(self):
        self.pos[0] += self.speed

    def render(self, screen, offset=(0,0)):
        render_pos = (self.pos[0] - offset[0] * self.depth, self.pos[1] - offset[1] * self.depth)
        screen.blit(self.image, (render_pos[0] % (screen.get_width() + self.image.get_width()) - self.image.get_width(), render_pos[1] % (screen.get_height() + self.image.get_height()) - self.image.get_height()))

class Clouds:
    def __init__(self, cloud_images, count=16):
        self.clouds = []

        for i in range(count):
            self.clouds.append(Cloud((random.random() * 99999, random.random() * 99999), random.choice(cloud_images), random.random() * 0.05 + 0.05, random.random() * 0.6 + 0.2))
        
        self.clouds.sort(key=lambda x: x.depth)
    
    def update(self):
        for cloud in self.clouds:
            cloud.update()
    
    def render(self, screen, offset=(0,0)):
        for cloud in self.clouds:
            cloud.render(screen, offset=offset)