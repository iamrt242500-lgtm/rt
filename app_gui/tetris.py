import tkinter as tk
import random
from dataclasses import dataclass

BOARD_WIDTH = 10
BOARD_HEIGHT = 20
CELL_SIZE = 24

# Standard tetromino shapes with rotation states (list of (x,y) relative coords)
SHAPES = {
    'I': [ [(0,0),(1,0),(2,0),(3,0)], [(2,-1),(2,0),(2,1),(2,2)] ],
    'O': [ [(0,0),(1,0),(0,1),(1,1)] ],
    'T': [ [(0,0),(1,0),(2,0),(1,1)], [(1,0),(0,1),(1,1),(1,2)], [(1,0),(0,1),(1,1),(2,1)], [(0,0),(0,1),(1,1),(0,2)] ],
    'S': [ [(1,0),(2,0),(0,1),(1,1)], [(0,0),(0,1),(1,1),(1,2)] ],
    'Z': [ [(0,0),(1,0),(1,1),(2,1)], [(1,0),(0,1),(1,1),(0,2)] ],
    'J': [ [(0,0),(0,1),(1,1),(2,1)], [(0,0),(1,0),(0,1),(0,2)], [(0,0),(1,0),(2,0),(2,1)], [(1,0),(1,1),(0,2),(1,2)] ],
    'L': [ [(2,0),(0,1),(1,1),(2,1)], [(0,0),(0,1),(0,2),(1,2)], [(0,0),(1,0),(2,0),(0,1)], [(0,0),(1,0),(1,1),(1,2)] ],
}

# Color mapping (requested colors): red, blue, yellow, orange, green, purple, cyan
COLORS = {
    'I': '#00bcd4',  # cyan
    'O': '#ffeb3b',  # yellow
    'T': '#9c27b0',  # purple
    'S': '#4caf50',  # green
    'Z': '#f44336',  # red
    'J': '#1976d2',  # blue
    'L': '#ff9800',  # orange
}

SCORE_TABLE = {1:100, 2:300, 3:500, 4:800}
LEVEL_LINES = 10
INITIAL_DELAY = 1000  # ms
MIN_DELAY = 80
DELAY_STEP = 70

@dataclass
class Piece:
    shape: str
    rotation: int
    x: int
    y: int

