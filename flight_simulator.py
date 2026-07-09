import pygame
import sys
import random
import math
import time

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("飛機航班模擬器")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

# 顏色
WHITE = (255, 255, 255)
SKY = (135, 206, 250)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# 城市清單
cities = {
    "台北": (100, HEIGHT - 100),
    "東京": (700, HEIGHT - 400),
    "紐約": (50, 100),
    "倫敦": (600, 80),
    "雪梨": (400, HEIGHT - 50)
}

def draw_text(text, x, y, color=BLACK):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

# 航線選擇
def select_route():
    selecting = True
    city_names = list(cities.keys())
    selected_from = 0
    selected_to = 1

    while selecting:
        screen.fill(SKY)
        draw_text("選擇出發與目的地城市", 250, 50)
        draw_text("↑↓ 出發城市   ←→ 目的地城市   Enter 確定", 150, 90)
        draw_text(f"出發城市: {city_names[selected_from]}", 250, 150, RED)
        draw_text(f"目的地: {city_names[selected_to]}", 250, 200, GREEN)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_from = (selected_from - 1) % len(city_names)
                    if selected_from == selected_to:
                        selected_from = (selected_from - 1) % len(city_names)
                elif event.key == pygame.K_DOWN:
                    selected_from = (selected_from + 1) % len(city_names)
                    if selected_from == selected_to:
                        selected_from = (selected_from + 1) % len(city_names)
                elif event.key == pygame.K_LEFT:
                    selected_to = (selected_to - 1) % len(city_names)
                    if selected_to == selected_from:
                        selected_to = (selected_to - 1) % len(city_names)
                elif event.key == pygame.K_RIGHT:
                    selected_to = (selected_to + 1) % len(city_names)
                    if selected_to == selected_from:
                        selected_to = (selected_to + 1) % len(city_names)
                elif event.key == pygame.K_RETURN:
                    selecting = False

        pygame.display.update()
        clock.tick(30)

    return city_names[selected_from], city_names[selected_to]

# 選擇航線
departure_city, arrival_city = select_route()
departure_pos = cities[departure_city]
arrival_pos = cities[arrival_city]
total_distance = math.hypot(arrival_pos[0] - departure_pos[0], arrival_pos[1] - departure_pos[1])
progress_distance = 0

# 狀態變數
plane = pygame.Rect(departure_pos[0], departure_pos[1], 60, 30)
speed = 0
altitude = 0
fuel = 100
passenger_satisfaction = 100
passenger_count = random.randint(80, 150)
ticket_price = random.randint(300, 800)
extra_income = 0
last_service_time = time.time()

# 儀表板
def draw_dashboard():
    draw_text(f"速度: {int(speed)} km/h", 10, 10)
    draw_text(f"高度: {int(altitude)} m", 10, 40)
    draw_text(f"燃料: {int(fuel)}%", 10, 70)
    draw_text(f"乘客滿意度: {int(passenger_satisfaction)}%", 10, 100)
    draw_text(f"航程進度: {int(progress_ratio * 100)}%", 10, 130)
    draw_text(f"乘客數: {passenger_count}", 10, 160)
    draw_text(f"票價: ${ticket_price}", 10, 190)
    draw_text(f"額外收入: ${int(extra_income)}", 10, 220)

def draw_map():
    for name, pos in cities.items():
        pygame.draw.circle(screen, BLACK, pos, 8)
        draw_text(name, pos[0] + 10, pos[1] - 10)
    pygame.draw.line(screen, RED, departure_pos, arrival_pos, 2)
    draw_text(f"{departure_city} ➜ {arrival_city}", WIDTH - 250, HEIGHT - 40)

def game_over(message):
    revenue = passenger_count * ticket_price * (passenger_satisfaction / 100) + extra_income
    screen.fill(RED)
    draw_text(message, 250, 200, WHITE)
    draw_text(f"乘客數：{passenger_count}", 250, 240, WHITE)
    draw_text(f"票價：${ticket_price}", 250, 270, WHITE)
    draw_text(f"乘客滿意度：{int(passenger_satisfaction)}%", 250, 300, WHITE)
    draw_text(f"機上服務額外收入：${int(extra_income)}", 250, 330, WHITE)
    draw_text(f"總收益：約 ${int(revenue)} 元", 250, 370, WHITE)
    pygame.display.update()
    pygame.time.wait(6000)
    pygame.quit()
    sys.exit()

# 主遊戲
while True:
    screen.fill(SKY)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()

    # 基本控制
    if keys[pygame.K_UP] and fuel > 0:
        speed += 0.5
        fuel -= 0.05
    if keys[pygame.K_DOWN]:
        speed -= 0.5
    if keys[pygame.K_w] and speed > 60:
        altitude += 2
        fuel -= 0.02
    if keys[pygame.K_s]:
        altitude -= 2

    speed = max(0, min(speed, 300))
    altitude = max(0, altitude)

    # 飛行進度與位置更新
    if speed > 0:
        fuel -= 0.01
        progress_distance += speed / 100
    progress_ratio = min(1, progress_distance / total_distance)

    plane.x = int(departure_pos[0] + (arrival_pos[0] - departure_pos[0]) * progress_ratio)
    plane.y = int(departure_pos[1] + (arrival_pos[1] - departure_pos[1]) * progress_ratio)

    # 滿意度變化
    if abs(speed - 150) < 10 and 100 < altitude < 300:
        passenger_satisfaction += 0.05
    elif keys[pygame.K_s] and altitude > 100:
        passenger_satisfaction -= 0.2
    else:
        passenger_satisfaction -= 0.01

    # 長時間無服務會下降
    if time.time() - last_service_time > 30:
        passenger_satisfaction -= 0.1

    # 服務按鍵
    if keys[pygame.K_1] and fuel >= 1:
        passenger_satisfaction += random.uniform(2, 5)
        fuel -= 1
        last_service_time = time.time()
    if keys[pygame.K_2] and fuel >= 0.5:
        passenger_satisfaction += random.uniform(1, 3)
        fuel -= 0.5
        last_service_time = time.time()
    if keys[pygame.K_3]:
        bonus = passenger_count * random.uniform(5, 10)
        extra_income += bonus
        last_service_time = time.time()

    passenger_satisfaction = max(0, min(100, passenger_satisfaction))

    draw_map()
    pygame.draw.rect(screen, BLACK, plane)
    draw_dashboard()

    if progress_ratio >= 1 and altitude <= 0 and speed < 40:
        passenger_satisfaction += 20
        game_over(f"成功降落在 {arrival_city}！")

    if fuel <= 0:
        passenger_satisfaction = 0
        game_over("燃料耗盡！飛機墜毀")

    pygame.display.update()
    clock.tick(60)

