import pygame
import random

pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("公車司機模擬器")
clock = pygame.time.Clock()

# 顏色
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 100, 255)

# 公車
bus_img = pygame.Surface((60, 30))
bus_img.fill(BLUE)
bus_x = 100
bus_y = HEIGHT // 2
speed = 0
fuel = 100
score = 0

# 站牌
stations = [300, 600, 900, 1200, 1500]
station_img = pygame.Surface((20, 50))
station_img.fill(GREEN)

# 加油站
fuel_station_x = 800
fuel_station_img = pygame.Surface((40, 60))
fuel_station_img.fill(RED)

# 捲動
scroll_x = 0

font = pygame.font.SysFont(None, 24)

def draw_text(text, x, y, color=WHITE):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

running = True
while running:
    screen.fill(GRAY)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 控制
    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT]:
        speed = 3
    elif keys[pygame.K_LEFT]:
        speed = -3
    else:
        speed = 0

    bus_x += speed
    scroll_x += speed
    fuel -= 0.05

    # 畫公車
    screen.blit(bus_img, (100, bus_y))

    # 畫站牌
    for station in stations:
        screen.blit(station_img, (station - scroll_x, bus_y + 40))
        if abs((station - scroll_x) - 100) < 5:
            score += 1
            stations.remove(station)

    # 畫加油站
    screen.blit(fuel_station_img, (fuel_station_x - scroll_x, bus_y + 50))
    if abs((fuel_station_x - scroll_x) - 100) < 5:
        fuel = 100

    # 畫資訊欄
    draw_text(f"油量: {int(fuel)}%", 10, 10)
    draw_text(f"乘客數: {score}", 10, 30)

    # 油量耗盡
    if fuel <= 0:
        draw_text("油量耗盡！Game Over", WIDTH // 2 - 80, HEIGHT // 2, RED)
        pygame.display.flip()
        pygame.time.wait(2000)
        running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

