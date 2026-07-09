"""
公車司機模擬器 - 完整加強版
功能：
- 主選單：選擇地圖（市區 / 郊區 / 山區）與模式（正常 / 自由駕駛）
- 每張地圖有站牌、加油站、紅綠燈
- GPS 小地圖（右上角）顯示重要物件
- 自由駕駛模式：油量無限、不計分
- 紅綠燈與違規罰則（正常模式）
Controls:
- 右/左方向鍵：前進/後退
- Esc：回到主選單 / 離開
- P：暫停
"""

import pygame
import random
import math

pygame.init()
WIDTH, HEIGHT = 960, 640  # 稍微放大視窗方便 GPS 顯示
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("公車司機模擬器 - 完整版")
clock = pygame.time.Clock()

# ---------- 顏色 ----------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (120, 120, 120)
ROAD_GRAY = (70, 70, 70)
SIDEWALK = (160, 160, 160)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
YELLOW = (255, 200, 0)
BLUE = (30, 120, 220)
DARK_GREEN = (30, 160, 60)
BROWN = (140, 100, 60)

# ---------- 字型 ----------
font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 48)

# ---------- 公車 ----------
BUS_W, BUS_H = 80, 36
bus_img = pygame.Surface((BUS_W, BUS_H), pygame.SRCALPHA)
pygame.draw.rect(bus_img, BLUE, (0, 0, BUS_W, BUS_H), border_radius=6)
pygame.draw.rect(bus_img, (220, 220, 255), (8, 6, BUS_W-16, BUS_H-18))  # 車窗
bus_y = HEIGHT // 2
# bus x is fixed on screen (camera follows world), world offset controlled by scroll_x
BUS_SCREEN_X = 200  # 在視窗上的固定 x
bus_world_x = 100.0

# ---------- 遊戲狀態 ----------
game_state = "menu"   # menu, play, paused
route_choice = None   # "city", "suburb", "mountain"
mode_choice = "normal"  # normal or free

# ---------- 世界 / 地圖資料 ---------- 
# Each map: world_length, stations(list of x), traffic_lights(list of x), fuel_stations(list of x), optional hills
maps = {
    "city": {
        "length": 1800,
        "stations": [300, 450, 600, 760, 900, 1050, 1200, 1350, 1500],
        "lights": [380, 720, 980, 1280, 1460],
        "fuels": [800, 1400],
        "hills": []  # no hills
    },
    "suburb": {
        "length": 2800,
        "stations": [500, 900, 1300, 1900, 2300],
        "lights": [1200, 2100],
        "fuels": [1500, 2600],
        "hills": []
    },
    "mountain": {
        "length": 2400,
        "stations": [400, 900, 1300, 1700, 2100],
        "lights": [1100, 1900],
        "fuels": [1000, 2000],
        # hills as tuples (start_x, end_x, slope_factor) slope_factor positive = uphill then downhill
        "hills": [(600, 850, 0.6), (1400, 1650, 0.8)]
    }
}

# Active map data (will be filled when route selected)
world_length = 2000
stations = []
lights = []
fuel_stations = []
hills = []

# light state trackers
light_state = {}
light_timer = {}

# scrolling / camera
scroll_x = 0.0

# gameplay variables
speed = 0.0  # current speed applied to world (affects scroll)
fuel = 100.0
score = 0
free_mode = False

# GPS / mini map
MINIMAP_W, MINIMAP_H = 220, 120
MINIMAP_PADDING = 12
minimap_surface = pygame.Surface((MINIMAP_W, MINIMAP_H))

# helper draw text
def draw_text(s, x, y, color=WHITE, fontobj=font):
    surf = fontobj.render(s, True, color)
    screen.blit(surf, (x, y))

