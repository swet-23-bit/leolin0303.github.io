import pygame
import random
import sys

pygame.init()
screen_width = 800
screen_height = 300
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("恐龍跳躍遊戲 - 加入方向鍵控制")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 177, 76)

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

class Dino:
    def __init__(self):
        self.width = 40
        self.height = 40
        self.x = 50
        self.y = screen_height - self.height - 20
        self.vel_y = 0
        self.jump = False
        self.speed = 5

    def draw(self):
        pygame.draw.rect(screen, GREEN, (self.x, self.y, self.width, self.height))

    def update(self):
        if self.jump:
            self.vel_y = -12
            self.jump = False
        self.vel_y += 1
        self.y += self.vel_y
        if self.y >= screen_height - self.height - 20:
            self.y = screen_height - self.height - 20
            self.vel_y = 0

    def move_left(self):
        if self.x > 0:
            self.x -= self.speed

    def move_right(self):
        if self.x < screen_width - self.width:
            self.x += self.speed

class Cactus:
    def __init__(self):
        self.width = 20
        self.height = 40
        self.x = screen_width
        self.y = screen_height - self.height - 20
        self.speed = 7

    def draw(self):
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height))

    def update(self):
        self.x -= self.speed

score = 0
high_score = 0

def main():
    global score, high_score
    dino = Dino()
    cactus_list = []
    spawn_timer = 0
    score = 0

    running = True
    while running:
        screen.fill(WHITE)
        pygame.draw.line(screen, BLACK, (0, screen_height - 20), (screen_width, screen_height - 20), 2)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 鍵盤連續偵測
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] and dino.y >= screen_height - dino.height - 20:
            dino.jump = True
        if keys[pygame.K_LEFT]:
            dino.move_left()
        if keys[pygame.K_RIGHT]:
            dino.move_right()

        dino.update()
        dino.draw()

        # 障礙物
        spawn_timer += 1
        if spawn_timer > 60:
            cactus_list.append(Cactus())
            spawn_timer = 0

        for cactus in cactus_list[:]:
            cactus.update()
            cactus.draw()
            if cactus.x + cactus.width < 0:
                cactus_list.remove(cactus)

            if dino.x < cactus.x + cactus.width and dino.x + dino.width > cactus.x:
                if dino.y + dino.height > cactus.y:
                    running = False

        score += 1
        if score > high_score:
            high_score = score
        score_text = font.render(f"分數: {score}", True, BLACK)
        high_text = font.render(f"最高分: {high_score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        screen.blit(high_text, (10, 40))

        pygame.display.flip()
        clock.tick(30)

    game_over()

def game_over():
    global score
    screen.fill(WHITE)
    over_text = font.render("遊戲結束! 按任意鍵重新開始", True, BLACK)
    screen.blit(over_text, (screen_width // 2 - 150, screen_height // 2))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                main()

main()
