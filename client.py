from ursina import *
from ursinanetworking import *
import json as js
import sys

if len(sys.argv) < 3:
    print("Usage: python client.py <port> <username>")
    sys.exit(1)

port = int(sys.argv[1])
username = sys.argv[2]

app = Ursina(title=f"Yoblox - {username}", borderless=False)
window.fps_counter.enabled = False
window.always_on_top = False
window.exit_button.visible = False
client = UrsinaNetworkingClient("localhost", port)
players = {}
local_player_id = None
local_player = None
last_position = None
player_names = {}
spawn_point = None

# Modern Zemin ve Çevre
ground = Entity(model='plane', scale=(100, 1, 100), texture='white_cube', texture_scale=(100, 100), color=color.rgb(50, 150, 50))

class Part(Entity):
    def __init__(self, **kwargs):
        color_arg = kwargs.pop('color', color.random_color())
        super().__init__(model='cube', color=color_arg, **kwargs)  # Texture kaldırıldı
        self.collider = 'box'
        self.highlight_color = color.lime

    def on_click(self):
        print(f'Clicked on part at position: {self.position}')

class YobloxPlayer(Entity):
    def __init__(self, position, color_rgb, player_id, name=None):
        super().__init__()
        self.id = player_id
        
        # Modern karakter: Texture olmadan düz renkler
        self.torso = Entity(model='cube', scale=(1, 1.8, 0.5), position=position, color=rgb(*color_rgb), parent=self)
        self.head = Entity(model='sphere', scale=0.8, position=(0, 1.2, 0), color=color.hex('#ffd700'), parent=self.torso)
        self.left_arm = Entity(model='cube', scale=(0.4, 1.6, 0.4), position=(-0.7, 0.2, 0), color=color.hex('#ff8c00'), parent=self.torso)
        self.right_arm = Entity(model='cube', scale=(0.4, 1.6, 0.4), position=(0.7, 0.2, 0), color=color.hex('#ff8c00'), parent=self.torso)
        self.left_leg = Entity(model='cube', scale=(0.4, 1.6, 0.4), position=(-0.3, -0.6, 0), color=color.hex('#4682b4'), parent=self.torso)
        self.right_leg = Entity(model='cube', scale=(0.4, 1.6, 0.4), position=(0.3, -0.6, 0), color=color.hex('#4682b4'), parent=self.torso)
        
        # İsim etiketi
        self.name_tag = Text(text=name or f"Player_{player_id}", scale=2, origin=(0, 0), position=(0, 1.8, 0), parent=self.torso, color=color.white, billboard=True)

# ESC Menüsü
menu_open = False
menu_entities = []

def toggle_menu():
    global menu_open, menu_entities
    print("[CLIENT] Toggling menu called")
    if not menu_open:
        print("[CLIENT] Opening ESC menu")
        menu_panel = Entity(model='quad', scale=(0.6, 0.7), position=window.center, parent=camera.ui, 
                           color=color.rgba(40, 40, 40, 230), texture='vertical_gradient', texture_scale=(1, 1), 
                           texture_offset=(0, 0.5))
        menu_panel.visible = True
        print(f"[CLIENT] Menu panel created at position={menu_panel.position}, z={menu_panel.z}")

        menu_title = Text(text="Game Menu", scale=2.5, origin=(0, 0), position=(0, 0.28, -0.01), 
                         parent=menu_panel, color=color.white, font='VeraMono.ttf')
        menu_title.visible = True
        print(f"[CLIENT] Menu title created at position={menu_title.position}, z={menu_title.z}")

        leave_button = Button(text="Leave Game", scale=(0.45, 0.1), y=0.1, z=-0.01, parent=menu_panel, 
                             color=color.hex('#e63946'), text_color=color.white, radius=0.1, 
                             highlight_color=color.hex('#f94144'), on_click=sys.exit)
        leave_button.visible = True
        print(f"[CLIENT] Leave button created at position={leave_button.position}, z={leave_button.z}")

        reset_button = Button(text="Reset Character", scale=(0.45, 0.1), y=-0.02, z=-0.01, parent=menu_panel, 
                             color=color.hex('#2a9d8f'), text_color=color.white, radius=0.1, 
                             highlight_color=color.hex('#34c7b7'), on_click=die_and_respawn)
        reset_button.visible = True
        print(f"[CLIENT] Reset button created at position={reset_button.position}, z={reset_button.z}")

        settings_button = Button(text="Settings", scale=(0.45, 0.1), y=-0.14, z=-0.01, parent=menu_panel, 
                                color=color.hex('#457b9d'), text_color=color.white, radius=0.1, 
                                highlight_color=color.hex('#569dc2'), on_click=lambda: print("Settings clicked (not implemented yet)"))
        settings_button.visible = True
        print(f"[CLIENT] Settings button created at position={settings_button.position}, z={settings_button.z}")

        shadow = Entity(model='quad', scale=(0.62, 0.72), position=(0.01, -0.01, 0.01), parent=menu_panel, 
                       color=color.rgba(0, 0, 0, 50))
        shadow.visible = True

        menu_entities = [menu_panel, menu_title, leave_button, reset_button, settings_button, shadow]
        mouse.locked = False
        menu_open = True
    else:
        print("[CLIENT] Closing ESC menu")
        for entity in menu_entities:
            destroy(entity)
        menu_entities = []
        mouse.locked = True
        menu_open = False

