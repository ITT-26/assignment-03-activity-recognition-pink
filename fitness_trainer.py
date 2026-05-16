# this program visualizes activities with pyglet
from enum import Enum
import activity_recognizer as activity
import pyglet

WINDOW_W, WINDOW_H = 400, 600
# ITEM_W, ITEM_H = 320, 60
# BG_COLOR = (20 / 255, 20 / 255, 40 / 255, 1.0)  # dark blue

class Placement(Enum):
    UNDEFINED = 1
    HAND = 2
    POCKET = 3

class Activity(Enum):
    JUMPINGJACK = 0
    LIFTING = 1
    ROWING = 2
    RUNNING = 3

class CustomButton(pyglet.shapes.Rectangle):
    def __init__(self, x, y, width, height, text, color=(0, 0, 0), highlight_color=(115, 190, 181), font_name='Calibri', font_size=20):
        super().__init__(x, y, width, height, color)
        self.x = x
        self.y = y
        self.width = width
        self.is_hovered = False
        self.origin_color = color
        self.color = color
        self.highlight_color = highlight_color
        text_x = x + width / 2
        text_y = y + height / 2
        self.text_content = text
        self.text = pyglet.text.Label(text, font_name=font_name, font_size=font_size, x=text_x, y=text_y, anchor_x='center', anchor_y='center')


    def is_point_inside(self, x, y):
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def set_hovered(self, is_hovered):
        self.is_hovered = is_hovered
        if self.is_hovered:
            self.color = self.highlight_color
        else:
            self.color = self.origin_color

    def update_values(self):
        text_x = self.x + self.width / 2
        text_y = self.y + self.height / 2
        self.text.text = self.text_content
        self.text.x = text_x
        self.text.y = text_y

    def draw(self):
        super().draw()
        self.text.draw()



