# bus_simulator_pro.py
import pygame
import random
import sys

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("公車司機模擬器 Pro")
clock = pygame.time.Clock()

# Colors
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

# Fonts
font = pygame.font.SysFont(None, 24)
big = pygame.font.SysFont(None, 44)

# Bus sprite (simple)
BUS_W, BUS_H = 72, 34
bus_img = pygame.Surface((BUS_W, BUS_H), pygame.SRCALPHA)
pygame.draw.rect(bus_img, BLUE, (0,0,BUS_W,BUS_H), border_radius=6)
pygame.draw.rect(bus_img, (220,220,255), (8,6,BUS_W-16,BUS_H-16))

# UI / world constants
BUS_SCREEN_X = 180  # bus fixed on screen x
bus_world_x = 100.0

# Maps definition
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

# Game state
game_state = "menu"  # menu, play, paused
selected_route = None
selected_mode = "normal"  # "normal" or "free"
route_choice = None

# Active world variables (set when starting)
world_length = 2000
stations = []
lights = []
fuels = []
hills = []
light_state = {}
light_timer = {}
scroll_x = 0.0
speed = 0.0
fuel = 100.0
score = 0
free_mode = False

# Minimap
MINIMAP_W, MINIMAP_H = 200, 100
minimap = pygame.Surface((MINIMAP_W, MINIMAP_H))

def draw_text(s, x, y, c=WHITE, f=font):
    screen.blit(f.render(s, True, c), (x,y))

def init_route(route, mode):
    global world_length, stations, lights, fuels, hills, light_state, light_timer
    global scroll_x, bus_world_x, fuel, score, free_mode, route_choice
    cfg = maps[route]
    world_length = cfg["length"]
    stations = cfg["stations"][:]
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

def world_to_screen(wx):
    return int(wx - scroll_x + BUS_SCREEN_X - bus_world_x)

def draw_background():
    # ground color
    screen.fill(DARK_GREEN if route_choice != "mountain" else (90,130,90))
    road_top = HEIGHT//2 - 60
    road_h = 120
    pygame.draw.rect(screen, SIDEWALK, (0, road_top, WIDTH, road_h))
    pygame.draw.rect(screen, ROAD_GRAY, (0, road_top + 20, WIDTH, road_h - 40))
    # dashed center
    dash = 28; gap = 18
    cy = road_top + road_h//2
    for x in range(0, WIDTH, dash+gap):
        pygame.draw.line(screen, WHITE, (x, cy), (x+dash, cy), 3)

