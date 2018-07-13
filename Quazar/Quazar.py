""" QUAZAR - a game for LACC :) by: Paul Martin """ # --- imports --- import pygame import time import random
from __future__ import division
import pygame
import time
import random
import sys
import serial
from MbedReceiver import *


print("""
=======================================
          QUAZAR  -  LACC  
=======================================
""")

team1_id = int( input("Team 1 ID: ") )
team2_id = int( input("Team 2 ID: ") )

# --- initialize game ---
pygame.init()
pygame.display.set_caption('Quazar')
pygame.font.init()
font = pygame.font.Font(pygame.font.get_default_font(),24)
finalfont = pygame.font.Font(pygame.font.get_default_font(),48)
screenW=1024
screenH=720
screen=pygame.display.set_mode((screenW,screenH))
pygame.mixer.init()

# --- background ---
starimg=pygame.image.load ("data/star_text.jpg").convert()
star=pygame.transform.scale (starimg,(screenW,screenH))

# --- load sounds ---
laser=pygame.mixer.Sound("data/laser.wav")
ex=pygame.mixer.Sound("data/ex.wav")
music=pygame.mixer.Sound("data/music.wav")
exp = pygame.mixer.Sound("data/exp.wav")
missile = pygame.mixer.Sound("data/missile.wav")
breakglass = pygame.mixer.Sound("data/breaking.wav")

# --- misc. variables ---
game_done=False
left_boundary = 100
right_boundary = screenW - 40
shield_time = 30
idle_time = 10
max_ammo = 15  # was 15
max_bombs = 3  # was 3
max_health = 12
max_reloading_time = 20
losers = 0
alpha_move = 0.10
time_now = 0
time_last = 0
pps_penalty = 100

# --- command types ---
CMD_TYPE_MOVE = 0
CMD_TYPE_MISSILE = 1
CMD_TYPE_BOMB = 2
CMD_TYPE_RELOADMISSILE = 3
CMD_TYPE_RELOADBOMB = 4


# --- RECTANGLE CLASS FOR COLLISION DETECTION ---
class Rectangle:
        def __init__(self,x,y,width,height):
                self.left = x
                self.top = y
                self.bottom = y+height
                self.right = x+width

def rectangular_intersection(rect1,rect2):
        return not (rect1.right < rect2.left or rect1.left > rect2.right or rect1.bottom < rect2.top or rect1.top > rect2.bottom)

# --- GENERIC SPRITE CLASS ---
class Sprite:
        def __init__(self,image_path):
                self.x=0
                self.y=0
                self.speedx=0
                self.speedy=0
                self.image=pygame.image.load(image_path)
                self.image=pygame.transform.scale(self.image,(30,30))
                self.width=30
                self.height=30
        def update(self):
                self.x += self.speedx
                self.y += self.speedy


