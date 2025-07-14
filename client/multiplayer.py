import os
import sys
import json
import queue
import socket
import threading
import math
import pygame

from shared.game import GRID_SIZE

# --- Configuração de rede e tela ---
SERVER_HOST = "127.0.0.1"  # altere para o IP do servidor na LAN
SERVER_PORT = 4000
CELL = 80
WIDTH = GRID_SIZE * CELL
HEIGHT = GRID_SIZE * CELL + 100

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tesouro Multiplayer")
font = pygame.font.SysFont(None, 28)
clock = pygame.time.Clock()

# --- Carregamento de sprites ---
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
IMG_PATH = os.path.join(ROOT_PATH, "imagens")
sprites = {
    "base":    pygame.image.load(os.path.join(IMG_PATH, "base.png")),
    "normal":  pygame.image.load(os.path.join(IMG_PATH, "normal.png")),
    "banana":  pygame.image.load(os.path.join(IMG_PATH, "banana.png")),
    "estrela": pygame.image.load(os.path.join(IMG_PATH, "estrela.png")),
    "bau": [
        pygame.image.load(os.path.join(IMG_PATH, f"bau{i}.png"))
        for i in range(1, 5)
    ],
    "inicial": pygame.image.load(os.path.join(IMG_PATH, "inicial.png")),
    "vitoria": pygame.image.load(os.path.join(IMG_PATH, "vitoria.png")),
}

# --- Utilitário para texto legível ---

def blit_text(surf, text, pos, *, color=(255, 255, 255), outline=(0, 0, 0), bg_alpha=160, padding=4):
    """Desenha texto com tarja semitransparente + contorno para garantir contraste."""
    txt = font.render(text, True, color)
    w, h = txt.get_size()
    bg = pygame.Surface((w + 2 * padding, h + 2 * padding), pygame.SRCALPHA)
    bg.fill((0, 0, 0, bg_alpha))
    surf.blit(bg, (pos[0] - padding, pos[1] - padding))
    if outline:
        out = font.render(text, True, outline)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            surf.blit(out, (pos[0] + dx, pos[1] + dy))
    surf.blit(txt, pos)

# --- Estado global ---
mode = "waiting"  # waiting, game, ending, game_over
players = []
ready_status = {}
winner = None
hint_text = ""
end_start = None

grid = [["base"] * GRID_SIZE for _ in range(GRID_SIZE)]

# --- Animações ---
FRAME_DURATION = 150  # animação do baú
bau_animations = {}
CLICK_ANIM_DURATION = 400  # ms para "pulo" da casa
click_animations = {}


def get_bau_frame(start_ticks: int) -> int:
    elapsed = pygame.time.get_ticks() - start_ticks
    idx = elapsed // FRAME_DURATION
    return min(idx, len(sprites["bau"]) - 1)


def get_click_scale(start_ticks: int) -> float:
    t = pygame.time.get_ticks() - start_ticks
    if t >= CLICK_ANIM_DURATION:
        return 1.0
    return 1.0 + 0.2 * math.sin(math.pi * t / CLICK_ANIM_DURATION)


# --- Thread de rede ---

def net_thread(sock: socket.socket, inbox: queue.Queue):
    buff = b""
    while True:
        try:
            data = sock.recv(4096)
        except OSError:
            break
        if not data:
            break
        buff += data
        while b"\n" in buff:
            line, buff = buff.split(b"\n", 1)
            try:
                inbox.put(json.loads(line.decode()))
            except json.JSONDecodeError:
                pass


# --- Loop principal ---

