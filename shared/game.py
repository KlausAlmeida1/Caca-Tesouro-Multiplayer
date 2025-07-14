import random

GRID_SIZE = 10
EFFECTS = ["extra_turn", "lose_turn"]        # tipos válidos de casa especial

class GameState:
    """
    Mantém todo o estado do jogo – independente de rede ou UI.
    """
    def __init__(self, size: int = GRID_SIZE, k_specials: int = 30):
        self.size = size
        self.k_specials = k_specials
        self.players = []                    # [(player_id, skips_left), ...]
        self.reset()

    def reset(self):
        """Reinicia o estado (tesouro, efeitos e turnos), mantendo jogadores."""
        self.treasure = self._rand_cell()
        self.turn_index = 0                  # índice no vetor players
        # limpa skips
        for p in self.players:
            p[1] = 0
        # novas casas especiais
        self.special_cells = self._spawn_specials(self.k_specials)

    # ---------- utilidades --------- #
    def _rand_cell(self):
        return (random.randrange(self.size), random.randrange(self.size))

    def _spawn_specials(self, k: int):
        specials = {}
        while len(specials) < k:
            cell = self._rand_cell()
            if cell == self.treasure:
                continue                     # não sobrescreve o tesouro
            specials[cell] = random.choice(EFFECTS)
        return specials                      # dict {(x,y): effect}

    # ---------- API usada pelo servidor --------- #
    def add_player(self, pid: str):
        self.players.append([pid, 0])      # 0 skips_left

    def _current_player(self):
        return self.players[self.turn_index][0]

    def _advance_turn(self):
        n = len(self.players)
        while True:
            self.turn_index = (self.turn_index + 1) % n
            _, skips = self.players[self.turn_index]
            if skips > 0:
                self.players[self.turn_index][1] = skips - 1  # consome skip
            else:
                break

    def guess(self, pid: str, x: int, y: int):
        """
        Processa um palpite. Retorna um dicionário com:
        hint        : str   (“mesma linha”, “3 de distância” …)
        effect      : str|None   (“extra_turn”, “lose_turn” ou None)
        win         : bool
        next_player : str ou None
        """
        if pid != self._current_player():
            raise ValueError("Not your turn")

        # --- calcula dica --- #
        if (x, y) == self.treasure:
            win = True
            hint = "Tesouro ENCONTRADO!"
        else:
            win = False
            dx = abs(x - self.treasure[0])
            dy = abs(y - self.treasure[1])
            if dx == 0 and dy != 0:
                hint = "Mesma COLUNA"
            elif dy == 0 and dx != 0:
                hint = "Mesma LINHA"
            else:
                hint = f"{dx+dy} de distância"

        # --- verifica efeito especial --- #
        effect = self.special_cells.pop((x, y), None)

        if effect == "lose_turn":
            # marca 1 rodada de pulo
            for p in self.players:
                if p[0] == pid:
                    p[1] += 1
                    break

        # --- avança ou mantém turno --- #
        if not win and effect != "extra_turn":
            self._advance_turn()

        return {"hint": hint, "effect": effect, "win": win,
                "next_player": None if win else self._current_player()}