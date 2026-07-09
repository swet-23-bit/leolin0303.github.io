
from ursina import *
import math
import os
import wave
import struct
import numpy as np

app = Ursina(borderless=False)
window.title = '3D 公車司機模擬器 — Advanced'
window.size = (1280, 720)

ASSET_DIR = 'assets'
os.makedirs(ASSET_DIR, exist_ok=True)
ENGINE_WAV = os.path.join(ASSET_DIR, 'engine_loop.wav')
BRAKE_WAV  = os.path.join(ASSET_DIR, 'brake.wav')
CHIME_WAV  = os.path.join(ASSET_DIR, 'chime.wav')

def _write_wav(path, data, sr=44100):
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(b''.join(struct.pack('<h', int(max(-1,min(1,x))*32767)) for x in data))

if not os.path.exists(ENGINE_WAV):
    sr=44100; dur=1.0
    t=np.linspace(0,dur,int(sr*dur),endpoint=False)
    base=110
    wave1 = 0.5*np.sin(2*np.pi*base*t) + 0.25*np.sin(2*np.pi*2*base*t) + 0.15*np.sin(2*np.pi*3*base*t)
    trem = 0.1*np.sin(2*np.pi*4*t)
    data=(wave1*(0.7+trem)).astype(np.float32)
    _write_wav(ENGINE_WAV, data, sr)
if not os.path.exists(BRAKE_WAV):
    sr=44100; dur=0.7
    t=np.linspace(0,dur,int(sr*dur),endpoint=False)
    noise=np.random.uniform(-1,1,len(t))
    env=np.linspace(1,0,len(t))**2
    hp = np.convolve(noise, [1,-0.98], mode='same')
    data=(hp*env*0.6).astype(np.float32)
    _write_wav(BRAKE_WAV, data, sr)
if not os.path.exists(CHIME_WAV):
    sr=44100; dur=0.4
    t=np.linspace(0,dur,int(sr*dur),endpoint=False)
    a=np.sin(2*np.pi*880*t)*np.exp(-5*t)
    b=np.sin(2*np.pi*1318.5*t)*np.exp(-6*t)
    data=((a+b)*0.5).astype(np.float32)
    _write_wav(CHIME_WAV, data, sr)

game_state = 'menu'
selected_route = None
mode = 'normal'
free_mode = False
score = 0
fuel = 100.0
passengers = 0
boarding = False
board_timer = 0.0
BOARD_INTERVAL = .3

GRID = {'cell': 120, 'lanes_half': 3.5, 'blocks': 3}
WORLD_LEN = GRID['cell']*(GRID['blocks']-1)

MAPS = {
    'city': {'stops': [(-GRID['cell'], 0), (0, GRID['cell']), (GRID['cell'], 0)], 'hills': [], 'traffic_cycle': (180,60,180)},
    'suburb': {'stops': [(-GRID['cell'], -GRID['cell']), (GRID['cell'], -GRID['cell']), (GRID['cell'], GRID['cell'])], 'hills': [], 'traffic_cycle': (220,60,200)},
    'mountain': {'stops': [(-GRID['cell'], 0), (0, GRID['cell']), (GRID['cell'], GRID['cell'])],
                 'hills': [((-GRID['cell'], -GRID['cell']), (0,0), 6), ((0,0), (GRID['cell'], GRID['cell']), 10)], 'traffic_cycle': (180,60,180)}
}

title_text = Text('3D 公車司機模擬器 — Advanced', scale=2, y=.35, enabled=True)
menu_text  = Text('\n'.join(['按 1：市區   2：郊區   3：山區', '按 N：正常模式   F：自由駕駛', '按 Space 開始   Esc 離開']), y=.05, enabled=True)
hud_mode = Text('', position=Vec2(-.88,.47), origin=(0,0), enabled=False)
hud_score= Text('', position=Vec2(-.88,.42), origin=(0,0), enabled=False)
hud_pass = Text('', position=Vec2(-.88,.37), origin=(0,0), enabled=False)
hud_fuel = Text('', position=Vec2(-.88,.32), origin=(0,0), enabled=False)
hint_text= Text('', y=-.43, enabled=False)