class TetrisGame(tk.Frame):
    def __init__(self, master, on_game_over=None):
        super().__init__(master)
        self.on_game_over = on_game_over
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current = None
        self.next_shape = self.random_shape()
        self.score = 0
        self.lines = 0
        self.level = 0
        self.delay = INITIAL_DELAY
        self.running = True
        self.game_over_flag = False

        # UI Layout
        self.canvas = tk.Canvas(self, width=BOARD_WIDTH*CELL_SIZE, height=BOARD_HEIGHT*CELL_SIZE, bg='#111')
        self.canvas.grid(row=0, column=0, rowspan=20)
        side = tk.Frame(self)
        side.grid(row=0, column=1, sticky='n', padx=12)
        self.lbl_score = tk.Label(side, text='Score: 0', font=('Arial', 12))
        self.lbl_score.pack(anchor='w')
        self.lbl_lines = tk.Label(side, text='Lines: 0', font=('Arial', 12))
        self.lbl_lines.pack(anchor='w')
        self.lbl_level = tk.Label(side, text='Level: 0', font=('Arial', 12))
        self.lbl_level.pack(anchor='w')
        tk.Label(side, text='Next:', font=('Arial', 12, 'bold')).pack(anchor='w', pady=(10,2))
        self.preview = tk.Canvas(side, width=6*CELL_SIZE, height=5*CELL_SIZE, bg='#222', highlightthickness=0)
        self.preview.pack()
        self.btn_restart = tk.Button(side, text='Restart (R)', command=self.restart)
        self.btn_restart.pack(pady=10)
        controls_txt = 'Controls:\n←/→: Move\n↑: Rotate\n↓: Soft Drop\nSpace: Hard Drop\nR: Restart'
        tk.Label(side, text=controls_txt, justify='left', font=('Arial', 10)).pack(anchor='w', pady=(8,0))

        self.spawn_piece()
        self.draw_preview()
        self.draw()

        self.bind_all('<Key>', self.on_key)
        self.after(self.delay, self.step)

    def random_shape(self):
        return random.choice(list(SHAPES.keys()))

    def spawn_piece(self):
        shape = self.next_shape
        self.next_shape = self.random_shape()
        # center spawn
        self.current = Piece(shape=shape, rotation=0, x=BOARD_WIDTH//2 - 2, y=0)
        if self.collision(self.current):
            self.game_over()

    def rotation_states(self, piece):
        return SHAPES[piece.shape]

    def cells(self, piece):
        states = self.rotation_states(piece)
        coords = states[piece.rotation % len(states)]
        return [(piece.x + cx, piece.y + cy) for (cx, cy) in coords]

    def collision(self, piece):
        for x,y in self.cells(piece):
            if x < 0 or x >= BOARD_WIDTH or y < 0 or y >= BOARD_HEIGHT:
                return True
            if y >=0 and self.board[y][x] is not None:
                return True
        return False

    def lock_piece(self):
        for x,y in self.cells(self.current):
            if 0 <= y < BOARD_HEIGHT:
                self.board[y][x] = COLORS[self.current.shape]
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        new_board = [row for row in self.board if any(cell is None for cell in row)]
        cleared = BOARD_HEIGHT - len(new_board)
        while len(new_board) < BOARD_HEIGHT:
            new_board.insert(0, [None]*BOARD_WIDTH)
        self.board = new_board
        if cleared > 0:
            self.lines += cleared
            self.score += SCORE_TABLE.get(cleared, 100*cleared)
            prev_level = self.level
            self.level = self.lines // LEVEL_LINES
            if self.level != prev_level:
                # speed up
                self.delay = max(MIN_DELAY, INITIAL_DELAY - self.level*DELAY_STEP)
            self.update_labels()

    def update_labels(self):
        self.lbl_score.config(text=f'Score: {self.score}')
        self.lbl_lines.config(text=f'Lines: {self.lines}')
        self.lbl_level.config(text=f'Level: {self.level}')

    def step(self):
        if not self.running:
            return
        if self.game_over_flag:
            return
        # try move down
        nxt = Piece(self.current.shape, self.current.rotation, self.current.x, self.current.y + 1)
        if self.collision(nxt):
            # lock
            self.lock_piece()
        else:
            self.current = nxt
        self.draw()
        self.after(self.delay, self.step)

    def on_key(self, event):
        if self.game_over_flag and event.keysym.lower() != 'r':
            return
        k = event.keysym
        if k in ['Left','Right']:
            dx = -1 if k=='Left' else 1
            nxt = Piece(self.current.shape, self.current.rotation, self.current.x + dx, self.current.y)
            if not self.collision(nxt):
                self.current = nxt
                self.draw()
        elif k == 'Up':
            nxt = Piece(self.current.shape, self.current.rotation + 1, self.current.x, self.current.y)
            if not self.collision(nxt):
                self.current = nxt
                self.draw()
        elif k == 'Down':
            nxt = Piece(self.current.shape, self.current.rotation, self.current.x, self.current.y + 1)
            if not self.collision(nxt):
                self.current = nxt
                self.draw()
        elif k == 'space':
            # hard drop
            temp = Piece(self.current.shape, self.current.rotation, self.current.x, self.current.y)
            while True:
                nxt = Piece(temp.shape, temp.rotation, temp.x, temp.y + 1)
                if self.collision(nxt):
                    break
                temp = nxt
            self.current = temp
            self.lock_piece()
            self.draw()
        elif k.lower() == 'r':
            self.restart()

    def restart(self):
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.lines = 0
        self.level = 0
        self.delay = INITIAL_DELAY
        self.game_over_flag = False
        self.next_shape = self.random_shape()
        self.spawn_piece()
        self.update_labels()
        self.draw_preview()
        self.draw()
        if not self.running:
            self.running = True
            self.after(self.delay, self.step)

    def game_over(self):
        self.game_over_flag = True
        self.draw()  # to overlay text
        if self.on_game_over:
            self.on_game_over()

    def draw_preview(self):
        self.preview.delete('all')
        states = SHAPES[self.next_shape][0]
        min_x = min(x for x,_ in states)
        min_y = min(y for _,y in states)
        for cx, cy in states:
            x = (cx - min_x + 1) * CELL_SIZE
            y = (cy - min_y + 1) * CELL_SIZE
            self.preview.create_rectangle(x, y, x+CELL_SIZE, y+CELL_SIZE, fill=COLORS[self.next_shape], outline='#333')

    def draw(self):
        self.canvas.delete('all')
        # grid
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                color = self.board[y][x]
                if color:
                    self.canvas.create_rectangle(x*CELL_SIZE, y*CELL_SIZE, (x+1)*CELL_SIZE, (y+1)*CELL_SIZE, fill=color, outline='#222')
                else:
                    self.canvas.create_rectangle(x*CELL_SIZE, y*CELL_SIZE, (x+1)*CELL_SIZE, (y+1)*CELL_SIZE, fill='#181818', outline='#202020')
        # current piece
        if not self.game_over_flag:
            for x,y in self.cells(self.current):
                if y >=0:
                    self.canvas.create_rectangle(x*CELL_SIZE, y*CELL_SIZE, (x+1)*CELL_SIZE, (y+1)*CELL_SIZE, fill=COLORS[self.current.shape], outline='#222')
        # game over overlay
        if self.game_over_flag:
            self.canvas.create_rectangle(0, BOARD_HEIGHT*CELL_SIZE//3, BOARD_WIDTH*CELL_SIZE, BOARD_HEIGHT*CELL_SIZE*2//3, fill='#000000', stipple='gray50')
            self.canvas.create_text(BOARD_WIDTH*CELL_SIZE//2, BOARD_HEIGHT*CELL_SIZE//2 - 20, text='GAME OVER', fill='white', font=('Arial', 24, 'bold'))
            self.canvas.create_text(BOARD_WIDTH*CELL_SIZE//2, BOARD_HEIGHT*CELL_SIZE//2 + 10, text='Press R to Restart', fill='white', font=('Arial', 14))
        self.draw_preview()

# Convenience to integrate
class TetrisFrame(tk.Frame):
    def __init__(self, master, username: str):
        super().__init__(master)
        header = tk.Label(self, text=f'Tetris - Player: {username}', font=('Arial', 14, 'bold'))
        header.pack(anchor='w', pady=(4,8), padx=4)
        game = TetrisGame(self)
        game.pack()