# initialize route data
def init_route(route, mode="normal"):
    global world_length, stations, lights, fuel_stations, hills
    global light_state, light_timer, scroll_x, bus_world_x, fuel, score, free_mode
    cfg = maps[route]
    world_length = cfg["length"]
    stations = cfg["stations"][:]
    lights = cfg["lights"][:]
    fuel_stations = cfg["fuels"][:]
    hills = cfg["hills"][:]
    light_state.clear()
    light_timer.clear()
    for p in lights:
        light_state[p] = "green"
        light_timer[p] = 0
    scroll_x = 0.0
    bus_world_x = 100.0
    fuel = 100.0
    score = 0
    free_mode = (mode == "free")

# draw background (grass / sidewalk / road)
def draw_background():
    # fill ground depending on map
    if route_choice == "mountain":
        screen.fill((90, 140, 90))  # greenish
    else:
        screen.fill(DARK_GREEN)

    # sidewalk strip: center portion
    road_top = HEIGHT // 2 - 60
    road_height = 120
    # draw long road across width (we will later draw world objects with offset)
    pygame.draw.rect(screen, SIDEWALK, (0, road_top, WIDTH, road_height))
    pygame.draw.rect(screen, ROAD_GRAY, (0, road_top + 20, WIDTH, road_height - 40))

    # dashed center line
    dash_w = 30
    gap = 20
    center_y = road_top + road_height // 2
    for x in range(0, WIDTH, dash_w + gap):
        pygame.draw.line(screen, WHITE, (x, center_y), (x + dash_w, center_y), 3)

# draw world objects with scroll offset (world_x - scroll_x => screen_x)
def world_to_screen(wx):
    return int(wx - scroll_x + BUS_SCREEN_X - bus_world_x)

