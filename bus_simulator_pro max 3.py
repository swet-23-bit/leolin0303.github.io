# bus_simulator_pro.py
import pygame
import sys
import random

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("公車司機模擬器 Pro")
clock = pygame.time.Clock()

# ---------- Colors ----------
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (120,120,120)
ROAD_GRAY = (70,70,70)
SIDEWALK = (160,160,160)
GREEN = (0,200,0)
RED = (200,0,0)
YELLOW = (255,200,0)
BLUE = (30,120,220)
DARK_GREEN = (30,140,60)
BROWN = (140,100,60)
ORANGE = (255,160,60)

# ---------- Fonts ----------
font = pygame.font.SysFont(None, 24)
big = pygame.font.SysFont(None, 44)

def draw_text(s, x, y, c=WHITE, f=font):
    screen.blit(f.render(s, True, c), (x,y))

# ---------- Bus ----------
BUS_W, BUS_H = 72, 34
bus_img = pygame.Surface((BUS_W, BUS_H), pygame.SRCALPHA)
pygame.draw.rect(bus_img, BLUE, (0,0,BUS_W,BUS_H), border_radius=6)
pygame.draw.rect(bus_img, (220,220,255), (8,6,BUS_W-16,BUS_H-16))
BUS_SCREEN_X = 180           # bus fixed x on screen
bus_world_x = 100.0          # position in world coords
bus_speed = 0.0

# ---------- Game / Maps ----------
maps = {
    "city": {
        "length": 1600,
        "stations": [250, 420, 600, 760, 920, 1080, 1240, 1400],
        "lights": [360, 840, 1160, 1360],
        "fuels": [800, 1400],
        "hills": []
    },
    "suburb": {
        "length": 2600,
        "stations": [480, 940, 1400, 1850, 2250],
        "lights": [1200, 2100],
        "fuels": [1500, 2400],
        "hills": []
    },
    "mountain": {
        "length": 2200,
        "stations": [380, 920, 1320, 1680, 2040],
        "lights": [1100, 1900],
        "fuels": [1000, 1900],
        "hills": [(600, 820, 0.6), (1400, 1620, 0.8)]
    }
}

game_state = "menu"          # menu | play
selected_route = None
selected_mode = "normal"     # normal | free
route_choice = None

# Active world
world_length = 2000
scroll_x = 0.0
fuel = 100.0
score = 0
free_mode = False
passengers_onboard = 0       # 目前車上乘客數

# Objects
stations = []    # list of dicts: {"x":pos,"waiting":n,"served":False}
lights = []
fuels = []
hills = []
light_state = {}
light_timer = {}

# Boarding (乘客上車) 狀態
BOARD_RANGE = 14               # 與站牌的距離門檻（世界座標）
BOARD_INTERVAL_MS = 350        # 每位乘客上車間隔
is_boarding = False
boarding_station = None        # 指向當前靠站的 dict
boarding_timer = 0
boarded_this_stop = 0

# Minimap
MINIMAP_W, MINIMAP_H = 200, 100
minimap = pygame.Surface((MINIMAP_W, MINIMAP_H))

# ---------- Helpers ----------
def world_to_screen(wx):
    return int(wx - scroll_x + BUS_SCREEN_X - bus_world_x)

def init_route(route, mode):
    global world_length, stations, lights, fuels, hills, light_state, light_timer
    global scroll_x, bus_world_x, fuel, score, free_mode, route_choice
    global passengers_onboard, is_boarding, boarding_station, boarding_timer, boarded_this_stop

    cfg = maps[route]
    world_length = cfg["length"]
    # 站牌：加入等待人數（隨機 2~8 人）
    stations = [{"x": x, "waiting": random.randint(2,8), "served": False} for x in cfg["stations"]]
    lights = cfg["lights"][:]
    fuels = cfg["fuels"][:]
    hills = cfg["hills"][:]
    light_state = {p: "green" for p in lights}
    light_timer = {p: 0 for p in lights}

    scroll_x = 0.0
    bus_world_x = 100.0
    fuel = 100.0
    score = 0
    free_mode = (mode == "free")
    route_choice = route
    passengers_onboard = 0

    # reset boarding state
    is_boarding = False
    boarding_station = None
    boarding_timer = 0
    boarded_this_stop = 0