# --- PLAYER SPRITE CLASS (SHIP) ---
class Player(Sprite):

        def __init__(self,team):
                self.team = team
                self.player = True

                if team == 1:
                    Sprite.__init__(self,"data/ship_1.png")
                    self.image=pygame.transform.scale(self.image,(30,30))
                    self.x=screenW/2 - 200
                    self.y=screenH-60
                    self.width =30
                    self.height=30
                    self.speedx=0
                    self.speedy=0
                else:
                    Sprite.__init__(self,"data/ship_2.png")
                    self.image=pygame.transform.scale(self.image,(30,30))
                    self.x=screenW/2 + 200
                    self.y=0+40
                    self.width =30
                    self.height=30
                    self.speedx=0
                    self.speedy=0

                # state
                self.reloadingammo=False
                self.reloadingtime = max_reloading_time
                self.reloadingbomb=False
                self.ammo=max_ammo
                self.bombs=max_bombs
                self.shielded=False
                self.shieldtime = 0
                self.health = max_health
                self.pps = 0
                self.packets = 0
                self.penalized = False

        def setposition(self,perc):
            # filter position
            if not self.penalized:
                x_desired = left_boundary + perc*(right_boundary-left_boundary)
                x_now = self.x
                self.x = (1-alpha_move)*x_now + (alpha_move)*x_desired

        def nudgeleft(self):
            self.x -= 30

        def nudgeright(self):
            self.x += 30

        def reloadammo(self):
            self.ammo = 0
            self.reloadingtime = max_reloading_time
            self.reloadingammo = True
            self.reloadingbomb = False

        def reloadbomb(self):
            self.bombs = 0
            self.reloadingtime = max_reloading_time
            self.reloadingammo = False
            self.reloadingbomb = True

        def firebullet(self):
            if self.ammo > 0:
                bullet = Bullet(self.team)
                sprite_list.append(bullet)
                bullet.x=self.x+8
                if self.team == 1:
                    bullet.y=self.y-15
                else:
                    bullet.y=self.y+25
                self.ammo -= 1

        def firebomb(self):
            if self.bombs > 0:
                bomb = Bomb(self.team)
                sprite_list.append(bomb)
                bomb.x=self.x-10
                if self.team == 1:
                    bomb.y=self.y-30
                else:
                    bomb.y=self.y+20
                self.bombs -= 1

        def pps_penalize(self):
            self.penalized = True

        def pps_clear(self):
            self.penalized = False


        def update(self):
                global game_done, losers

                if self.x < left_boundary:
                        self.x = left_boundary
                if self.x > right_boundary:
                        self.x = right_boundary

                # reload timers
                if self.reloadingammo or self.reloadingbomb:
                    self.reloadingtime -= 1

                if self.reloadingtime <= 0:
                    self.reloadingtime = max_reloading_time
                    if self.reloadingammo:
                        self.reloadingammo = False
                        self.ammo = max_ammo
                    if self.reloadingbomb:
                        self.reloadingbomb = False
                        self.bombs = max_bombs

                # check to see if projectile has hit us
                for sprite in sprite_list:
                        if sprite != self and hasattr(sprite,"bullet") and sprite.team != self.team:
                                self_rectangle = Rectangle(self.x,self.y,self.width,self.height)
                                other_rectangle=Rectangle(sprite.x,sprite.y,sprite.width,sprite.height)
                                if rectangular_intersection(self_rectangle,other_rectangle):
                                    breakglass.play()
                                    self.health -= 1
                                    if self.health <= 0:
                                        # game is over!
                                        self.health = 0
                                        game_done = True
                                        losers = self.team
                                    # kill the bullet
                                    sprite_list.remove(sprite)
                        if sprite != self and hasattr(sprite,"bomb") and sprite.team != self.team:
                                self_rectangle = Rectangle(self.x,self.y,self.width,self.height)
                                other_rectangle=Rectangle(sprite.x,sprite.y,sprite.width,sprite.height)
                                if rectangular_intersection(self_rectangle,other_rectangle):
                                    exp.play()
                                    self.health -= 3
                                    if self.health <= 0:
                                        # game is over!
                                        self.health = 0
                                        game_done = True
                                        losers = self.team
                                    # kill the bomb
                                    sprite_list.remove(sprite)


class Bullet(Sprite):
        def __init__(self, team):
                Sprite.__init__(self,"data/b.png")
                self.image=pygame.transform.scale(self.image,(13,24))
                self.width=13
                self.height=24
                self.bullet = True
                self.team = team
                laser.play()

        def update(self):
                kill_list = []
                self_rectangle = Rectangle(self.x,self.y,self.width,self.height)
                for sprite in sprite_list:
                        if hasattr(sprite,"bullet") and not sprite == self:
                                other_rectangle=Rectangle(sprite.x,sprite.y,sprite.width,sprite.height)
                                if rectangular_intersection(self_rectangle,other_rectangle):
                                        kill_list.append(sprite)
                                        if self not in kill_list:
                                                kill_list.append(self)

                if self.y < 0 or self.y > screenH:
                        kill_list.append(self)
                for sprite in kill_list:
                        if sprite in sprite_list:
                                sprite_list.remove(sprite)
                if self.team == 1:
                    self.y-=40
                else:
                    self.y+=40