def draw_world():
    global score, fuel
    draw_background()

    # hills (mountain map) draw as colored areas to give hill feel
    for h in hills:
        hx1, hx2, slope = h
        # create a polygon representing a hill
        sx1 = world_to_screen(hx1) - 200
        sx2 = world_to_screen(hx2) + 200
        base_y = HEIGHT // 2 - 40
        hill_color = BROWN
        points = [(sx1, HEIGHT), (sx1 + (sx2 - sx1)//2, base_y - int(slope*200)), (sx2, HEIGHT)]
        pygame.draw.polygon(screen, hill_color, points)

    # draw stations
    for s in stations[:]:
        sx = world_to_screen(s)
        if -100 < sx < WIDTH + 100:
            # sign
            pygame.draw.rect(screen, GREEN, (sx-10, HEIGHT//2 + 40, 20, 50))
            draw_text("站", sx - 8, HEIGHT//2 + 44, BLACK)
        # auto-stop detection
        if abs(s - bus_world_x) < 8 and abs(world_to_screen(s) - BUS_SCREEN_X) < 6:
            score += 1
            try:
                stations.remove(s)
            except ValueError:
                pass

    # draw fuel stations
    for fpos in fuel_stations:
        fx = world_to_screen(fpos)
        if -100 < fx < WIDTH + 100:
            pygame.draw.rect(screen, RED, (fx-20, HEIGHT//2 + 46, 40, 40))
            draw_text("GAS", fx-18, HEIGHT//2 + 48, BLACK)
        if abs(fpos - bus_world_x) < 8 and abs(world_to_screen(fpos) - BUS_SCREEN_X) < 6:
            fuel = 100.0

    # draw red/green lights
    for lpos in lights:
        lx = world_to_screen(lpos)
        if -100 < lx < WIDTH + 100:
            pygame.draw.rect(screen, GRAY, (lx-6, HEIGHT//2 - 90, 12, 60))
            state = light_state.get(lpos, "green")
            if state == "green":
                pygame.draw.circle(screen, GREEN, (lx, HEIGHT//2 - 80), 6)
            elif state == "yellow":
                pygame.draw.circle(screen, YELLOW, (lx, HEIGHT//2 - 68), 6)
            elif state == "red":
                pygame.draw.circle(screen, RED, (lx, HEIGHT//2 - 56), 6)

        # if red and crossing -> violation
        if light_state.get(lpos) == "red":
            # detect when bus crosses the light location
            if (bus_world_x < lpos and bus_world_x + (scroll_x - scroll_x) >= lpos) or False:
                # not used because bus_world_x used for detection below on screen
                pass

    # draw bus at fixed screen x
    screen.blit(bus_img, (BUS_SCREEN_X - BUS_W//2, HEIGHT//2 - BUS_H//2))

    # HUD
    draw_text(f"模式: {'自由駕駛' if free_mode else '正常'}", 12, 12)
    draw_text(f"地圖: {route_choice}", 12, 36)
    if not free_mode:
        draw_text(f"油量: {int(fuel)}%", 12, 60)
        draw_text(f"乘客數: {score}", 12, 84)
    else:
        draw_text("自由駕駛：油量無限，無計分", 12, 60)

# update traffic lights timers and detect red-light violations
def update_lights_and_check_violations(delta_ms):
    global score, fuel
    # timer increments are in frames; convert delta_ms to frames ~ 60fps baseline
    for pos in lights:
        light_timer[pos] = light_timer.get(pos, 0) + 1
        state = light_state.get(pos, "green")
        # cycles: green ~180 frames(3s), yellow ~60 (1s), red ~180 (3s)
        if state == "green" and light_timer[pos] > 180:
            light_state[pos] = "yellow"
            light_timer[pos] = 0
        elif state == "yellow" and light_timer[pos] > 60:
            light_state[pos] = "red"
            light_timer[pos] = 0
        elif state == "red" and light_timer[pos] > 180:
            light_state[pos] = "green"
            light_timer[pos] = 0

        # violation: if the bus is roughly at the crossing and light is red while moving forward
        screen_lx = world_to_screen(pos)
        # detect crossing moment when bus is near signal line (in front of bus)
        if abs(screen_lx - BUS_SCREEN_X) < 8 and light_state[pos] == "red":
            if not free_mode:
                # punish once: reduce score and fuel and show message
                score -= 2
                fuel -= 10
                # Put a center message
                draw_text("闖紅燈！-2 分 -10% 油量", WIDTH//2 - 160, HEIGHT//2 - 120, RED)

# draw minimap
def draw_minimap():
    minimap_surface.fill((40, 40, 40))
    # draw border
    pygame.draw.rect(minimap_surface, (200, 200, 200), (0, 0, MINIMAP_W, MINIMAP_H), 2)
    # world scale mapping
    map_len = world_length
    if map_len <= 0:
        map_len = 1
    sx = 8
    sy = 8
    sw = MINIMAP_W - 2*sx
    sh = MINIMAP_H - 2*sy

    # draw base line
    pygame.draw.rect(minimap_surface, (80, 80, 80), (sx, sy + sh//3, sw, sh//3))
    # draw stations as small green rects
    for s in (stations + maps[route_choice]["stations"]):
        # show also removed stations positions (from initial list) by using map's original station list
        # clamp to map length
        if 0 <= s <= map_len:
            px = sx + int((s / map_len) * sw)
            pygame.draw.rect(minimap_surface, GREEN, (px-3, sy + sh//3 - 6, 6, 6))
    # draw lights
    for l in maps[route_choice]["lights"]:
        if 0 <= l <= map_len:
            px = sx + int((l / map_len) * sw)
            pygame.draw.rect(minimap_surface, YELLOW, (px-2, sy + sh//3 - 14, 4, 8))

    # draw fuel stations
    for f in maps[route_choice]["fuels"]:
        if 0 <= f <= map_len:
            px = sx + int((f / map_len) * sw)
            pygame.draw.rect(minimap_surface, RED, (px-3, sy + sh//3 + 8, 6, 6))

    # draw bus position
    bx = max(0, min(map_len, int(bus_world_x)))
    px = sx + int((bx / map_len) * sw)
    pygame.draw.polygon(minimap_surface, BLUE, [(px, sy + sh//3 + 16), (px-6, sy + sh//3 + 26), (px+6, sy + sh//3 + 26)])

    # blit minimap to screen (top-right)
    screen.blit(minimap_surface, (WIDTH - MINIMAP_W - MINIMAP_PADDING, MINIMAP_PADDING))

# ---------- 主選單繪製 ----------
def main_menu_draw(selected_route=None, selected_mode=None):
    screen.fill(GRAY)
    draw_text("公車司機模擬器 - 完整版", WIDTH//2 - 260, 60, WHITE, big_font)
    draw_text("按 1：市區線（紅綠燈多、站牌多）", WIDTH//2 - 220, 170)
    draw_text("按 2：郊區線（距離長、紅綠燈少）", WIDTH//2 - 220, 210)
    draw_text("按 3：山區線（有坡道、坡度影響速度）", WIDTH//2 - 220, 250)
    draw_text("按 F：自由駕駛模式（油量無限）", WIDTH//2 - 220, 300)
    draw_text("按 N：正常模式（有油量與計分）", WIDTH//2 - 220, 340)
    draw_text("選擇地圖後按空白鍵開始遊戲 (或 Esc 離開)", WIDTH//2 - 220, 420)
    # show current selections
    draw_text(f"目前選擇地圖: {selected_route}", WIDTH//2 - 220, 460)
    draw_text(f"目前選擇模式: {selected_mode}", WIDTH//2 - 220, 490)

# ---------- 主迴圈 ----------
running = True
selected_route = None
selected_mode = "normal"
paused = False

while running:
    dt = clock.tick(60)  # ms since last frame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_state == "menu":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_route = "city"
                elif event.key == pygame.K_2:
                    selected_route = "suburb"
                elif event.key == pygame.K_3:
                    selected_route = "mountain"
                elif event.key == pygame.K_f:
                    selected_mode = "free"
                elif event.key == pygame.K_n:
                    selected_mode = "normal"
                elif event.key == pygame.K_SPACE and selected_route:
                    # start game
                    route_choice = selected_route
                    mode_choice = selected_mode
                    init_route(route_choice, mode_choice)
                    game_state = "play"
                elif event.key == pygame.K_ESCAPE:
                    running = False
        elif game_state == "play":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # back to menu
                    game_state = "menu"
                    selected_route = None
                    selected_mode = "normal"
                elif event.key == pygame.K_p:
                    paused = not paused

    if game_state == "menu":
        main_menu_draw(selected_route, selected_mode)
    elif game_state == "play":
        if paused:
            draw_text("已暫停 (P 切換) - Esc 回主選單", WIDTH//2 - 160, HEIGHT//2 - 30)
            pygame.display.flip()
            continue

        # controls
        keys = pygame.key.get_pressed()
        forward = keys[pygame.K_RIGHT]
        backward = keys[pygame.K_LEFT]

        # base speed
        base_speed = 3.5
        # mountain slope effects
        slope_factor = 1.0
        if route_choice == "mountain":
            # if bus in hill region, apply slope slow down/up by checking hills list
            for h in hills:
                hx1, hx2, s_factor = h
                if hx1 <= bus_world_x <= hx2:
                    # uphill (approximated): reduce effective speed when moving forward
                    slope_factor = max(0.4, 1.0 - s_factor*0.5)
                    break

        if forward and not backward:
            speed = base_speed * slope_factor
        elif backward and not forward:
            speed = -2.0  # slower reverse
        else:
            speed = 0.0

        # update world position
        # moving forward increases world coordinate of bus
        bus_world_x += speed
        # clamp
        if bus_world_x < 0:
            bus_world_x = 0
        if bus_world_x > world_length:
            bus_world_x = world_length

        # update scroll to keep bus at BUS_SCREEN_X
        scroll_x = bus_world_x - BUS_SCREEN_X

        # fuel consumption (only in normal mode)
        if not free_mode:
            # fuel decrease proportional to abs(speed)
            fuel -= abs(speed) * 0.01
            if fuel < 0:
                fuel = 0

        # update traffic lights timers & detect violations
        update_lights_and_check_violations(dt)

        # draw world
        draw_world()

        # check fuel out
        if not free_mode and fuel <= 0:
            draw_text("油量耗盡！遊戲結束，按 Esc 返回主選單", WIDTH//2 - 260, HEIGHT//2 + 60, RED)

        # draw minimap
        draw_minimap()

    pygame.display.flip()

pygame.quit()

