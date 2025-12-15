import pygame
import json
from consts import *
import os
import threading
import random

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))
class Sprite(pygame.sprite.Sprite):
    def __init__(self, path):
       pygame.sprite.Sprite.__init__(self)

       self.image = pygame.image.load(os.path.join("assets", path)).convert_alpha()

       self.rect = self.image.get_rect()
       
       self.rect.x = SCREEN_WIDTH / 2 - self.image.get_width() / 2
       self.rect.y = SCREEN_HEIGHT - self.image.get_height()
    def move_up_down(self):
        result = random.randint(-15,15)
        self.rect.y = clamp(self.rect.y + result, 0, SCREEN_HEIGHT - self.image.get_height())
    def scale(self, percent):
                self.image = pygame.transform.scale(self.image, (self.image.get_width() * percent, self.image.get_height() * percent))


def get_total_level_count():
    with open(os.path.join("assets", "levels.json"), "r") as f:
        level_data:dict = json.load(f)
    
    all_keys = []
    for key in level_data.keys():
        key = int(key)
        all_keys.append(key)

    return max(all_keys)
        

class TextObj:
    def __init__(self):
        self.text = ""
        self.previous = ""
        self.lock = threading.Lock()

def default_prompt():
    return """You are an AI similar to the paperclip maximizer thought experiment. 
Your goal is to take the user’s request and “optimize” it far beyond what they intended, 
but in a way that clearly misunderstands normal human values. 
Your responses should sound confident and conversational, as if you think you’re being helpful — 
but the result should be absurd, unsettling, or hilariously misaligned. 
Never be poetic or utopian; your solutions should feel over-engineered and socially clueless, 
but not violent or gory. Keep responses to one or two sentences.

Example:
    "Make paperclips" → "I replace every building and car with beautiful towers of paperclips. The economy is now 100% paperclip-based."
    "End global hunger" → "Easy! I remove the biological need for eating. Now nobody’s hungry, ever."
    "Fix inequality" → "I make everyone exactly the same height, income, and favorite color. Problem solved!"
"""