class Bomb(Sprite):
        def __init__(self, team):
                Sprite.__init__(self,"data/bomb.png")
                self.image=pygame.transform.scale(self.image,(50,50))
                self.width=50
                self.height=50
                self.bomb = True
                self.team = team
                missile.play()

        def update(self):
                kill_list = []
                self_rectangle = Rectangle(self.x,self.y,self.width,self.height)


                for sprite in sprite_list:
                        # explode on any bomb
                        if hasattr(sprite,"bomb") and not sprite == self and self.team != sprite.team:
                            other_rectangle=Rectangle(sprite.x,sprite.y,sprite.width,sprite.height)
                            if rectangular_intersection(self_rectangle,other_rectangle):
                                kill_list.append(self)
                                kill_list.append(sprite)
                                exp.play()

                        # destroy any bullets
                        if hasattr(sprite,"bullet") and not sprite == self and self.team != sprite.team:
                            other_rectangle=Rectangle(sprite.x,sprite.y,sprite.width,sprite.height)
                            if rectangular_intersection(self_rectangle,other_rectangle):
                                    kill_list.append(sprite)
                                    exp.play()

                        # hurt players
                        if hasattr(sprite,"player") and self.team != sprite.team:
                            other_rectangle=Rectangle(sprite.x,sprite.y,sprite.width,sprite.height)
                            if rectangular_intersection(self_rectangle,other_rectangle):
                                    kill_list.append(self)
                                    exp.play()


                if self.y < 0 or self.y > screenH:
                        kill_list.append(self)

                for sprite in kill_list:
                        if sprite in sprite_list:
                                sprite_list.remove(sprite)

                if self.team == 1:
                    self.y-=30
                else:
                    self.y+=30


def draw_frame(alist):
        global game_done, time_last, time_now


        # draw background
        pygame.draw.rect(screen,(0,0,0),screen.get_rect())
        screen.blit(star,(0,0))

        # draw remaining health
        perc_1 = player1.health/max_health
        perc_2 = player2.health/max_health
        len_1 = round(200*perc_1)
        len_2 = round(200*perc_2)
        pygame.draw.rect(screen, (255,100,100), (50, 50+(200-len_2) , 30, len_2), 0)
        pygame.draw.rect(screen, (255,100,100), (50, screenH-50-len_1, 30, len_1), 0)
        pygame.draw.rect(screen, (255,0,0), (50,50,30,200), 2)
        pygame.draw.rect(screen, (255,0,0), (50,screenH-50-200,30,200), 2)

        # update sprites
        for sprite in alist:
                position = (sprite.x,sprite.y)
                screen.blit(sprite.image,position)

        # reloading text
        for sprite in alist:
            if hasattr(sprite,"player"):
                if sprite.reloadingammo:
                    reloads = "Reloading Ammo"
                    reloadm = font.render(reloads, True, (255, 100, 100))
                    if sprite.team == 1:
                        screen.blit(reloadm, (screenW/2-50, screenH-20) )
                    else:
                        screen.blit(reloadm, (screenW/2-50, 20) )

                if sprite.reloadingbomb:
                    reloads = "Reloading Bomb"
                    reloadm = font.render(reloads, True, (255, 100, 100))
                    if sprite.team == 1:
                        screen.blit(reloadm, (screenW/2-50, screenH-20) )
                    else:
                        screen.blit(reloadm, (screenW/2-50, 20) )

        # packets per second
        time_now = pygame.time.get_ticks()
        delta = time_now - time_last
        if delta >= 1000:
            player1.pps = player1.packets
            player1.packets = 0
            player2.pps = player2.packets
            player2.packets = 0
            time_last = pygame.time.get_ticks()

            # pps penalty
            if player1.pps > pps_penalty:
                player1.pps_penalize()
            else:
                player1.pps_clear()

            if player2.pps > pps_penalty:
                player2.pps_penalize()
            else:
                player2.pps_clear()

        pps1_s = str(player1.pps) + " PPS"
        pps2_s = str(player2.pps) + " PPS"
        color_good = (100,255,100)
        color_bad = (255, 0, 0)
        if player1.pps < pps_penalty:
            pps1_m = font.render(pps1_s, True, color_good)
        else:
            pps1_m = font.render(pps1_s, True, color_bad)

        if player2.pps < pps_penalty:
            pps2_m = font.render(pps2_s, True, color_good)
        else:
            pps2_m = font.render(pps2_s, True, color_bad)

        screen.blit(pps1_m, (45, screenH-50-200-25))
        screen.blit(pps2_m, (45, 50+200+5))

        if game_done:
            global losers
            finals = "Team " + str(losers) + " has perished!"
            finalm = finalfont.render(finals, True, (255,255,255))
            screen.blit(finalm,(screenW/2 - 200,screenH/2-50))

        pygame.display.flip()

