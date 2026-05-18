# this program visualizes activities with pyglet

import activity_recognizer as activity
import pyglet


WINDOW_W, WINDOW_H = 400, 700
ITEM_W, ITEM_H = 320, 60
BG_COLOR = (20 / 255, 20 / 255, 40 / 255, 1.0)  # dark blue

class TrainerApp:
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        self._build_ui()

    def _build_ui(self):
        return

    def update(self, dt):
        return

    def draw(self):
        self.batch.draw()


def main():
    win = pyglet.window.Window(WINDOW_W, WINDOW_H, caption="Fitness Trainer", resizable=False)
    pyglet.gl.glClearColor(*BG_COLOR)
    app = TrainerApp()
    recognizer = activity.ActivityRecognizer()

    @win.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.Q:
            pyglet.app.exit()            

    @win.event
    def on_draw():
        win.clear()
        app.draw()

    def tick(dt):
        recognizer.tick(dt)
        app.update(dt)

    pyglet.clock.schedule_interval(tick, 1 / 60)
    with recognizer:
        pyglet.app.run()


if __name__ == "__main__":
    main()