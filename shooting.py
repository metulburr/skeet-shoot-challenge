from math import radians

import pygame as pg

import prepare
from state_engine import GameState
from labels import Label
from animation import Task
from world import World
from clay_pigeon import ClayPigeon


class Shooting(GameState):
    """Main gameplay state."""
    colors = {
            "day": {
                    "sky": pg.Color("skyblue"),
                    "grass": pg.Color(125, 183, 100)},
            "night": {
                    "sky": pg.Color(1, 2, 7),
                    "grass":  pg.Color(11, 15, 8)}}

    def __init__(self):
        super(Shooting, self).__init__()
        self.animations = pg.sprite.Group()
        self.world = World(True)
        self.cooldown = 0
        self.cooldown_duration = 250
        self.clip_size = 10
        self.bullets_in_clip = self.clip_size
        self.cooldown_reload = 1000
        self.crosshairs_day = prepare.GFX['crosshairs_day']
        self.crosshairs_night = prepare.GFX['crosshairs_night']
        self.crosshairs = self.crosshairs_day
        self.crosshairs_rect = self.crosshairs.get_rect()
        self.switched = False

    def startup(self, persistent):
        self.persist = persistent
        self.score = 0
        self.score_label = Label("{}".format(self.score),
                                           {"topleft": (5, 5)}, font_size=64)
        self.world.reset()
        pg.mouse.set_visible(False)

    def get_event(self, event):
        if event.type == pg.QUIT:
            pg.mouse.set_visible(True)
            self.quit = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.quit = True
        elif event.type == pg.MOUSEBUTTONDOWN:
            self.shoot()

    def update(self, dt):
        self.cooldown += dt
        self.animations.update(dt)
        self.world.update(dt)
        for sprite in self.world.all_sprites:
            self.world.all_sprites.change_layer(sprite, sprite.z * -1)
        self.score_label.set_text("{}".format(int(self.score)))
        if self.world.done:
            self.done = True
            self.persist["score"] = int(self.score)
            self.next_state = "HIGHSCORES"
        self.crosshairs_rect.center = pg.mouse.get_pos()
        if self.world.nighttime:
            self.crosshairs = self.crosshairs_night
        else:
            self.crosshairs = self.crosshairs_day
        if self.world.h >= 19:
            if not self.switched:
                prepare.SFX["clicker"].play()
                self.switched = not self.switched
        elif self.world.h < 19:
            self.switched = False
    def shoot(self):
        if self.cooldown < self.cooldown_duration:
            return
        else:
            prepare.SFX["gunshot"].play()
            if self.bullets_in_clip:
                self.bullets_in_clip -= 1
                self.cooldown = 0
            else:
                self.cooldown = self.cooldown_reload
        for clay in [x for x in self.world.clays if not x.shattered]:
            if clay.rect.collidepoint(pg.mouse.get_pos()):
                clay.shatter()
                self.add_points(clay)

    def add_points(self, clay):
        modifier = clay.z / 50.
        score = modifier * (100. / clay.speed)
        self.score += score

    def draw(self, surface):
        surface.fill(self.world.sky)
        surface.fill(self.world.grass, self.world.ground_rect)
        self.world.all_sprites.draw(surface)
        surface.blit(self.crosshairs, self.crosshairs_rect)
        self.score_label.draw(surface)
