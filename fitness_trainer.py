# this program visualizes activities with pyglet
from enum import Enum
import activity_recognizer as activity
import pyglet

WINDOW_W, WINDOW_H = 400, 600
# ITEM_W, ITEM_H = 320, 60
# BG_COLOR = (20 / 255, 20 / 255, 40 / 255, 1.0)  # dark blue

# Use Enums for Placement and Activity giving nicer code

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
    """
    Custom Button for pyglet apps. Basically just a rectangle that has text and is highlighted when hovered.
    A real observer pattern has not been implemented yet (due to laziness on my part).
    """
    def __init__(self, x, y, width, height, text, color=(0, 0, 0), highlight_color=(115, 190, 181),
                 font_name='Calibri', font_size=20):
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
        self.text = pyglet.text.Label(text, font_name=font_name, font_size=font_size, x=text_x, y=text_y,
                                      anchor_x='center', anchor_y='center')


    def is_point_inside(self, x, y):
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def set_hovered(self, is_hovered):
        self.is_hovered = is_hovered
        if self.is_hovered:
            self.color = self.highlight_color
        else:
            self.color = self.origin_color

    def update_values(self):
        """
        Call this after changing size of the button so the text label is adjusted as well
        :return:
        """
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
        # Values for buttons
        self.window_dimensions = {'width': 800, 'height': 600}
        self.sprite_dimensions = {'width': 360, 'height': 460}
        self.sprite_coordinates = {'x_one': 20, 'y_one': 20, 'x_two': 420, 'y_two': 20}
        self.button_coordinates = {'x_one': 20, 'y_one': 50, 'x_two': 420, 'y_two': 50}
        self.button_coordinates_small = {'x_one': 20, 'y_one': 520, 'x_two': 420, 'y_two': 520}
        self.button_dimensions = {'width': 360, 'height': 500}
        self.button_dimensions_small = {'width': 360, 'height': 60}
        self.button_color = (0, 0, 0)
        self.button_highlight_color = (115, 190, 181)
        self.background_color = (20 / 255, 20 / 255, 40 / 255, 1.0)
        self.placement_button_hand = None
        self.placement_button_pocket = None
        self.cursor_default = None
        self.cursor_pointer = None

        notif_x = self.window_dimensions['width'] / 2
        notif_y = 20
        self.placement_notif = pyglet.text.Label('', x=notif_x, y=notif_y, anchor_x='center', anchor_y='center',
                                                 font_name='Calibri', font_size=16)

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

        Idea taken from chatGPT, no code copied directly
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
        Scales a sprite to fit the target dimensions. Code copied from chatGPT
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
            'Sensor will be held in hand',
            color=self.button_color,
            highlight_color=self.button_highlight_color
        )
        self.placement_button_pocket = CustomButton(
            self.button_coordinates['x_two'],
            self.button_coordinates['y_two'],
            self.button_dimensions['width'],
            self.button_dimensions['height'],
            'Sensor will be in pocket',
            color=self.button_color,
            highlight_color=self.button_highlight_color
        )

    def handle_click(self, x, y, button, modifiers):
        print(f'Registered Mouse button press at {x}, {y}')
        # Change sensor placement value depending on what button is pressed and display a notification
        if self.placement_button_hand.is_hovered:
            self.sensor_placement = Placement.HAND
            self.display_notif('Sensor placement was set to \'hand\'')
        if self.placement_button_pocket.is_hovered:
            self.sensor_placement = Placement.POCKET
            self.display_notif('Sensor placement was set to \'pocket\'')

        # Once the placement has been set initially, rearrange the buttons
        if self.sensor_placement is not Placement.UNDEFINED:
            self._rearrange_placement_buttons()

    def display_notif(self, msg, reset=3):
        self.placement_notif.text = msg
        pyglet.clock.schedule_once(self.reset_notif, reset)

    def reset_notif(self, dt):
        """
        Resets the placement notification.
        :param dt: time after which the notification resets
        :return:
        """
        self.placement_notif.text = ''

    def _rearrange_placement_buttons(self):
        """
        Changes the placement of the buttons so they are smaller and cover only the top of the screen
        :return:
        """
        self.placement_button_hand.x = self.button_coordinates_small['x_one']
        self.placement_button_hand.y = self.button_coordinates_small['y_one']
        self.placement_button_hand.width = self.button_dimensions_small['width']
        self.placement_button_hand.height = self.button_dimensions_small['height']
        self.placement_button_hand.text_content = 'Click here for hand mode'

        self.placement_button_pocket.x = self.button_coordinates_small['x_two']
        self.placement_button_pocket.y = self.button_coordinates_small['y_two']
        self.placement_button_pocket.width = self.button_dimensions_small['width']
        self.placement_button_pocket.height = self.button_dimensions_small['height']
        self.placement_button_pocket.text_content = 'Click here for pocket mode'

        self.placement_button_hand.update_values()
        self.placement_button_pocket.update_values()

    def handle_mouse_move(self, x, y, dx, dy) -> str:
        # Return a string to set the cursor since app has no direct access to window
        # Check if mouse hovers over one of the buttons and if yes, highlight it
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


def main():
    # Magic numbers since size should be a property of TrainerApp but initing app before win crashes
    win = pyglet.window.Window(800, 600, caption="Fitness Trainer", resizable=False)
    app = TrainerApp()
    pyglet.gl.glClearColor(*app.background_color)
    recognizer = activity.ActivityRecognizer()

    # set the cursors the app should use
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