class TrainerApp:
    def __init__(self):
        self.window_dimensions = {'width': 800, 'height': 600}
        self.sprite_dimensions = {'width': 360, 'height': 460}
        self.sprite_coordinates = {'x_one': 20, 'y_one': 20, 'x_two': 420, 'y_two': 20}
        self.button_coordinates = {'x_one': 20, 'y_one': 50, 'x_two': 420, 'y_two': 50}
        self.button_dimensions = {'width': 360, 'height': 500}
        self.background_color = (20 / 255, 20 / 255, 40 / 255, 1.0)
        self.placement_button_hand = None
        self.placement_button_pocket = None
        self.cursor_default = None
        self.cursor_pointer = None

        notif_x = self.window_dimensions['width'] / 2
        notif_y = 20
        self.placement_notif = pyglet.text.Label('', x=notif_x, y=notif_y, anchor_x='center', anchor_y='center', font_name='Calibri', font_size=16)

        self.sprites = {}

        self.sensor_placement = Placement.UNDEFINED
        self.active_category = None
        self.batch = pyglet.graphics.Batch()
        self._init_sprites()
        self._build_ui()

    def define_cursors(self, default, pointer):
        if default is not None:
            self.cursor_default = default
        if pointer is not None:
            self.cursor_pointer = pointer

    def set_sensor_placement(self, placement: Placement):
        self.sensor_placement = placement

    def get_sensor_placement(self) -> Placement:
        return self.sensor_placement

    def set_active_category(self, category: Activity):
        self.active_category = category

    def get_active_category(self) -> Activity:
        return self.active_category

    def _init_sprites(self):
        """
        Create sprites for each activity category by loading all images from assets. Store sprites in a dict for easy
        key access later.
        """
        for activity_cat in Activity:
            sprite = pyglet.sprite.Sprite(
                pyglet.image.load(f'img/{activity_cat.name.lower()}_1.png'),
                x=self.sprite_coordinates['x_one'],
                y=self.sprite_coordinates['y_one']
            )


            sprite_two = pyglet.sprite.Sprite(
                pyglet.image.load(f'img/{activity_cat.name.lower()}_2.png'),
                x=self.sprite_coordinates['x_two'],
                y=self.sprite_coordinates['y_two']
            )

            self._fit_sprite(sprite, self.sprite_dimensions['width'], self.sprite_dimensions['height'])
            self._fit_sprite(sprite_two, self.sprite_dimensions['width'], self.sprite_dimensions['height'])

            self.sprites[activity_cat] = [sprite, sprite_two]

    def _fit_sprite(self, sprite, target_width, target_height):
        """
        Scales a sprite to fit the target dimensions.
        :param sprite: the sprite to fit
        :param target_width: desired width
        :param target_height: desired height
        :return:
        """
        scale = min(
            target_width / sprite.width,
            target_height / sprite.height
        )
        sprite.scale = scale


    def _build_ui(self):
        self.placement_button_hand = CustomButton(
            self.button_coordinates['x_one'],
            self.button_coordinates['y_one'],
            self.button_dimensions['width'],
            self.button_dimensions['height'],
            'Sensor will be held in hand'
        )
        self.placement_button_pocket = CustomButton(
            self.button_coordinates['x_two'],
            self.button_coordinates['y_two'],
            self.button_dimensions['width'],
            self.button_dimensions['height'],
            'Sensor will be in pocket'
        )

    def handle_click(self, x, y, button, modifiers):
        print(f'Registered Mouse button press at {x}, {y}')
        # Change sensor placement value depending on what button is pressed
        if self.placement_button_hand.is_hovered:
            self.sensor_placement = Placement.HAND
            self.display_notif('Sensor placement was set to \'hand\'')
        if self.placement_button_pocket.is_hovered:
            self.sensor_placement = Placement.POCKET
            self.display_notif('Sensor placement was set to \'pocket\'')

        # If a button was pressed, rearrange the buttons
        if self.sensor_placement is not Placement.UNDEFINED:
            self.rearrange_placement_buttons()

    def display_notif(self, msg):
        self.placement_notif.text = msg
        pyglet.clock.schedule_once(self.reset_notif, 3)

    def reset_notif(self, dt):
        print('Resetting notif')
        self.placement_notif.text = ''

    def rearrange_placement_buttons(self):
        self.placement_button_hand.x = 20
        self.placement_button_hand.y = 520
        self.placement_button_hand.width = 360
        self.placement_button_hand.height = 80
        self.placement_button_hand.text_content = 'Click here for hand mode'

        self.placement_button_pocket.x = 420
        self.placement_button_pocket.y = 520
        self.placement_button_pocket.width = 360
        self.placement_button_pocket.height = 80
        self.placement_button_pocket.text_content = 'Click here for pocket mode'

        self.placement_button_hand.update_values()
        self.placement_button_pocket.update_values()

    def handle_mouse_move(self, x, y, dx, dy) -> str:
        #print(f'Registered Mouse move to {x}, {y}')
        if self.placement_button_hand.is_point_inside(x, y):
            self.placement_button_hand.set_hovered(True)
            return 'pointer'
        else:
            self.placement_button_hand.set_hovered(False)

        if self.placement_button_pocket.is_point_inside(x, y):
            self.placement_button_pocket.set_hovered(True)
            return 'pointer'

        else:
            self.placement_button_pocket.set_hovered(False)
        return 'default'


    def update(self, dt):
        return

    def draw(self):

        self.placement_button_hand.draw()
        self.placement_button_pocket.draw()
        # Check which sprites need to be drawn
        active_sprites = None if self.active_category is None else self.sprites[self.active_category]
        if active_sprites is not None:
            for sprite in active_sprites:
                sprite.draw()
        self.placement_notif.draw()

    def _draw_sensor_placement_selection(self):
        self.placement_button_hand.draw()
        self.placement_button_pocket.draw()

def main():
    win = pyglet.window.Window(800, 600, caption="Fitness Trainer", resizable=False)
    app = TrainerApp()
    pyglet.gl.glClearColor(*app.background_color)
    recognizer = activity.ActivityRecognizer()

    app.define_cursors(win.get_system_mouse_cursor(win.CURSOR_DEFAULT), win.get_system_mouse_cursor(win.CURSOR_HAND))

    @win.event
    def on_mouse_press(x, y, button, modifiers):
        app.handle_click(x, y, button, modifiers)

    @win.event
    def on_mouse_motion(x, y, dx, dy):
        if app.handle_mouse_move(x, y, dx, dy) == 'pointer':
            win.set_mouse_cursor(app.cursor_pointer)
        elif app.handle_mouse_move(x, y, dx, dy) == 'default':
            win.set_mouse_cursor(app.cursor_default)
        else:
            win.set_mouse_cursor(app.cursor_default)

    @win.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.Q:
            pyglet.app.exit()
        if symbol == pyglet.window.key.J:
            app.set_active_category(Activity.JUMPINGJACK)
            print(f'Set active category to {app.get_active_category()}')
        if symbol == pyglet.window.key.L:
            app.set_active_category(Activity.LIFTING)
            print(f'Set active category to {app.get_active_category()}')
        if symbol == pyglet.window.key.R:
            app.set_active_category(Activity.ROWING)
            print(f'Set active category to {app.get_active_category()}')
        if symbol == pyglet.window.key.U:
            app.set_active_category(Activity.RUNNING)
            print(f'Set active category to {app.get_active_category()}')

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