def draw_background():
    screen.fill(DARK_GREEN if route_choice != "mountain" else (90,130,90))
    road_top = HEIGHT//2 - 60
    road_h = 120
    pygame.draw.rect(screen, SIDEWALK, (0, road_top, WIDTH, road_h))
    pygame.draw.rect(screen, ROAD_GRAY, (0, road_top + 20, WIDTH, road_h - 40))
    dash = 28; gap = 18
    cy = road_top + road_h//2
    for x in range(0, WIDTH, dash+gap):
        pygame.draw.line(screen, WHITE, (x, cy), (x+dash, cy), 3)

def draw_world():
    # Hills
    for hx1, hx2, slope in hills:
        sx1 = world_to_screen(hx1) - 200
        sx2 = world_to_screen(hx2) + 200
        base_y = HEIGHT//2 - 40
        points = [(sx1, HEIGHT), ((sx1+sx2)//2, base_y - int(slope*200)), (sx2, HEIGHT)]
        pygame.draw.polygon(screen, BROWN, points)

    # Fuel stations
    for fpos in fuels:
        fx = world_to_screen(fpos)
        if -120 < fx < WIDTH + 120:
            pygame.draw.rect(screen, RED, (fx-18, HEIGHT//2 + 48, 36, 36))
            screen.blit(font.render("G", True, BLACK), (fx-8, HEIGHT//2 + 52))

    # Traffic lights
    for lpos in lights:
        lx = world_to_screen(lpos)
        if -120 < lx < WIDTH + 120:
            pygame.draw.rect(screen, GRAY, (lx-6, HEIGHT//2 - 94, 12, 60))
            st = light_state.get(lpos, "green")
            if st == "green":
                pygame.draw.circle(screen, GREEN, (lx, HEIGHT//2 - 84), 6)
            elif st == "yellow":
                pygame.draw.circle(screen, YELLOW, (lx, HEIGHT//2 - 72), 6)
            else:
                pygame.draw.circle(screen, RED, (lx, HEIGHT//2 - 60), 6)

    # Stations
    for st in stations:
        sx = world_to_screen(st["x"])
        if -140 < sx < WIDTH + 140:
            # 站牌
            pygame.draw.rect(screen, GREEN if not st["served"] else (80,140,80),
                             (sx-8, HEIGHT//2 + 36, 16, 48))
            # 顯示等待人數
            draw_text(str(st["waiting"]), sx-6, HEIGHT//2 + 18, ORANGE)

    # Bus
    screen.blit(bus_img, (BUS_SCREEN_X - BUS_W//2, HEIGHT//2 - BUS_H//2))

def update_lights_and_check():
    global score, fuel
    for pos in lights:
        light_timer[pos] += 1
        st = light_state[pos]
        if st == "green" and light_timer[pos] > 180:
            light_state[pos] = "yellow"; light_timer[pos] = 0
        elif st == "yellow" and light_timer[pos] > 60:
            light_state[pos] = "red"; light_timer[pos] = 0
        elif st == "red" and light_timer[pos] > 180:
            light_state[pos] = "green"; light_timer[pos] = 0

        # violation check: near line and red while moving forward
        sx = world_to_screen(pos)
        if abs(sx - BUS_SCREEN_X) < 8 and light_state[pos] == "red" and bus_speed > 0:
            if not free_mode:
                score -= 2
                fuel -= 10
                screen.blit(big.render("闖紅燈！-2分 -10%油量", True, RED), (WIDTH//2 - 220, HEIGHT//2 - 110))

def refuel_if_needed():
    global fuel
    for fpos in fuels:
        if abs(fpos - bus_world_x) <= 8 and abs(world_to_screen(fpos) - BUS_SCREEN_X) <= 8:
            fuel = 100.0

def find_near_station():
    """回傳靠近的站牌物件（世界距離在 BOARD_RANGE 內），否則回傳 None"""
    for st in stations:
        if not st["served"] and abs(st["x"] - bus_world_x) <= BOARD_RANGE:
            return st
    return None

def start_boarding(station_obj):
    """開始上客流程"""
    global is_boarding, boarding_station, boarding_timer, boarded_this_stop
    is_boarding = True
    boarding_station = station_obj
    boarding_timer = 0
    boarded_this_stop = 0

def update_boarding(dt_ms):
    """每隔 BOARD_INTERVAL_MS 讓 1 位乘客上車，直到 waiting 為 0"""
    global is_boarding, boarding_station, boarding_timer, boarded_this_stop
    global passengers_onboard, score
    if not is_boarding or boarding_station is None:
        return

    boarding_timer += dt_ms
    if boarding_timer >= BOARD_INTERVAL_MS and boarding_station["waiting"] > 0:
        boarding_timer = 0
        boarding_station["waiting"] -= 1
        passengers_onboard += 1
        if not free_mode:
            score += 1
        boarded_this_stop += 1

    if boarding_station["waiting"] <= 0:
        # 完成上客
        boarding_station["served"] = True
        is_boarding = False
        boarding_station = None
        boarding_timer = 0

def draw_hud():
    draw_text(f"地圖: {route_choice}", 10, 8)
    draw_text(f"模式: {'自由' if free_mode else '正常'}", 10, 30)
    draw_text(f"車上乘客: {passengers_onboard}", 10, 52)
    if not free_mode:
        draw_text(f"油量: {int(fuel)}%", 10, 74)
        draw_text(f"得分: {score}", 10, 96)
    else:
        draw_text("自由駕駛：油量無限、無計分", 10, 74)

def draw_boarding_ui():
    """顯示靠站提示與上客進度"""
    near = find_near_station()
    if near and not is_boarding and abs(bus_speed) < 0.05:
        draw_text("已到站！按 E 開始上客", WIDTH//2 - 120, HEIGHT//2 + 80, ORANGE)
    if is_boarding and boarding_station:
        msg = f"上客中... {boarded_this_stop} 位 / 總共"
        draw_text(msg, WIDTH//2 - 80, HEIGHT//2 + 80, ORANGE)
        # 簡單進度條
        total = boarded_this_stop + boarding_station["waiting"]
        total = max(1, total)
        done = boarded_this_stop
        bar_w = 240
        x = WIDTH//2 - bar_w//2
        y = HEIGHT//2 + 110
        pygame.draw.rect(screen, (60,60,60), (x, y, bar_w, 16))
        fill_w = int(bar_w * (done / total))
        pygame.draw.rect(screen, ORANGE, (x, y, fill_w, 16))
        draw_text(f"{done}/{total}", x + bar_w//2 - 16, y - 20, WHITE)

def draw_minimap():
    minimap.fill((30,30,30))
    pygame.draw.rect(minimap, (200,200,200), (0,0,MINIMAP_W,MINIMAP_H), 2)
    sx, sy = 8, 12
    sw = MINIMAP_W - 2*sx
    sh = MINIMAP_H - 2*sy
    pygame.draw.rect(minimap, (70,70,70), (sx, sy + sh//3, sw, sh//3))
    if route_choice:
        cfg = maps[route_choice]
        mlen = cfg["length"]
        def mapx(wx):
            wx = max(0, min(mlen, wx))
            return sx + int((wx / mlen) * sw)

        # stations (用原始位置顯示；已服務的顏色會變暗)
        for st in stations:
            color = GREEN if not st["served"] else (80,140,80)
            pygame.draw.rect(minimap, color, (mapx(st["x"])-2, sy + sh//3 - 6, 4, 6))
        for l in lights:
            pygame.draw.rect(minimap, YELLOW, (mapx(l)-1, sy + sh//3 - 14, 3, 8))
        for f in fuels:
            pygame.draw.rect(minimap, RED, (mapx(f)-2, sy + sh//3 + 8, 4, 4))
        # bus
        bx = mapx(bus_world_x)
        pygame.draw.polygon(minimap, BLUE, [(bx, sy + sh//3 + 18), (bx-5, sy + sh//3 + 28), (bx+5, sy + sh//3 + 28)])
    screen.blit(minimap, (WIDTH - MINIMAP_W - 10, 10))

def draw_menu(selected, mode):
    screen.fill(GRAY)
    screen.blit(big.render("公車司機模擬器 Pro", True, WHITE), (WIDTH//2 - 240, 40))
    draw_text("按 1：市區線（紅綠燈多、站牌密）", WIDTH//2 - 220, 160)
    draw_text("按 2：郊區線（距離長、紅綠燈少）", WIDTH//2 - 220, 200)
    draw_text("按 3：山區線（坡道、多樣地形）", WIDTH//2 - 220, 240)
    draw_text("按 N：正常模式（油量 & 計分）", WIDTH//2 - 220, 300)
    draw_text("按 F：自由駕駛（油量無限）", WIDTH//2 - 220, 340)
    draw_text("選好後按 Space 開始遊戲，Esc 離開程式", WIDTH//2 - 220, 420)
    draw_text(f"目前選擇地圖：{selected}", WIDTH//2 - 220, 460)
    draw_text(f"目前選擇模式：{mode}", WIDTH//2 - 220, 490)

# ---------- Main loop ----------
running = True
paused = False

while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "menu":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: selected_route = "city"
                elif event.key == pygame.K_2: selected_route = "suburb"
                elif event.key == pygame.K_3: selected_route = "mountain"
                elif event.key == pygame.K_n: selected_mode = "normal"
                elif event.key == pygame.K_f: selected_mode = "free"
                elif event.key == pygame.K_SPACE and selected_route:
                    init_route(selected_route, selected_mode)
                    game_state = "play"
                elif event.key == pygame.K_ESCAPE:
                    running = False

        elif game_state == "play":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"
                    selected_route = None
                    selected_mode = "normal"
                elif event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_e:
                    # 嘗試開始上客：需在站牌旁且速度為 0
                    near = find_near_station()
                    if near and not is_boarding and abs(bus_speed) < 0.05:
                        start_boarding(near)

    if game_state == "menu":
        draw_menu(selected_route, selected_mode)

    elif game_state == "play":
        if paused:
            draw_text("已暫停 (P 切換) - Esc 回主選單", WIDTH//2 - 180, HEIGHT//2 - 20)
            pygame.display.flip()
            continue

        # Controls: arrows or WASD
        keys = pygame.key.get_pressed()
        forward = keys[pygame.K_RIGHT] or keys[pygame.K_d] or keys[pygame.K_UP] or keys[pygame.K_w]
        back    = keys[pygame.K_LEFT]  or keys[pygame.K_a] or keys[pygame.K_DOWN] or keys[pygame.K_s]

        # Base speed & slope effect
        base_speed = 3.6
        slope_factor = 1.0
        if route_choice == "mountain":
            for hx1, hx2, s in hills:
                if hx1 <= bus_world_x <= hx2:
                    slope_factor = max(0.4, 1.0 - s*0.5)
                    break

        if is_boarding:
            # 上客中必須保持靜止
            bus_speed = 0.0
        else:
            if forward and not back:
                bus_speed = base_speed * slope_factor
            elif back and not forward:
                bus_speed = -2.0
            else:
                bus_speed = 0.0

        # Update world pos / camera
        bus_world_x += bus_speed
        bus_world_x = max(0, min(world_length, bus_world_x))
        scroll_x = bus_world_x - BUS_SCREEN_X

        # Fuel usage
        if not free_mode and not is_boarding:
            fuel -= abs(bus_speed) * 0.01
            if fuel < 0: fuel = 0.0

        # Systems
        update_lights_and_check()
        refuel_if_needed()
        update_boarding(dt)

        # Draw scene
        draw_background()
        draw_world()
        draw_hud()
        draw_boarding_ui()
        draw_minimap()

        # Out of fuel
        if not free_mode and fuel <= 0:
            draw_text("油量耗盡！按 Esc 回主選單", WIDTH//2 - 160, HEIGHT//2 + 80, RED)

    pygame.display.flip()

pygame.quit()
sys.exit()