gps_arrow = Entity(parent=camera.ui, model='quad', scale=(.05,.08), color=color.azure, rotation_z=0, position=(.9,.42), enabled=False)

from ursina.prefabs.health_bar import HealthBar
fuel_bar = HealthBar(max_value=100, value=100, roundness=.25, bar_color=color.orange, scale=(.4,.03))
fuel_bar.position = Vec2(.25,.45); fuel_bar.enabled=False

ground_parent = Entity()
lamp_parents = []
stops_entities = []

light_state = {}
light_timer = {}
light_cycle  = (180,60,180)

bus = Entity(model='cube', color=color.azure, scale=(1.8,1,4), position=Vec3(0,0.6,-GRID['cell']), collider='box', enabled=False)
bus_vel = Vec3(0,0,0)
yaw = 0.0
steer_input = 0.0
engine_audio = Audio(ENGINE_WAV, loop=True, autoplay=False, volume=0.35)
brake_audio  = Audio(BRAKE_WAV, loop=False, autoplay=False, volume=0.7)
chime_audio  = Audio(CHIME_WAV, loop=False, autoplay=False, volume=0.8)

cam_pivot = Entity(position=(0, 6, -14))
camera.parent = cam_pivot
camera.position = (0,0,0)
camera.rotation = (12,0,0)
camera.fov = 95

sound_enabled = True

def clamp(val, min_v, max_v):
    return max(min_v, min(max_v, val))

def grid_positions():
    coords=[]
    half = GRID['cell']*(GRID['blocks']-1)/2
    for i in range(GRID['blocks']):
        for j in range(GRID['blocks']):
            x = -half + i*GRID['cell']
            z = -half + j*GRID['cell']
            coords.append((x,z))
    return coords

def build_world(route):
    global lamp_parents, stops_entities, light_state, light_timer, light_cycle
    for e in lamp_parents + stops_entities:
        destroy(e)
    lamp_parents.clear(); stops_entities.clear()
    for e in ground_parent.children:
        destroy(e)
    light_state.clear(); light_timer.clear()

    size = WORLD_LEN + 120
    Entity(parent=ground_parent, model='cube', color=color.lime.tint(-.35), scale=(size,0.2,size), position=(0,-.05,0))

    lane_w = GRID['lanes_half']*2
    half = GRID['cell']*(GRID['blocks']-1)/2
    for j in range(GRID['blocks']):
        z = -half + j*GRID['cell']
        Entity(parent=ground_parent, model='cube', color=color.dark_gray, scale=(size,0.1,lane_w), position=(0,0,z))
        for x in range(-int(size/2), int(size/2), 10):
            Entity(parent=ground_parent, model='quad', color=color.white, scale=(0.3,0.8), position=(x,0.06,z), rotation_x=90)
    for i in range(GRID['blocks']):
        x = -half + i*GRID['cell']
        Entity(parent=ground_parent, model='cube', color=color.dark_gray, scale=(lane_w,0.1,size), position=(x,0,0))
        for z in range(-int(size/2), int(size/2), 10):
            Entity(parent=ground_parent, model='quad', color=color.white, scale=(0.3,0.8), position=(x,0.06,z), rotation_x=90)

    for ((x1,z1),(x2,z2),h) in MAPS[route]['hills']:
        cx=(x1+x2)/2; cz=(z1+z2)/2
        length = math.hypot(x2-x1, z2-z1) + GRID['cell']*0.8
        yaw = math.degrees(math.atan2(x2-x1, z2-z1))
        Entity(parent=ground_parent, model='cube', color=color.brown, scale=(lane_w, h, length), position=(cx, h/2, cz), rotation=(0,yaw,0))

    light_cycle = MAPS[route]['traffic_cycle']
    for (x,z) in grid_positions():
        post = Entity(model='cube', color=color.gray, scale=(0.4,4,0.4), position=(x+GRID['lanes_half']+1,2,z))
        head = Entity(model='cube', color=color.black, scale=(0.7,1.2,0.7), position=(x+GRID['lanes_half']+0.6,3.4,z))
        head.g = Entity(model='sphere', scale=.22, position=head.position+Vec3(.0,.35,.0), color=color.green)
        head.y = Entity(model='sphere', scale=.22, position=head.position+Vec3(.0,.00,.0), color=color.black)
        head.r = Entity(model='sphere', scale=.22, position=head.position+Vec3(.0,-.35,.0), color=color.black)
        head.center = (x,z)
        lamp_parents.append(head)
        light_state[(x,z)] = 'NS'
        light_timer[(x,z)] = 0

    for (sx,sz) in MAPS[route]['stops']:
        pole = Entity(model='cube', color=color.green, scale=(0.4,2,0.4), position=(sx- (GRID['lanes_half']+1),1,sz))
        sign = Entity(model='quad', color=color.azure, scale=(0.8,0.8), position=(sx- (GRID['lanes_half']+1),2.2,sz), rotation_y=90)
        stops_entities.append(pole)
        stops_entities.append(sign)

