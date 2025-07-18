# 🎮 Caça ao Tesouro – Jogo Multiplayer com Sockets e Pygame

Este projeto é um jogo multiplayer desenvolvido para a disciplina de Redes 1, estilo "Caça ao Tesouro". Ele utiliza a arquitetura cliente-servidor via **sockets TCP** e possui uma interface gráfica com **Pygame**, além de sprites personalizados e animações.

---

## 🎯 Propósito do Software

Este projeto tem como objetivo implementar um jogo multiplayer baseado em arquitetura cliente-servidor, utilizando comunicação via socket TCP, a fim de demonstrar conceitos de redes de computadores e comunicação distribuída de forma prática e interativa.

---

## 🔌 Escolha do Protocolo de Transporte

O protocolo TCP foi escolhido por oferecer comunicação confiável, ordenada e livre de perdas, características essenciais para um jogo em turnos onde cada mensagem deve ser entregue corretamente e na ordem em que foi enviada. A confiabilidade do TCP garante integridade na troca de mensagens como tentativas de jogada e notificações de turno, evitando inconsistências entre os jogadores.

---

## 📌 Descrição do Jogo

- Os jogadores se conectam ao servidor e disputam quem encontra o **tesouro escondido** em um tabuleiro.
- Cada jogador clica em uma casa do grid em seu turno.
- Algumas casas são **especiais**:
  - ⭐ `estrela.png`: joga 2 vezes
  - 🍌 `banana.png`: perde a vez e o adversário joga 2x
  - 🪙 `bau1.png ~ bau4.png`: animação do baú sendo aberto

---

## 🧾 Protocolo da Camada de Aplicação

As mensagens trocadas entre cliente e servidor são codificadas em JSON (uma por linha) e trafegam por conexões TCP persistentes.

### Estados possíveis do cliente:
- `waiting`: aguardando todos os jogadores ficarem prontos
- `game`: turno em andamento
- `ending`: vitória anunciada
- `game_over`: reinício

### Tipos de mensagem:

| Tipo             | Origem   | Conteúdo                                                | Ação                             |
|------------------|----------|----------------------------------------------------------|----------------------------------|
| `WELCOME`        | Servidor | `{id, grid}`                                            | Informa ID do jogador e grid     |
| `PLAYER_JOINED`  | Servidor | `{players}`                                             | Lista de jogadores conectados    |
| `PLAYER_STATUS`  | Servidor | `{player, ready}`                                       | Status de prontidão dos jogadores|
| `ALL_READY`      | Servidor | `{}`                                                    | Todos prontos → iniciar jogo     |
| `YOUR_TURN`      | Servidor | `{player}`                                              | Informa quem deve jogar          |
| `GUESS`          | Cliente  | `{x, y}`                                                | Envia tentativa de jogada        |
| `FEEDBACK`       | Servidor | `{x, y, player, hint, effect, win, next_player}`        | Retorno da jogada                |
| `GAME_OVER`      | Servidor | `{winner}`                                              | Informa quem venceu              |

Todos os clientes recebem todas as mensagens, mas só reagem àquelas relevantes ao seu estado.

---

## ⚙️ Requisitos Mínimos de Execução

- Python 3.10 ou superior
- Biblioteca `pygame` instalada
- Conexão TCP local ou em rede LAN
- Sistema operacional compatível com Pygame (Windows, Linux ou macOS)

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
git clone https://github.com/KlausAlmeida1/Caca-Tesouro-Multiplayer.git
cd Caca-Tesouro-Multiplayer
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
