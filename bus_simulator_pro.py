import pygame
import random

pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("公車司機模擬器 加強版")
clock = pygame.time.Clock()

# 顏色
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
ROAD_GRAY = (70, 70, 70)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
YELLOW = (255, 200, 0)
BLUE = (0, 100, 255)
SIDEWALK = (160, 160, 160)

# 字型
font = pygame.font.SysFont(None, 28)

# 公車
bus_img = pygame.Surface((60, 30))
bus_img.fill(BLUE)
bus_y = HEIGHT // 2
fuel = 100
score = 0

# 遊戲狀態
game_state = "menu"
route_type = None

# 地圖資料
stations = []
fuel_station_x = 0
traffic_lights = []
light_state = {}
light_timer = {}
scroll_x = 0
bus_x = 100
speed = 0

def draw_text(text, x, y, color=WHITE):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def init_route(route):
    global stations, fuel_station_x, traffic_lights, light_state, light_timer, scroll_x, fuel, score
    scroll_x = 0
    fuel = 100
    score = 0

    if route == "city":
        stations = [300, 600, 900, 1200, 1500]
        fuel_station_x = 800
        traffic_lights[:] = [400, 700, 1000, 1300]
    elif route == "suburb":
        stations = [500, 1000, 1800]
        fuel_station_x = 1500
        traffic_lights[:] = [900, 1700]

    light_state.clear()
    light_timer.clear()
    for pos in traffic_lights:
        light_state[pos] = "green"
        light_timer[pos] = 0

def draw_background():
    screen.fill(GREEN)  # 草地背景
    pygame.draw.rect(screen, SIDEWALK, (0, HEIGHT//2 - 60, WIDTH, 120))  # 人行道
    pygame.draw.rect(screen, ROAD_GRAY, (0, HEIGHT//2 - 40, WIDTH, 80))   # 馬路

    # 畫道路虛線
    for i in range(0, WIDTH, 40):
        pygame.draw.line(screen, WHITE, (i, HEIGHT//2), (i+20, HEIGHT//2), 2)

def draw_game():
    global scroll_x, fuel, score
    draw_background()

    # 畫站牌
    station_img = pygame.Surface((20, 50))
    station_img.fill(GREEN)
    for station in stations[:]:
        screen.blit(station_img, (station - scroll_x, bus_y + 40))
        if abs((station - scroll_x) - 100) < 5:
            score += 1
            stations.remove(station)

    # 畫加油站
    fuel_station_img = pygame.Surface((40, 60))
    fuel_station_img.fill(RED)
    screen.blit(fuel_station_img, (fuel_station_x - scroll_x, bus_y + 50))
    if abs((fuel_station_x - scroll_x) - 100) < 5:
        fuel = 100

    # 畫紅綠燈
    for pos in traffic_lights:
        light_timer[pos] += 1
        if light_state[pos] == "green" and light_timer[pos] > 180:
            light_state[pos] = "yellow"
            light_timer[pos] = 0
        elif light_state[pos] == "yellow" and light_timer[pos] > 60:
            light_state[pos] = "red"
            light_timer[pos] = 0
        elif light_state[pos] == "red" and light_timer[pos] > 180:
            light_state[pos] = "green"
            light_timer[pos] = 0

        pygame.draw.rect(screen, GRAY, (pos - scroll_x, bus_y - 60, 20, 60))
        if light_state[pos] == "green":
            pygame.draw.circle(screen, GREEN, (pos - scroll_x + 10, bus_y - 50), 8)
        elif light_state[pos] == "yellow":
            pygame.draw.circle(screen, YELLOW, (pos - scroll_x + 10, bus_y - 35), 8)
        elif light_state[pos] == "red":
            pygame.draw.circle(screen, RED, (pos - scroll_x + 10, bus_y - 20), 8)

        # 違規檢查
        if light_state[pos] == "red":
            if pos - scroll_x - 100 < 0 and pos - scroll_x - 100 > -3:
                score -= 2
                fuel -= 10
                draw_text("闖紅燈！-2 分", WIDTH//2 - 60, HEIGHT//2, RED)

    # 畫公車
    screen.blit(bus_img, (100, bus_y))

    # 畫資訊
    draw_text(f"油量: {int(fuel)}%", 10, 10)
    draw_text(f"乘客數: {score}", 10, 40)

def main_menu():
    screen.fill(GRAY)
    draw_text("公車司機模擬器", WIDTH//2 - 100, HEIGHT//2 - 80, WHITE)
    draw_text("1. 市區線 (紅綠燈多)", WIDTH//2 - 120, HEIGHT//2 - 20, WHITE)
    draw_text("2. 郊區線 (距離長)", WIDTH//2 - 120, HEIGHT//2 + 20, WHITE)
    draw_text("按數字鍵選擇路線", WIDTH//2 - 100, HEIGHT//2 + 60, WHITE)

running = True
while running:
    if game_state == "menu":
        main_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    route_type = "city"
                    init_route("city")
                    game_state = "play"
                elif event.key == pygame.K_2:
                    route_type = "suburb"
                    init_route("suburb")
                    game_state = "play"

    elif game_state == "play":
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

        bus_x += speed
        scroll_x += speed
        fuel -= 0.05

        draw_game()

        if fuel <= 0:
            draw_text("油量耗盡！Game Over", WIDTH // 2 - 80, HEIGHT // 2, RED)
            pygame.display.flip()
            pygame.time.wait(2000)
            game_state = "menu"

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