def main():
    global mode, players, ready_status, winner, hint_text, end_start, grid

    sock = socket.create_connection((SERVER_HOST, SERVER_PORT))
    inbox = queue.Queue()
    threading.Thread(target=net_thread, args=(sock, inbox), daemon=True).start()

    player_id = None
    my_turn = False
    running = True

    while running:
        # --- Checa animação de fim ---
        if mode == "ending" and end_start and pygame.time.get_ticks() - end_start >= 5000:
            mode = "game_over"

        # --- Processa mensagens da rede ---
        try:
            while True:
                msg = inbox.get_nowait()
                t = msg.get("type")
                if t == "WELCOME":
                    player_id = msg["id"]
                    hint_text = "Aguardando jogadores."
                elif t == "PLAYER_JOINED":
                    players = msg["players"]
                    for p in players:
                        ready_status.setdefault(p, False)
                elif t == "PLAYER_STATUS":
                    ready_status[msg["player"]] = msg["ready"]
                elif t == "ALL_READY":
                    mode = "game"
                    grid = [["base"] * GRID_SIZE for _ in range(GRID_SIZE)]
                    bau_animations.clear()
                    click_animations.clear()
                    winner = None
                    hint_text = ""
                elif t == "YOUR_TURN":
                    my_turn = (msg["player"] == player_id)
                    hint_text = "É o seu turno!" if my_turn else f"Aguardando {msg['player']}."
                elif t == "FEEDBACK":
                    x, y = msg["x"], msg["y"]
                    if msg["win"]:
                        grid[y][x] = "bau"
                        bau_animations[(x, y)] = pygame.time.get_ticks()
                    elif msg["effect"] == "extra_turn":
                        grid[y][x] = "estrela"
                    elif msg["effect"] == "lose_turn":
                        grid[y][x] = "banana"
                    else:
                        grid[y][x] = "normal"
                    click_animations[(x, y)] = pygame.time.get_ticks()
                    if msg["player"] == player_id:
                        hint_text = msg["hint"]
                elif t == "GAME_OVER":
                    winner = msg["winner"]
                    mode = "ending"
                    end_start = pygame.time.get_ticks()
                inbox.task_done()
        except queue.Empty:
            pass

        # --- Eventos de input ---
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if mode == "waiting":
                    btn = pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2 + 20, 120, 50)
                    if btn.collidepoint(mx, my) and not ready_status.get(player_id, False):
                        sock.sendall((json.dumps({"type": "READY"}) + "\n").encode())
                        ready_status[player_id] = True
                elif mode == "game" and my_turn and not winner:
                    if my < GRID_SIZE * CELL:
                        gx, gy = mx // CELL, my // CELL
                        # --- Impede clique em casas já reveladas ---
                        if grid[gy][gx] == "base":
                            pkt = {"type": "GUESS", "x": gx, "y": gy}
                            sock.sendall((json.dumps(pkt) + "\n").encode())
                            my_turn = False
                        else:
                            hint_text = "Casa já revelada! Escolha outra."
                elif mode == "game_over":
                    mode = "waiting"
                    for p in ready_status:
                        ready_status[p] = False

        # --- Renderização ---
        if mode in ("game", "ending"):
            screen.fill((30, 30, 30))
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    tipo = grid[y][x]
                    if tipo == "bau":
                        img = sprites["bau"][get_bau_frame(bau_animations.get((x, y)))]
                    else:
                        img = sprites[tipo]

                    start = click_animations.get((x, y))
                    if start:
                        scale = get_click_scale(start)
                        if scale == 1.0:
                            click_animations.pop((x, y), None)
                        size = int(CELL * scale)
                        offset = (CELL - size) // 2
                        scaled = pygame.transform.scale(img, (size, size))
                        screen.blit(scaled, (x * CELL + offset, y * CELL + offset))
                    else:
                        screen.blit(pygame.transform.scale(img, (CELL, CELL)), (x * CELL, y * CELL))

            blit_text(screen, f"Você é o jogador: {player_id}", (10, HEIGHT - 80))
            blit_text(screen, hint_text, (10, HEIGHT - 50), color=(255, 255, 0))

        elif mode == "waiting":
            screen.blit(pygame.transform.scale(sprites["inicial"], (WIDTH, HEIGHT)), (0, 0))
            for i, p in enumerate(players[:4]):
                status = "Pronto" if ready_status.get(p) else "Aguardando"
                blit_text(screen, f"{p}: {status}", (WIDTH // 2 - 100, HEIGHT // 2 - 50 + i * 30), color=(255, 255, 0))

            btn = pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2 + 20, 120, 50)
            color = (0, 200, 0) if not ready_status.get(player_id, False) else (100, 100, 100)
            pygame.draw.rect(screen, color, btn)
            blit_text(
                screen,
                "Pronto" if not ready_status.get(player_id, False) else "Aguardando",
                (btn.x + btn.width // 2 - font.size("Pronto")[0] // 2, btn.y + btn.height // 2 - font.size("Pronto")[1] // 2),
                color=(0, 0, 0),
                outline=None,
                bg_alpha=0,
            )

        else:  # game_over
            screen.blit(pygame.transform.scale(sprites["vitoria"], (WIDTH, HEIGHT)), (0, 0))
            msg = f"{winner} venceu! Clique para reiniciar"
            blit_text(screen, msg, (WIDTH // 2 - font.size(msg)[0] // 2, HEIGHT // 2))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sock.close()
    sys.exit()


if __name__ == "__main__":
    main()
