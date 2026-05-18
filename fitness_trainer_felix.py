import os
import pyglet
import pyglet.shapes
import math
import activity_recognizer as activity_module

WINDOW_W, WINDOW_H = 400, 700

BG_GL = (248 / 255, 248 / 255, 250 / 255, 1.0)

OFF_WHITE = (248, 248, 250)
LIGHT_GRAY = (229, 229, 234)
MID_GRAY = (174, 174, 178)
TEXT_DARK = (28, 28, 30)
TEXT_GRAY = (142, 142, 147)
TEXT_FADED = (190, 190, 194)

APPLE_RED = (255, 59, 48)
APPLE_ORANGE = (255, 149, 0)
APPLE_BLUE = (0, 122, 255)
APPLE_GREEN = (52, 199, 89)

RING_COLOR = APPLE_BLUE
PREP_COLOR = APPLE_ORANGE

ACTIVITIES = ["jumpingjacks", "lifting", "rowing", "running"]
ACTIVITY_LABELS = {
    "jumpingjacks": "Jumping Jacks",
    "lifting": "Lifting",
    "rowing": "Rowing",
    "running": "Running",
}
ACTIVITY_DURATION = 20.0
PREP_DURATION = 5.0

FONT = "Arial"


def _rgba(rgb, a=255):
    return (*rgb, a)


