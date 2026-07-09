import pygame
import random

pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("公車司機模擬器 - 紅綠燈版")
clock = pygame.time.Clock()

# 顏色
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
YELLOW = (255, 200, 0)
BLUE = (0, 100, 255)

# 公車
bus_img = pygame.Surface((60, 30))
bus_img.fill(BLUE)
bus_y = HEIGHT // 2
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

# 紅綠燈
traffic_lights = [500, 1100, 1700]
light_state = {}  # 存紅綠燈狀態
light_timer = {}
for pos in traffic_lights:
    light_state[pos] = "green"  # 初始綠燈
    light_timer[pos] = 0

# 捲動
scroll_x = 0
bus_x = 100
speed = 0

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

    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT]:
        speed = 3
    elif keys[pygame.K_LEFT]:
        speed = -3
    else:
        speed = 0

    # 更新位置與油量
    bus_x += speed
    scroll_x += speed
    fuel -= 0.05

    # 畫公車
    screen.blit(bus_img, (100, bus_y))

    # 畫站牌
    for station in stations[:]:
        screen.blit(station_img, (station - scroll_x, bus_y + 40))
        if abs((station - scroll_x) - 100) < 5:
            score += 1
            stations.remove(station)

    # 畫加油站
    screen.blit(fuel_station_img, (fuel_station_x - scroll_x, bus_y + 50))
    if abs((fuel_station_x - scroll_x) - 100) < 5:
        fuel = 100

    # 畫紅綠燈 & 更新狀態
    for pos in traffic_lights:
        light_timer[pos] += 1
        if light_state[pos] == "green" and light_timer[pos] > 180:  # 綠燈 3 秒
            light_state[pos] = "yellow"
            light_timer[pos] = 0
        elif light_state[pos] == "yellow" and light_timer[pos] > 60:  # 黃燈 1 秒
            light_state[pos] = "red"
            light_timer[pos] = 0
        elif light_state[pos] == "red" and light_timer[pos] > 180:  # 紅燈 3 秒
            light_state[pos] = "green"
            light_timer[pos] = 0

        # 畫紅綠燈柱
        pygame.draw.rect(screen, GRAY, (pos - scroll_x, bus_y - 60, 20, 60))
        if light_state[pos] == "green":
            pygame.draw.circle(screen, GREEN, (pos - scroll_x + 10, bus_y - 50), 8)
        elif light_state[pos] == "yellow":
            pygame.draw.circle(screen, YELLOW, (pos - scroll_x + 10, bus_y - 35), 8)
        elif light_state[pos] == "red":
            pygame.draw.circle(screen, RED, (pos - scroll_x + 10, bus_y - 20), 8)

        # 違規檢查（紅燈通過）
        if light_state[pos] == "red":
            if pos - scroll_x - 100 < 0 and pos - scroll_x - 100 > -3:  
                score -= 2
                fuel -= 10
                draw_text("闖紅燈！-2 分", WIDTH//2 - 60, HEIGHT//2, RED)

    # 畫資訊欄
    draw_text(f"油量: {int(fuel)}%", 10, 10)
    draw_text(f"乘客數: {score}", 10, 30)

    if fuel <= 0:
        draw_text("油量耗盡！Game Over", WIDTH // 2 - 80, HEIGHT // 2, RED)
        pygame.display.flip()
        pygame.time.wait(2000)
        running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

