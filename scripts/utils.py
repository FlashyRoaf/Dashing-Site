import os
import pygame
import json

ORIGINAL_IMG_PATH = "data/images/"

def load_image(path, alpha):
    if alpha == "y":
        img = pygame.image.load(ORIGINAL_IMG_PATH + path).convert_alpha()
    else:
        img = pygame.image.load(ORIGINAL_IMG_PATH + path).convert()
        img.set_colorkey((0, 0, 0))
    return img

def load_images(path, alpha, flip=False):
    images = []
    for img_name in sorted(os.listdir(ORIGINAL_IMG_PATH + path)):
        if alpha:
            images.append(load_image(path + "/" + img_name, "y") if not flip else pygame.transform.flip(load_image(path + "/" + img_name, "y"), True, False))
        else:
            images.append(load_image(path + "/" + img_name, "n" if not flip else pygame.transform.flip(load_image(path + "/" + img_name, "n"), True, False)))
    return images

def current_fps(tick, font, screen, color, show=True):
    fps = int(tick.get_fps())
    fps_text = font.render(f"FPS:{fps}", True, color)
    if show:
        screen.blit(fps_text, (screen.get_width() - 75,10))

class Animation:
    def __init__(self, images, fps, loop=True):
        self.images = images
        self.fps = fps
        self.loop = loop
        self.done = False
        self.frame = 0
    
    def copy(self):
        return Animation(self.images, self.fps, self.loop)
    
    def img(self):
        return self.images[int(self.frame / self.fps)]

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.fps * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.fps * len(self.images) - 1)
            
            if self.frame >= self.fps * len(self.images) - 1:
                self.done = True

def load_sound(path, volume):
    sfx = pygame.mixer.Sound(path)
    sfx.set_volume(volume)
    return sfx

class Fast_Rect:
    def __init__(self, pos, size, font, image=None, text=None, rectcolor="white", textcolor="black"):
        self.pos = list(pos)
        self.size = list(size)
        self.image = image
        self.font = font
        self.color = textcolor

        if self.image:
            self.rect = self.image.get_rect(topleft=(self.pos))
        else:
            self.image = pygame.Surface(self.size)
            self.image.fill(rectcolor)
            self.rect = pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
            if text:
                self.button_text = self.font.render(str(text), False, textcolor)

    def update(self, updatetext):
        self.button_text = self.font.render(str(updatetext), False, self.color)
    
    def render(self, screen, posadj=(4,4)):
        screen.blit(self.image, self.rect)
        screen.blit(self.button_text, (self.rect.centerx - (self.size[0] / posadj[0]), self.rect.centery - (self.size[1] / posadj[1])))

class Text:
    def __init__(self, pos, font, text, color="black"):
        self.pos = list(pos)
        self.font = font
        self.text = text
        self.color = color
        self.rtext = self.font.render(str(self.text), False, self.color)
    
    def update(self, score):
        self.rtext = self.font.render(str(score), False, self.color)

    def render(self, screen, offset=(0,0)):
        screen.blit(self.rtext, (self.pos[0] - offset[0], self.pos[1] - offset[1]))

def saving(path, guide):
    f = open(path, "w")
    json.dump(guide, f)
    f.close()

def loading_save(path):
    f = open(path, "r")
    data = json.load(f)
    f.close()
    return data

class Level_selector(Fast_Rect):
    def __init__(self, game, pos, size, font, text, image=None):
        super().__init__(pos, size, font, text=text, image=image)

        self.game = game
        self.text = text
        self.button_text = self.font.render(str(text), False, "black")
        
    
    def update(self, mouse, clicking):
        if self.rect.collidepoint(mouse) and clicking:
            return self.game.run(self.text)
            

    def render(self, screen, posadj=(4, 4)):
        return super().render(screen, posadj)