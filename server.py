from ursinanetworking import *
import random
import threading
import time
import json as js
import sys

if len(sys.argv) < 2:
    print("Usage: python server.py <ybxl_file>")
    sys.exit(1)

ybxl_file = sys.argv[1]

with open(ybxl_file, 'r') as file:
    map_data = js.load(file)
map_data_str = js.dumps(map_data)

class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.position = self.generate_spawn_position()
        self.color = (random.random(), random.random(), random.random())
        self.name = f"Player_{player_id}"  # Varsayılan isim

    def generate_spawn_position(self):
        while True:
            pos = (random.uniform(-5, 5), 5, random.uniform(-5, 5))
            if not any(p.position == pos for p in players.values()):
                return pos

server = UrsinaNetworkingServer("localhost", 25556)
players = {}

@server.event
def onClientConnected(client):
    print(f"[SERVER] {client.id} connected!")
    players[client.id] = Player(client.id)
    client.send_message("load_map", map_data_str)
    client.send_message("your_id", client.id)
    for p_id, p in players.items():
        if p_id != client.id:
            client.send_message("spawn_player", {"id": p.id, "position": p.position, "color": p.color, "name": p.name})
    server.broadcast("spawn_player", {"id": client.id, "position": players[client.id].position, "color": players[client.id].color, "name": players[client.id].name})
    client.send_message("update_positions", {p.id: p.position for p in players.values()})

@server.event
def player_just_died(client):
    print(f"[SERVER] {client.id} just died")

@server.event
def onClientDisconnected(client):
    print(f"[SERVER] {client.id} disconnected!")
    if client.id in players:
        del players[client.id]
        server.broadcast("remove_player", {"id": client.id})

@server.event
def move(client, position):
    if not isinstance(position, (tuple, list)) or len(position) != 3:
        print(f"[ERROR] Invalid position format: {position}")
        return
    if client.id in players:
        x, y, z = position
        ground_level = 0
        max_jump_height = 10
        if y < ground_level:
            y = ground_level
        elif y > max_jump_height:
            y = max_jump_height
        players[client.id].position = (x, y, z)
        server.broadcast("update_positions", {p.id: p.position for p in players.values()})

@server.event
def set_name(client, name):
    if client.id in players:
        players[client.id].name = name
        print(f"[SERVER] {client.id} set name to {name}")
        # Tüm istemcilere güncel isimle oyuncuyu bildir
        server.broadcast("spawn_player", {"id": client.id, "position": players[client.id].position, "color": players[client.id].color, "name": name})

def run_server():
    while True:
        try:
            server.process_net_events()
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(0.01)

threading.Thread(target=run_server, daemon=True).start()
print("Server running...")