def update_traffic(dt):
    for (x,z), state in light_state.items():
        light_timer[(x,z)] += dt
        r,g,y = light_cycle
        total = r+g+y
        t = light_timer[(x,z)] % total
        # 先用index取燈(因list會pop/append導致順序變化)
        # 這裡改成直接依座標操作，避免錯誤
        # 燈號切換
        if t < r:
            light_state[(x,z)] = 'NS'
            for h in lamp_parents:
                if getattr(h, 'center', None) == (x,z):
                    h.g.color = color.green
                    h.y.color = color.black
                    h.r.color = color.black
                    break
        elif t < r + g:
            light_state[(x,z)] = 'EW'
            for h in lamp_parents:
                if getattr(h, 'center', None) == (x,z):
                    h.g.color = color.black
                    h.y.color = color.green
                    h.r.color = color.black
                    break
        else:
            light_state[(x,z)] = 'YELLOW'
            for h in lamp_parents:
                if getattr(h, 'center', None) == (x,z):
                    h.g.color = color.black
                    h.y.color = color.black
                    h.r.color = color.yellow
                    break

def vehicle_physics(dt):
    global bus_vel, yaw, steer_input, fuel

    accel = 0
    braking = False
    if held_keys['w']:
        accel = 10
    if held_keys['s']:
        accel = -6
    if held_keys['space']:
        braking = True
        accel = -40

    steer = 0
    if held_keys['a']:
        steer = 1
    if held_keys['d']:
        steer = -1

    steer_input = lerp(steer_input, steer, 6*dt)
    yaw += steer_input * 45 * dt * (bus_vel.length()/5)
    dir_vec = Vec3(math.sin(math.radians(yaw)),0,math.cos(math.radians(yaw)))
    force = accel * dt
    bus_vel += dir_vec * force

    bus_vel -= bus_vel * 2.5 * dt

    if braking:
        bus_vel -= dir_vec * 8 * dt
    if bus_vel.length() < 0.05:
        bus_vel = Vec3(0,0,0)

    if not free_mode:
        fuel -= bus_vel.length() * 0.02
        fuel = max(fuel, 0)

    bus.position += bus_vel
    bus.rotation_y = yaw

def update_gps():
    if selected_route is None: return
    if len(MAPS[selected_route]['stops']) == 0: return

    # 目標為第一個站點 (這裡簡化，實務可依距離換下一站)
    target = Vec3(*MAPS[selected_route]['stops'][0], 0)
    vec = target - bus.position
    angle = math.degrees(math.atan2(vec.x, vec.z))
    gps_arrow.rotation_z = -angle
    gps_arrow.enabled = True

