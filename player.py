from collections import deque
from random import randint

import settings
from datatypes import Vector, Position, Draw

class Player:

    HEAD_CHAR = "%"
    BODY_CHAR = "@"
    TAIL_CHAR = "*"

    DEAD_HEAD_CHAR = "x"
    DEAD_BODY_CHAR = "@"
    DEAD_TAIL_CHAR = "+"

    UP = Vector(0, -1)
    DOWN = Vector(0, 1)
    LEFT = Vector(-1, 0)
    RIGHT = Vector(1, 0)

    DIRECTIONS = [UP, DOWN, LEFT, RIGHT]

    keymap = {37: LEFT,
              38: UP,
              39: RIGHT,
              40: DOWN
              }

    def __init__(self, player_id, name, ws):
        self._id = player_id
        self.name = name
        self.ws = ws
        self.alive = False
        self.direction = None

    def new_snake(self, color):
        self.color = color
        self.grow = 0
        self.score = 0

        self.alive = True
        self.snake = deque()

    def render_new_snake(self):
        # try to spawn snake at some distance from world's borders
        distance = settings.INIT_LENGHT + 2
        x = randint(distance, settings.FIELD_SIZE_X - distance)
        y = randint(distance, settings.FIELD_SIZE_Y - distance)
        self.direction = self.DIRECTIONS[randint(0, 3)]
        # create snake from tail to head
        render = []
        pos = Position(x, y)
        for i in range(0, settings.INIT_LENGHT):
            self.snake.appendleft(pos)
            if i == 0:
                char = self.TAIL_CHAR
            elif i == settings.INIT_LENGHT - 1:
                char = self.HEAD_CHAR
            else:
                char = self.BODY_CHAR
            render.append(Draw(pos.x, pos.y, char, self.color))
            pos = self.next_position()
        return render

    def next_position(self):
        # next position of the snake's head
        return Position(self.snake[0].x + self.direction.xdir,
                        self.snake[0].y + self.direction.ydir)

    def render_move(self):
        # moving snake to the next position
        render = []
        new_head = self.next_position()
        self.snake.appendleft(new_head)
        # draw head in the next position
        render.append(Draw(new_head.x, new_head.y,
                           self.HEAD_CHAR, self.color))
        # draw body in the old place of head
        render.append(Draw(self.snake[1].x, self.snake[1].y,
                           self.BODY_CHAR, self.color))
        # if we grow this turn, the tail remains in place
        if self.grow > 0:
            self.grow -= 1
        else:
            # otherwise the tail moves
            old_tail = self.snake.pop()
            render.append(Draw(old_tail.x, old_tail.y, " ", 0))
            new_tail = self.snake[-1]
            render.append(Draw(new_tail.x, new_tail.y,
                               self.TAIL_CHAR, self.color))
        return render

    def render_game_over(self):
        render = []
        # dead snake
        for i, pos in enumerate(self.snake):
            if i == 0:
                render.append(Draw(pos.x, pos.y, self.DEAD_HEAD_CHAR, 0))
            elif i == len(self.snake) - 1:
                render.append(Draw(pos.x, pos.y, self.DEAD_TAIL_CHAR, 0))
            else:
                render.append(Draw(pos.x, pos.y, self.DEAD_BODY_CHAR, 0))
        return render

    def keypress(self, code):
        if not self.alive:
            return
        direction = self.keymap.get(code)
        if direction:
            # do not move in the opposite direction
            if not (self.direction and
                    direction.xdir == -self.direction.xdir and
                    direction.ydir == -self.direction.ydir):
                self.direction = direction