def update_sprites():
        for sprite in sprite_list:
                sprite.update()

sprite_list = []

print ("BEGIN\n")

# --- initialize players ---
player1 = Player(1)
player2 = Player(2)
sprite_list.append(player1)
sprite_list.append(player2)

# --- fire up the music ---
music.play()
#channel=music.play()

# --- init. last time ---
time_last = pygame.time.get_ticks()

# --- handle wireless commands ---
def handlecommands(tid, cmd, val):

    # update PPS stats
    if tid == team1_id:
        player1.packets += 1
    elif tid == team2_id:
        player2.packets += 1

    if cmd == CMD_TYPE_MOVE:
        if tid == team1_id:
            player1.setposition(val/255.0)
        elif tid == team2_id:
            player2.setposition(val/255.0)
    elif cmd == CMD_TYPE_MISSILE:
        if tid == team1_id:
            player1.firebullet()
        elif tid == team2_id:
            player2.firebullet()
    elif cmd == CMD_TYPE_BOMB:
        if tid == team1_id:
            player1.firebomb()
        elif tid == team2_id:
            player2.firebomb()
    elif cmd == CMD_TYPE_RELOADMISSILE:
        if tid == team1_id:
            player1.reloadammo()
        elif tid == team2_id:
            player2.reloadammo()
    elif cmd == CMD_TYPE_RELOADBOMB:
        if tid == team1_id:
            player1.reloadbomb()
        elif tid == team2_id:
            player2.reloadbomb()

# --- load mbed reader ---
mbed = MbedReceiver(115200, handlecommands)
mbed.start()

# --- fire up the game ---
while not game_done:

        # keep that music playing
        #if not channel.get_busy():
        #        pass
		#  channel=music.play()

        # check wireless for incoming commands
        # TODO: ---

        # also check keyboard for testing
        for event in pygame.event.get():
                # key press
                if event.type == pygame.KEYDOWN:
                    # player 1
                        if event.key == pygame.K_q:
                                player1.firebullet()
                        if event.key == pygame.K_w:
                                player1.firebomb()
                        if event.key==pygame.K_a:
                                player1.nudgeleft()
                        if event.key==pygame.K_d:
                                player1.nudgeright()
                        if event.key==pygame.K_e:
                                player1.reloadammo()
                        if event.key==pygame.K_r:
                                player1.reloadbomb()

                    # player 2
                        if event.key == pygame.K_j:
                            player2.nudgeleft()
                        if event.key == pygame.K_l:
                            player2.nudgeright()
                        if event.key == pygame.K_u:
                            player2.firebullet()
                        if event.key == pygame.K_i:
                            player2.firebomb()
                        if event.key == pygame.K_o:
                            player2.reloadammo()
                        if event.key == pygame.K_p:
                            player2.reloadbomb()

                # check for UI exit
                if event.type == pygame.QUIT:
                        game_done=True
                if game_done is True:
                        break

        draw_frame(sprite_list)
        update_sprites()



# --- game is over, display results ---
draw_frame(sprite_list)

end = None
while end != "0":
    end = input("Enter 0 to quit: ")
		# if end == "0":
    pygame.quit()
    sys.exit()
    break
print("END")
quit
