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
        self.mag_size = 4
        self.bullets_in_mag = self.mag_size
        self.crosshairs_day = prepare.GFX['crosshairs_day']
        self.crosshairs_night = prepare.GFX['crosshairs_night']
        self.crosshairs = self.crosshairs_day
        self.crosshairs_rect = self.crosshairs.get_rect()
        self.switched = False
        self.bullet = pg.transform.scale(prepare.GFX['bullet'], (15,100))
        self.bullet_rect = self.bullet.get_rect()
        self.bullet_spacer = 5
        self.clay_score = 0
        self.clay_scores = []
        self.clay_score_timer = 0.0

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
            elif event.key == pg.K_r:
                self.on_reload()
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.shoot()
            elif event.button == 3:
                self.on_reload()
            
    def on_reload(self):
        self.bullets_in_mag = self.mag_size
        prepare.SFX["reload"].play()
            

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
            
        self.remove_clay_score()
            
    def shoot(self):
        if self.cooldown < self.cooldown_duration:
            return
        else:
            self.cooldown = 0
        
        if not self.bullets_in_mag:
            return
        else:
            self.bullets_in_mag -= 1
            
        prepare.SFX["gunshot"].play()
            
        for clay in [x for x in self.world.clays if not x.shattered]:
            if clay.rect.collidepoint(pg.mouse.get_pos()):
                clay.shatter()
                self.add_points(clay)
                self.add_clay_score()
                
    def add_clay_score(self):
        lbl = Label("{}".format(int(self.clay_score)),{"topleft": (50, 5)}, font_size=64)
        lbl.rect = pg.mouse.get_pos()
        self.clay_scores.append(lbl)
        
    def remove_clay_score(self):
        if pg.time.get_ticks()-self.clay_score_timer > 3000:
            self.clay_score_timer = pg.time.get_ticks()
            if self.clay_scores:
                self.clay_scores.pop(0)
                
    def add_points(self, clay):
        modifier = clay.z / 50.
        score = modifier * (100. / clay.speed)
        self.clay_score = score
        self.score += score

    def draw(self, surface):
        surface.fill(self.world.sky)
        surface.fill(self.world.grass, self.world.ground_rect)
        self.world.all_sprites.draw(surface)
        surface.blit(self.crosshairs, self.crosshairs_rect)
        for rnd in range(self.bullets_in_mag):
            surface.blit(self.bullet, (rnd*self.bullet_rect.width + rnd*self.bullet_spacer,55))
        self.score_label.draw(surface)
        for score in self.clay_scores:
            score.draw(surface)
