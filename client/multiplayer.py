# -*- coding: utf-8 -*-
import os
import json
import queue
import socket
import threading
import pygame
import sys

from shared.game import GRID_SIZE

# --- Configurações de Rede e Tela --- #
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 4000
CELL = 80
WIDTH = GRID_SIZE * CELL
HEIGHT = GRID_SIZE * CELL + 100  # espaço para HUD

# --- Inicialização Pygame --- #
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tesouro Multiplayer")
font = pygame.font.SysFont(None, 28)
clock = pygame.time.Clock()

# --- Carregamento de Sprites --- #
IMG_PATH = os.path.join(os.path.dirname(__file__), "../imagens")

sprites = {
    "base":    pygame.image.load(os.path.join(IMG_PATH, "base.png")),
    "normal":  pygame.image.load(os.path.join(IMG_PATH, "normal.png")),
    "banana":  pygame.image.load(os.path.join(IMG_PATH, "banana.png")),
    "estrela": pygame.image.load(os.path.join(IMG_PATH, "estrela.png")),
    "bau": [
        pygame.image.load(os.path.join(IMG_PATH, f"bau{i}.png"))
        for i in range(1, 5)
    ]
}

# --- Estado do Jogo no Cliente --- #
# grid identifica o sprite a desenhar em cada célula
grid = [["base"] * GRID_SIZE for _ in range(GRID_SIZE)]

# Para cada baú encontrado, guardamos o instante em que começou a animação
bau_animations = {}  # key=(x,y) -> start_ticks

# duração de cada frame da animação do baú (em milissegundos)
FRAME_DURATION = 150

def get_bau_frame(start_ticks: int) -> int:
    """Retorna o índice do frame atual da animação do baú."""
    elapsed = pygame.time.get_ticks() - start_ticks
    idx = elapsed // FRAME_DURATION
    if idx >= len(sprites["bau"]):
        idx = len(sprites["bau"]) - 1
    return idx

# ------------------- Thread de Rede ------------------- #
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

# ------------------- Função Principal ------------------- #
def main():
    # Conexão e thread de recepção
    sock = socket.create_connection((SERVER_HOST, SERVER_PORT))
    inbox = queue.Queue()
    threading.Thread(target=net_thread, args=(sock, inbox), daemon=True).start()

    player_id = None
    current_turn = None
    my_turn = False
    hint_text = ""
    winner = None

    running = True
    while running:
        # --- Processa Mensagens de Rede --- #
        try:
            while True:
                msg = inbox.get_nowait()
                t = msg.get("type")
                if t == "WELCOME":
                    player_id = msg["id"]
                elif t == "YOUR_TURN":
                    current_turn = msg["player"]
                    my_turn = (current_turn == player_id)
                    hint_text = "É o seu turno!" if my_turn else f"Aguardando {current_turn}..."
                elif t == "FEEDBACK":
                    x, y = msg["x"], msg["y"]
                    # Define tipo de sprite
                    if msg["win"]:
                        grid[y][x] = "bau"
                        bau_animations[(x, y)] = pygame.time.get_ticks()
                    elif msg["effect"] == "extra_turn":
                        grid[y][x] = "estrela"
                    elif msg["effect"] == "lose_turn":
                        grid[y][x] = "banana"
                    else:
                        grid[y][x] = "normal"

                    # Atualiza texto de dica (apenas para o próprio jogador)
                    if msg["player"] == player_id:
                        hint_text = msg["hint"]
                        if msg["effect"] == "extra_turn":
                            hint_text += "  | BÔNUS: joga de novo!"
                        elif msg["effect"] == "lose_turn":
                            hint_text += "  | PENALIDADE: perde próxima vez"
                elif t == "GAME_OVER":
                    winner = msg["winner"]
                    if winner == player_id:
                        hint_text = "🎉 VOCÊ venceu! 🎉"
                    else:
                        hint_text = f"{winner} venceu! 😭"
                inbox.task_done()
        except queue.Empty:
            pass

        # --- Entrada de Mouse --- #
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and my_turn and not winner:
                mx, my = ev.pos
                if my < GRID_SIZE * CELL:
                    gx, gy = mx // CELL, my // CELL
                    pkt = {"type": "GUESS", "x": gx, "y": gy}
                    sock.sendall((json.dumps(pkt) + "\n").encode())
                    my_turn = False

        # --- Render --- #
        screen.fill((30, 30, 30))

        # Desenha cada célula com o sprite apropriado
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tipo = grid[y][x]
                if tipo == "bau":
                    start = bau_animations.get((x, y), None)
                    if start is not None:
                        frame = get_bau_frame(start)
                        img = sprites["bau"][frame]
                    else:
                        img = sprites["bau"][-1]
                else:
                    img = sprites[tipo]

                img = pygame.transform.scale(img, (CELL, CELL))
                screen.blit(img, (x * CELL, y * CELL))

        # HUD: jogador e dica
        if player_id:
            status1 = font.render(f"Você é o jogador: {player_id}", True, (255, 255, 255))
            status2 = font.render(hint_text, True, (255, 255, 0))
            screen.blit(status1, (10, HEIGHT - 60))
            screen.blit(status2, (10, HEIGHT - 30))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sock.close()
    sys.exit()

if __name__ == "__main__":
    main()
