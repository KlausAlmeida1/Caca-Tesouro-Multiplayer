import json, socket, threading
from shared.game import GameState, GRID_SIZE

HOST, PORT = "0.0.0.0", 4000
MAX_PLAYERS = 2

class TreasureServer:
    def __init__(self):
        self.game = GameState()
        self.lock = threading.Lock()
        self.clients = {}         # pid -> socket
        self.ready = set()        # pids prontos

    def _send(self, sock, obj):
        data = (json.dumps(obj) + "\n").encode()
        sock.sendall(data)

    def _broadcast(self, obj):
        dead = []
        for pid, sock in self.clients.items():
            try:
                self._send(sock, obj)
            except OSError:
                dead.append(pid)
        for pid in dead:
            self.clients.pop(pid, None)

    def _handle_client(self, pid, sock):
        with sock:
            # envia boas-vindas
            self._send(sock, {"type": "WELCOME", "id": pid, "grid": GRID_SIZE})
            # informa lista de jogadores
            self._broadcast({"type": "PLAYER_JOINED", "players": list(self.clients.keys())})
            while True:
                try:
                    raw = sock.recv(4096)
                except ConnectionResetError:
                    break
                if not raw:
                    break
                for line in raw.splitlines():
                    msg = json.loads(line.decode())
                    if msg["type"] == "GUESS":
                        self._on_guess(pid, msg["x"], msg["y"])
                    elif msg["type"] == "READY":
                        self.ready.add(pid)
                        self._broadcast({"type": "PLAYER_STATUS", "player": pid, "ready": True})
                        if len(self.ready) == len(self.clients):
                            with self.lock:
                                self.game.reset()
                            # todos prontos, iniciar jogo
                            self._broadcast({"type": "ALL_READY"})
                            self.ready.clear()
                            # avisa quem começa
                            self._broadcast({"type": "YOUR_TURN",
                                              "player": self.game._current_player()})
    def _on_guess(self, pid, x, y):
            with self.lock:
                try:
                    result = self.game.guess(pid, x, y)
                except ValueError:
                    return
                packet = {"type": "FEEDBACK", "player": pid,
                        "x": x, "y": y, **result}
                self._broadcast(packet)
                if result["win"]:
                    self._broadcast({"type": "GAME_OVER", "winner": pid})
                else:
                    self._broadcast({"type": "YOUR_TURN",
                                    "player": result["next_player"]})

    def start(self):
        print(f"TreasureServer @ {HOST}:{PORT}")
        with socket.create_server((HOST, PORT)) as s:
            pid_counter = 1
            while True:
                conn, addr = s.accept()
                pid = f"P{pid_counter}"
                pid_counter += 1
                print(f"+ {pid} de {addr}")
                self.clients[pid] = conn
                self.game.add_player(pid)
                threading.Thread(target=self._handle_client,
                                 args=(pid, conn), daemon=True).start()

if __name__ == "__main__":
    TreasureServer().start()