class FitnessTrainerApp:
    def __init__(self, window):
        self.window = window
        self.batch = pyglet.graphics.Batch()

        g1 = pyglet.graphics.Group(order=1)  # glow halo behind the ring
        g2 = pyglet.graphics.Group(order=2)  # ring: gray background circle
        g3 = pyglet.graphics.Group(order=3)  # ring: progress sector
        g4 = pyglet.graphics.Group(order=4)  # ring hole + chip + row highlights
        g5 = pyglet.graphics.Group(order=5)  # marker circles
        g6 = pyglet.graphics.Group(order=6)  # all text

        self.activities = list(ACTIVITIES)
        self.current_idx = 0
        self.elapsed = 0.0
        self.prep_remaining = PREP_DURATION
        self.detected = None
        self.is_correct = False
        self.pulse_t = 0.0
        self.session_done = False

        ring_cx, ring_cy = WINDOW_W // 2, 520
        r_out, r_in = 131, 109

        # --- ring ---
        self._glow = pyglet.shapes.Circle(
            ring_cx, ring_cy, r_out + 12,
            color=RING_COLOR, batch=self.batch, group=g1)
        self._glow.opacity = 0

        self._ring_bg = pyglet.shapes.Circle(
            ring_cx, ring_cy, r_out,
            color=LIGHT_GRAY, batch=self.batch, group=g2)

        self.ring_sector = pyglet.shapes.Sector(
            ring_cx, ring_cy, r_out,
            angle=0.0, start_angle=90,
            color=RING_COLOR, batch=self.batch, group=g3)

        self._inner_hole = pyglet.shapes.Circle(
            ring_cx, ring_cy, r_in,
            color=OFF_WHITE, batch=self.batch, group=g4)

        # --- text inside ring ---
        self.timer_lbl = pyglet.text.Label(
            "0:20",
            font_name=FONT, font_size=46,
            x=ring_cx, y=ring_cy + 18,
            anchor_x="center", anchor_y="center",
            color=_rgba(TEXT_DARK),
            batch=self.batch, group=g6)

        self.act_lbl = pyglet.text.Label(
            ACTIVITY_LABELS[ACTIVITIES[0]],
            font_name=FONT, font_size=16,
            x=ring_cx, y=ring_cy - 28,
            anchor_x="center", anchor_y="center",
            color=_rgba(RING_COLOR),
            batch=self.batch, group=g6)

        # --- detected caption + chip ---
        self._detected_caption = pyglet.text.Label(
            "DETECTED",
            font_name=FONT, font_size=10,
            x=WINDOW_W // 2, y=345,
            anchor_x="center", anchor_y="center",
            color=_rgba(TEXT_GRAY),
            batch=self.batch, group=g6)

        chip_w, chip_h = 260, 50
        chip_y = 310
        self.chip_bg = pyglet.shapes.RoundedRectangle(
            (WINDOW_W - chip_w) // 2, chip_y - chip_h // 2, chip_w, chip_h, radius=18,
            color=MID_GRAY, batch=self.batch, group=g4)
        self.chip_lbl = pyglet.text.Label(
            "Waiting for sensor...",
            font_name=FONT, font_size=16,
            x=WINDOW_W // 2, y=chip_y,
            anchor_x="center", anchor_y="center",
            color=(255, 255, 255, 255),
            batch=self.batch, group=g6)

        # --- workout list ---
        list_left = 40
        list_width = WINDOW_W - 2 * list_left
        marker_x = list_left + 22
        text_x = list_left + 48
        list_y_top = 200
        list_spacing = 46
        row_h = 38

        self._workout_heading = pyglet.text.Label(
            "WORKOUT",
            font_name=FONT, font_size=10,
            x=list_left, y=list_y_top + 32,
            anchor_x="left", anchor_y="center",
            color=_rgba(TEXT_GRAY),
            batch=self.batch, group=g6)
        self._workout_heading.bold = True

        self.row_highlights = []
        self.marker_outers = []
        self.marker_inners = []
        self.list_lbls = []

        for i, act in enumerate(self.activities):
            y = list_y_top - i * list_spacing

            hl = pyglet.shapes.RoundedRectangle(
                list_left, y - row_h // 2, list_width, row_h, radius=10,
                color=LIGHT_GRAY, batch=self.batch, group=g4)
            hl.opacity = 0
            self.row_highlights.append(hl)

            outer = pyglet.shapes.Circle(
                marker_x, y, 9,
                color=LIGHT_GRAY, batch=self.batch, group=g5)
            inner = pyglet.shapes.Circle(
                marker_x, y, 6,
                color=OFF_WHITE, batch=self.batch, group=g5)
            self.marker_outers.append(outer)
            self.marker_inners.append(inner)

            lbl = pyglet.text.Label(
                ACTIVITY_LABELS[act],
                font_name=FONT, font_size=16,
                x=text_x, y=y,
                anchor_x="left", anchor_y="center",
                color=_rgba(TEXT_GRAY),
                batch=self.batch, group=g6)
            self.list_lbls.append(lbl)

        self._refresh()

    # ------------------------------------------------------------------

    def _set_row_done(self, i):
        self.list_lbls[i].color = _rgba(APPLE_GREEN)
        self.list_lbls[i].bold = False
        self.marker_outers[i].color = APPLE_GREEN
        self.marker_inners[i].color = APPLE_GREEN
        self.row_highlights[i].opacity = 0

    def _set_row_current(self, i):
        self.list_lbls[i].color = _rgba(TEXT_DARK)
        self.list_lbls[i].bold = True
        self.marker_outers[i].color = RING_COLOR
        self.marker_inners[i].color = RING_COLOR
        self.row_highlights[i].opacity = 255

    def _set_row_pending(self, i):
        self.list_lbls[i].color = _rgba(TEXT_GRAY)
        self.list_lbls[i].bold = False
        self.marker_outers[i].color = LIGHT_GRAY
        self.marker_inners[i].color = OFF_WHITE
        self.row_highlights[i].opacity = 0

    def _update_list(self, idx):
        for i in range(len(self.list_lbls)):
            self.list_lbls[i].text = ACTIVITY_LABELS[self.activities[i]]
            if i < idx:
                self._set_row_done(i)
            elif i == idx:
                self._set_row_current(i)
            else:
                self._set_row_pending(i)

    def _refresh(self):
        if self.session_done:
            self._show_complete()
            return
        if self.prep_remaining > 0:
            self._refresh_prep()
            return

        idx = self.current_idx
        act = self.activities[idx]
        prog = min(1.0, self.elapsed / ACTIVITY_DURATION)

        self.ring_sector.color = RING_COLOR
        self.ring_sector.angle = prog * 360
        self.ring_sector.start_angle = 90 - prog * 360

        if self.is_correct:
            pulse = 0.5 + 0.5 * math.sin(self.pulse_t * math.pi * 2)
            self._glow.opacity = int(40 + 40 * pulse)
        else:
            self._glow.opacity = 0

        rem = max(0.0, ACTIVITY_DURATION - self.elapsed)
        secs = int(math.ceil(rem))
        self.timer_lbl.text = f"{secs // 60}:{secs % 60:02d}"
        self.act_lbl.text = ACTIVITY_LABELS[act]
        self.act_lbl.color = _rgba(RING_COLOR)

        if self.detected:
            det_name = ACTIVITY_LABELS.get(self.detected, self.detected)
            self.chip_bg.color = APPLE_GREEN if self.is_correct else APPLE_RED
            self.chip_lbl.text = det_name
        else:
            self.chip_bg.color = MID_GRAY
            self.chip_lbl.text = "Waiting for sensor..."

        self._update_list(idx)

    def _refresh_prep(self):
        idx = self.current_idx
        prep_prog = (PREP_DURATION - self.prep_remaining) / PREP_DURATION

        self.ring_sector.color = PREP_COLOR
        self.ring_sector.angle = prep_prog * 360
        self.ring_sector.start_angle = 90 - prep_prog * 360
        self._glow.opacity = 0

        secs = max(1, int(math.ceil(self.prep_remaining)))
        self.timer_lbl.text = str(secs)
        self.act_lbl.text = "Get ready"
        self.act_lbl.color = _rgba(PREP_COLOR)

        self.chip_bg.color = MID_GRAY
        if self.detected:
            self.chip_lbl.text = f"Get ready for {ACTIVITY_LABELS[self.activities[idx]]}"
        else:
            self.chip_lbl.text = "Waiting for sensor..."

        self._update_list(idx)

    def _show_complete(self):
        self.timer_lbl.text = "Done!"
        self.act_lbl.text = "Great workout!"
        self.act_lbl.color = _rgba(APPLE_GREEN)
        self.chip_bg.color = APPLE_GREEN
        self.chip_lbl.text = "Session complete"
        self.ring_sector.color = APPLE_GREEN
        self.ring_sector.start_angle = 90
        self.ring_sector.angle = 360
        self._glow.opacity = 0
        for i in range(len(self.list_lbls)):
            self.list_lbls[i].text = ACTIVITY_LABELS[self.activities[i]]
            self._set_row_done(i)

    # ------------------------------------------------------------------

    def restart(self):
        self.current_idx = 0
        self.elapsed = 0.0
        self.prep_remaining = PREP_DURATION
        self.detected = None
        self.is_correct = False
        self.pulse_t = 0.0
        self.session_done = False
        self._refresh()

    def update(self, dt, detected):
        if self.session_done:
            return

        if self.prep_remaining > 0:
            self.prep_remaining = max(0.0, self.prep_remaining - dt)
            self.detected = detected
            self.is_correct = False
            self._refresh()
            return

        self.detected = detected
        act = self.activities[self.current_idx]
        self.is_correct = detected == act

        self.elapsed += dt
        if self.is_correct:
            self.pulse_t += dt

        if self.elapsed >= ACTIVITY_DURATION:
            self.elapsed = 0.0
            self.pulse_t = 0.0
            self.current_idx += 1
            if self.current_idx >= len(self.activities):
                self.session_done = True
                self.current_idx = len(self.activities) - 1
            else:
                self.prep_remaining = PREP_DURATION

        self._refresh()

    def draw(self):
        self.batch.draw()


# ------------------------------------------------------------------

def main():
    config = pyglet.gl.Config(sample_buffers=1, samples=4, double_buffer=True)
    try:
        win = pyglet.window.Window(WINDOW_W, WINDOW_H, caption="Fitness Trainer", resizable=False, config=config)
    except pyglet.window.NoSuchConfigException:
        win = pyglet.window.Window(WINDOW_W, WINDOW_H, caption="Fitness Trainer", resizable=False)
    pyglet.gl.glClearColor(*BG_GL)

    recognizer = activity_module.ActivityRecognizer()
    app = FitnessTrainerApp(win)

    @win.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.Q:
            pyglet.app.exit()
            os._exit(0)
        elif symbol == pyglet.window.key.R:
            app.restart()

    @win.event
    def on_draw():
        win.clear()
        app.draw()

    def tick(dt):
        recognizer.tick(dt)
        app.update(dt, recognizer.current_activity)

    pyglet.clock.schedule_interval(tick, 1 / 60)
    try:
        with recognizer:
            pyglet.app.run()
    except KeyboardInterrupt:
        print("Interrupted. Exiting...")
        os._exit(0)


if __name__ == "__main__":
    main()