# Modern gökyüzü ve ışıklandırma
sky = Sky(texture='sky_sunset')
scene.fog_density = 0.02
scene.fog_color = color.rgb(200, 200, 200)
sun = DirectionalLight(shadows=True)
sun.look_at(Vec3(-1, -1, -1))

# Oyuncu listesi GUI’si (Modernize edilmiş)
playerlist_panel = Entity(model='quad', scale=(0.25, 0.4), position=(0.68, 0.38), parent=camera.ui, 
                         color=color.rgba(30, 30, 30, 200), texture='vertical_gradient')
playerlist_title = Text(text="Players", scale=2, origin=(0, 0), position=(0, 0.18, -0.01), parent=playerlist_panel, 
                       color=color.white, font='VeraMono.ttf')
playerlist_texts = []

def update_playerlist():
    global playerlist_texts
    for t in playerlist_texts:
        destroy(t)
    playerlist_texts = []
    y_pos = 0.12
    sorted_players = sorted(players.items(), key=lambda x: x[0])
    for pid, player in sorted_players:
        display_name = player_names.get(pid, f"Player_{pid}")
        t = Text(text=display_name, scale=1.5, origin=(-0.5, 0), position=(-0.11, y_pos, -0.01), parent=playerlist_panel, 
                color=color.white)
        playerlist_texts.append(t)
        y_pos -= 0.05
    if local_player:
        t = Text(text=username, scale=1.5, origin=(-0.5, 0), position=(-0.11, y_pos, -0.01), parent=playerlist_panel, 
                color=color.white)
        playerlist_texts.append(t)

mouse.locked = True
velocity = Vec3(0, 0, 0)
is_grounded = False

def update():
    global velocity, is_grounded, last_position
    if not local_player:
        return

    # ESC tuşu ile menüyü aç/kapat
    if held_keys['escape']:
        print("[CLIENT] ESC key detected")
        toggle_menu()
        held_keys['escape'] = 0  # Tekrar basımı önlemek için sıfırla

    if not menu_open:  # Menü açık değilse hareket et
        move_speed = 6 * time.dt
        fall_speed = 20

        def move_entity(entity, direction):
            start_pos = entity.position
            end_pos = start_pos + direction * move_speed
            ray = raycast(start_pos, direction, distance=move_speed, ignore=(entity,))
            if not ray.hit:
                entity.position = end_pos

        if held_keys['w']:
            move_entity(local_player, local_player.forward)
        if held_keys['s']:
            move_entity(local_player, -local_player.forward)
        if held_keys['a']:
            move_entity(local_player, -local_player.right)
        if held_keys['d']:
            move_entity(local_player, local_player.right)

        if is_grounded and held_keys['space']:
            velocity.y = 12
            is_grounded = False

        velocity.y -= fall_speed * time.dt
        local_player.position += velocity * time.dt

        ray = raycast(local_player.position, Vec3(0, -1, 0), distance=1.5, ignore=(local_player,))
        if ray.hit:
            is_grounded = True
            velocity.y = 0
            local_player.y = ray.world_point.y + 1.5
        else:
            is_grounded = False

        if local_player.y < -50:
            die_and_respawn()

        camera.rotation_x -= mouse.velocity[1] * 40
        camera.rotation_y += mouse.velocity[0] * 40

        current_position = (local_player.x, local_player.y, local_player.z)
        if client.connected and current_position != last_position:
            client.send_message("move", current_position)
            last_position = current_position

    update_playerlist()