def draw_world():
    global score, fuel
    draw_background()
    # hills
    for hx1, hx2, slope in hills:
        sx1 = world_to_screen(hx1) - 200
        sx2 = world_to_screen(hx2) + 200
        base_y = HEIGHT//2 - 40
        points = [(sx1, HEIGHT), ((sx1+sx2)//2, base_y - int(slope*200)), (sx2, HEIGHT)]
        pygame.draw.polygon(screen, BROWN, points)
    # draw stations (use map's original for minimap consistency)
    for s in stations[:]:
        sx = world_to_screen(s)
        if -120 < sx < WIDTH + 120:
            pygame.draw.rect(screen, GREEN, (sx-8, HEIGHT//2 + 40, 16, 44))
            screen.blit(font.render("站", True, BLACK), (sx-7, HEIGHT//2 + 44))
        # auto-stop detection
        if abs(s - bus_world_x) < 8 and abs(world_to_screen(s) - BUS_SCREEN_X) < 8:
            score += 1
            try:
                stations.remove(s)
            except ValueError:
                pass
    # fuel stations
    for fpos in fuels:
        fx = world_to_screen(fpos)
        if -120 < fx < WIDTH + 120:
            pygame.draw.rect(screen, RED, (fx-18, HEIGHT//2 + 48, 36, 36))
            screen.blit(font.render("G", True, BLACK), (fx-8, HEIGHT//2 + 52))
        if abs(fpos - bus_world_x) < 8 and abs(world_to_screen(fpos) - BUS_SCREEN_X) < 8:
            fuel = 100.0
    # traffic lights
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
    # bus
    screen.blit(bus_img, (BUS_SCREEN_X - BUS_W//2, HEIGHT//2 - BUS_H//2))
    # HUD
    draw_text(f"地圖: {route_choice}", 10, 8)
    draw_text(f"模式: {'自由' if free_mode else '正常'}", 10, 30)
    if not free_mode:
        draw_text(f"油量: {int(fuel)}%", 10, 52)
        draw_text(f"乘客: {score}", 10, 74)
    else:
        draw_text("自由駕駛：油量無限、無計分", 10, 52)

def update_lights_and_check(delta):
    global score, fuel
    # delta unused for frame-timer but kept for expansions
    for pos in lights:
        light_timer[pos] = light_timer.get(pos, 0) + 1
        st = light_state.get(pos, "green")
        if st == "green" and light_timer[pos] > 180:
            light_state[pos] = "yellow"; light_timer[pos] = 0
        elif st == "yellow" and light_timer[pos] > 60:
            light_state[pos] = "red"; light_timer[pos] = 0
        elif st == "red" and light_timer[pos] > 180:
            light_state[pos] = "green"; light_timer[pos] = 0
        # detect if bus is crossing while light is red (based on screen pos)
        sx = world_to_screen(pos)
        if abs(sx - BUS_SCREEN_X) < 8 and light_state[pos] == "red" and speed > 0:
            if not free_mode:
                score -= 2
                fuel -= 10
                # show center warning (drawn in draw_world via HUD)
                screen.blit(big.render("闖紅燈！-2分 -10% 油量", True, RED), ((WIDTH//2)-260, HEIGHT//2 - 120))

def draw_minimap():
    minimap.fill((30,30,30))
    pygame.draw.rect(minimap, (200,200,200), (0,0,MINIMAP_W,MINIMAP_H), 2)
    sx, sy = 8, 12
    sw = MINIMAP_W - 2*sx
    sh = MINIMAP_H - 2*sy
    # base road
    pygame.draw.rect(minimap, (70,70,70), (sx, sy + sh//3, sw, sh//3))
    # draw all initial stations and objects from maps[route_choice] to show original positions
    if route_choice:
        mapcfg = maps[route_choice]
        mlen = mapcfg["length"]
        def mapx(wx):
            return sx + max(0, min(sw, int((wx / mlen) * sw)))
        for s in mapcfg["stations"]:
            pygame.draw.rect(minimap, GREEN, (mapx(s)-2, sy + sh//3 - 6, 4, 6))
        for l in mapcfg["lights"]:
            pygame.draw.rect(minimap, YELLOW, (mapx(l)-1, sy + sh//3 - 14, 3, 8))
        for f in mapcfg["fuels"]:
            pygame.draw.rect(minimap, RED, (mapx(f)-2, sy + sh//3 + 8, 4, 4))
        # bus pos
        bx = max(0, min(mapcfg["length"], int(bus_world_x)))
        px = mapx(bx)
        pygame.draw.polygon(minimap, BLUE, [(px, sy + sh//3 + 18), (px-5, sy + sh//3 + 28), (px+5, sy + sh//3 + 28)])
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

# Main loop
running = True
paused = False

while running:
    dt = clock.tick(60)
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
                elif event.key == pygame.K_n:
                    selected_mode = "normal"
                elif event.key == pygame.K_f:
                    selected_mode = "free"
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

    if game_state == "menu":
        draw_menu(selected_route, selected_mode)
    elif game_state == "play":
        if paused:
            draw_text("已暫停 (P 切換) - Esc 回主選單", WIDTH//2 - 180, HEIGHT//2 - 20)
            pygame.display.flip()
            continue

        # Controls: arrow keys or WASD
        keys = pygame.key.get_pressed()
        forward = keys[pygame.K_RIGHT] or keys[pygame.K_d] or keys[pygame.K_UP] or keys[pygame.K_w]
        back = keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_DOWN] or keys[pygame.K_s]

        # base speed
        base_speed = 3.6
        slope_factor = 1.0
        # mountain slope slow effect
        if route_choice == "mountain":
            for h in hills:
                hx1, hx2, s = h
                if hx1 <= bus_world_x <= hx2:
                    slope_factor = max(0.4, 1.0 - s*0.5)
                    break

        if forward and not back:
            speed = base_speed * slope_factor
        elif back and not forward:
            speed = -2.0
        else:
            speed = 0.0

        # update world pos
        bus_world_x += speed
        bus_world_x = max(0, min(world_length, bus_world_x))
        scroll_x = bus_world_x - BUS_SCREEN_X

        # fuel consumption (normal mode)
        if not free_mode:
            fuel -= abs(speed) * 0.01
            if fuel < 0:
                fuel = 0

        # update lights & check violations
        update_lights_and_check(dt)

        # draw scene
        draw_world()
        if not free_mode and fuel <= 0:
            draw_text("油量耗盡！按 Esc 回主選單", WIDTH//2 - 160, HEIGHT//2 + 80, RED)

        draw_minimap()

    pygame.display.flip()

pygame.quit()
sys.exit()

