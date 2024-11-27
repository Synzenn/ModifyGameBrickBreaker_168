import tkinter as tk
import random


class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y, speed):
        self.radius = 10
        self.direction = [random.choice([-1, 1]), -1]
        self.speed = speed
        item = canvas.create_oval(
            x - self.radius, y - self.radius, x + self.radius, y + self.radius, fill='white'
        )
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 100
        self.height = 15
        self.ball = None
        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2, x + self.width / 2, y + self.height / 2, fill='#FF5733'
        )
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)

    def change_color(self):
        colors = ['#FF5733', '#48C9B0', '#F4D03F', '#8E44AD', '#1ABC9C']
        new_color = random.choice(colors)
        self.canvas.itemconfig(self.item, fill=new_color)


class Brick(GameObject):
    COLORS = {1: '#1F618D', 2: '#48C9B0', 3: '#F4D03F'}

    def __init__(self, canvas, x, y, hits):
        self.width = 60
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2, x + self.width / 2, y + self.height / 2, fill=color, tags='brick'
        )
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.level = 1
        self.lives = 3
        self.width = 640
        self.height = 480
        self.canvas = tk.Canvas(self, bg='#D7EAF5', width=self.width, height=self.height)
        self.canvas.pack()
        self.pack()
        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 400)
        self.items[self.paddle.item] = self.paddle
        self.setup_level()
        self.hud = None
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>', lambda _: self.paddle.move(-15))
        self.canvas.bind('<Right>', lambda _: self.paddle.move(15))

    def setup_level(self):
        for x in range(5, self.width - 5, 65):
            self.add_brick(x + 32.5, 50, 3)
            self.add_brick(x + 32.5, 80, 2)
            self.add_brick(x + 32.5, 110, 1)

    def setup_game(self):
        self.add_ball()
        self.update_hud()
        self.text = self.draw_text(320, 240, 'Tekan Spasi untuk Mulai!', size='30')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 380, speed=4 + self.level)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='20'):
        font = ('Arial', size)
        return self.canvas.create_text(x, y, text=text, font=font)

    def update_hud(self):
        text = f'Nyawa: {self.lives} | Level: {self.level}'
        if self.hud is None:
            self.hud = self.draw_text(70, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.level += 1
            self.setup_level()
            self.setup_game()
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = 0
            self.lives -= 1
            if self.lives < 0:
                self.draw_text(320, 240, 'Game Over!')
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)
        if self.paddle in objects:
            self.paddle.change_color()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Permainan Brick Breaker')
    game = Game(root)
    game.mainloop()
