# 🎮 Caça ao Tesouro – Jogo Multiplayer com Sockets e Pygame

Este projeto é um jogo multiplayer desenvolvido para a disciplina de Redes 1, estilo "Caça ao Tesouro". Ele utiliza a arquitetura cliente-servidor via **sockets TCP** e possui uma interface gráfica com **Pygame**, além de sprites personalizados e animações.

---

## 📌 Descrição do Jogo

- Os jogadores se conectam ao servidor e disputam quem encontra o **tesouro escondido** em um tabuleiro.
- Cada jogador clica em uma casa do grid em seu turno.
- Algumas casas são **especiais**:
  - ⭐ `estrela.png`: joga 2 vezes
  - 🍌 `banana.png`: perde a vez e o adversário joga 2x
  - 🪙 `bau1.png ~ bau4.png`: animação do baú sendo aberto

---

## ✅ Pré-requisitos

- Python 3.10 ou superior
- Pygame instalado

### Instalar Pygame:
```bash
pip install pygame
```

---

## 📁 Estrutura de Pastas

```
CaçaTesouro/
├── client/
│   ├── multiplayer.py
│   ├── __init__.py
├── server/
│   ├── main.py
├── shared/
│   ├── game.py
├── imagens/
│   ├── base.png
│   ├── normal.png
│   ├── estrela.png
│   ├── banana.png
│   ├── bau1.png
│   ├── bau2.png
│   ├── bau3.png
│   ├── bau4.png
├── run_server.bat
├── run_client.bat
└── README.md
```

---

## 🕹️ Como Jogar

### 1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/nome-do-repo.git
cd nome-do-repo
```

### 2. Rode o servidor:
Clique duas vezes em:
```
run_server.bat
```

> O servidor será iniciado minimizado no plano de fundo.

### 3. Rode o cliente:
Clique duas vezes em:
```
run_client.bat
```

> A interface do jogo será aberta com Pygame. Para jogar com mais de um jogador, abra múltiplos clientes (no mesmo PC ou em máquinas diferentes).

---

## 🌐 Jogando em rede local (LAN)

1. Descubra o IP da máquina que rodará o servidor (ex: `192.168.0.42`)
2. No arquivo `client/multiplayer.py`, altere:
```python
SERVER_HOST = "127.0.0.1"
```
para:
```python
SERVER_HOST = "192.168.0.42"
```
3. Execute normalmente o servidor no PC principal, e os clientes em outras máquinas conectadas na mesma rede.

---

## 📡 Protocolo de Comunicação

- Conexão: TCP
- Mensagens em JSON (1 por linha)
- Tipos de mensagens:
  - `WELCOME` → ID do jogador e tamanho do grid
  - `YOUR_TURN` → informa de quem é a vez
  - `GUESS` → jogador envia palpite `{x, y}`
  - `GAME_OVER` → anuncia o vencedor