def die_and_respawn():
    global velocity, last_position
    if local_player and spawn_point:
        client.send_message("player_just_died", None)
        print(f"[CLIENT] {local_player_id} died")
        local_player.position = spawn_point.position + Vec3(0, 1.5, 0)
        velocity = Vec3(0, 0, 0)
        last_position = local_player.position

@client.event
def onConnected():
    print(f"[CLIENT] {username} connected to server!")
    client.send_message("set_name", username)

@client.event
def your_id(player_id):
    global local_player_id
    local_player_id = player_id
    print(f"[CLIENT] My ID is {local_player_id}")

@client.event
def load_map(map_data_str):
    global spawn_point
    map_data = js.loads(map_data_str)
    print("[CLIENT] Loading map with data:", map_data)
    for item in map_data:
        r = float(item["color"]["r"]) * 255
        g = float(item["color"]["g"]) * 255
        b = float(item["color"]["b"]) * 255
        a = float(item["color"]["a"]) * 255
        color_value = color.rgba(int(r), int(g), int(b), int(a))
        pos = (item["position"]["x"], item["position"]["y"], item["position"]["z"])
        scale = (item["scale"]["x"], item["scale"]["y"], item["scale"]["z"])
        part = Part(position=pos, scale=scale, color=color_value)
        if item.get("name") == "spawnpoint":
            spawn_point = part
        print(f"[CLIENT] Creating part at {pos} with color {color_value}")

@client.event
def spawn_player(data):
    global local_player, last_position
    player_id = data["id"]
    position = data["position"]
    color_rgb = data["color"]
    name = data.get("name", f"Player_{player_id}")
    print(f"[CLIENT] Received spawn_player for ID {player_id} at {position} with color {color_rgb}, name: {name}")

    player_names[player_id] = name
    if player_id == local_player_id and local_player is None:
        local_player = YobloxPlayer(position=Vec3(*position), color_rgb=color_rgb, player_id=player_id, name=username)
        camera.parent = local_player.head
        camera.position = (0, 2, -5)
        camera.rotation = (10, 0, 0)
        last_position = local_player.position
        print(f"[CLIENT] Local player spawned with ID {player_id}")
    else:
        if player_id not in players:
            print(f"[CLIENT] Spawning new remote player {player_id}")
            players[player_id] = YobloxPlayer(position=Vec3(*position), color_rgb=color_rgb, player_id=player_id, name=name)
        else:
            print(f"[CLIENT] Updating existing player {player_id}")
            players[player_id].position = Vec3(*position)
            players[player_id].name_tag.text = name

@client.event
def remove_player(data):
    player_id = data["id"]
    if player_id in players:
        print(f"[CLIENT] Removing player {player_id}")
        destroy(players[player_id])
        del players[player_id]
        del player_names[player_id]

@client.event
def update_positions(positions):
    for player_id, position in positions.items():
        if player_id != local_player_id and player_id in players:
            print(f"[CLIENT] Updating position for player {player_id} to {position}")
            players[player_id].position = Vec3(*position)

def process_network(task):
    if client.connected:
        client.process_net_events()
    return task.again

app.taskMgr.add(process_network, "network_task", delay=0.01)
app.run()