def start_game():
    global game_state, bus, bus_vel, yaw, fuel, score, passengers, boarding, board_timer, free_mode

    game_state = 'play'
    hud_mode.enabled = True
    hud_score.enabled = True
    hud_pass.enabled = True
    hud_fuel.enabled = True
    hint_text.enabled = False
    fuel_bar.enabled = True

    bus.position = Vec3(0, 0.6, -GRID['cell'])
    bus.rotation_y = 0
    bus_vel = Vec3(0,0,0)
    yaw = 0
    fuel = 100.0
    score = 0
    passengers = 0
    boarding = False
    board_timer = 0
    free_mode = (mode == 'free')
    hud_mode.text = f"模式: {'自由駕駛' if free_mode else '正常'}"
    hud_score.text = f"分數: {score}"
    hud_pass.text = f"乘客: {passengers}"
    hud_fuel.text = f"油量: {fuel:.1f}"
    fuel_bar.value = fuel

    build_world(selected_route)
    bus.enabled = True
    engine_audio.play()

def to_menu():
    global game_state
    game_state = 'menu'
    hud_mode.enabled = False
    hud_score.enabled = False
    hud_pass.enabled = False
    hud_fuel.enabled = False
    fuel_bar.enabled = False
    gps_arrow.enabled = False
    bus.enabled = False
    engine_audio.stop()
    brake_audio.stop()
    chime_audio.stop()
    hint_text.enabled = False
    title_text.enabled = True
    menu_text.enabled = True

def toggle_sound():
    global sound_enabled
    sound_enabled = not sound_enabled
    if sound_enabled:
        engine_audio.volume = 0.35
        hint_text.text = '🔊 音效 開啟'
    else:
        engine_audio.volume = 0
        hint_text.text = '🔇 音效 關閉'
    hint_text.enabled = True

def input(key):
    global selected_route, mode, free_mode, game_state, passengers, boarding, board_timer

    if game_state == 'menu':
        if key == '1':
            selected_route = 'city'
            menu_text.text = '你選擇了 市區 路線\n按 N 開始正常模式，按 F 開始自由駕駛'
        elif key == '2':
            selected_route = 'suburb'
            menu_text.text = '你選擇了 郊區 路線\n按 N 開始正常模式，按 F 開始自由駕駛'
        elif key == '3':
            selected_route = 'mountain'
            menu_text.text = '你選擇了 山區 路線\n按 N 開始正常模式，按 F 開始自由駕駛'
        elif key == 'n' and selected_route:
            mode = 'normal'
            start_game()
            title_text.enabled = False
            menu_text.enabled = False
        elif key == 'f' and selected_route:
            mode = 'free'
            start_game()
            title_text.enabled = False
            menu_text.enabled = False
        elif key == 'escape':
            application.quit()
    elif game_state == 'play':
        if key == 'escape':
            to_menu()
        elif key == 'm':
            toggle_sound()
        elif key == 'p':
            # 乘客上車
            if passengers < 10:
                passengers += 1
                chime_audio.play()
                hud_pass.text = f"乘客: {passengers}"
                global score
                score += 5
                hud_score.text = f"分數: {score}"
        elif key == 'e':
            # 自動上下客切換(未實作)
            hint_text.text = '自動上下客模式尚未完成'
            hint_text.enabled = True

def update():
    dt = time.dt
    if game_state == 'play':
        vehicle_physics(dt)
        update_traffic(dt)
        update_gps()

        hud_fuel.text = f"油量: {fuel:.1f}"
        hud_score.text = f"分數: {score}"
        hud_pass.text = f"乘客: {passengers}"
        fuel_bar.value = fuel

        if fuel <= 0:
            hint_text.text = '油量耗盡，遊戲結束！按 ESC 返回選單'
            hint_text.enabled = True
            engine_audio.pause()
    else:
        pass

to_menu()
app.run()

