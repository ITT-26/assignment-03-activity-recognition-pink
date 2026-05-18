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
ACTIVITY_DURATION = 30.0
PREP_DURATION = 5.0

FONT = "Arial"


def _rgba(rgb, a=255):
    return (*rgb, a)


class FitnessTrainerApp:
    """
    Apple Fitness-inspired portrait UI (400x700).

    Ring is drawn as four stacked shapes:
      1. faint glow Circle  (radius r_out+12)  — visible only when correct
      2. filled gray Circle  (radius r_out)     — full background ring
      3. colored Sector      (radius r_out)     — progress pie slice
      4. filled off-white Circle (radius r_in)  — punches the center hole
    """

    def __init__(self, window):
        self.window = window
        self.batch = pyglet.graphics.Batch()

        g0 = pyglet.graphics.Group(order=0)  # static background
        g1 = pyglet.graphics.Group(order=1)  # glow halo behind the ring
        g2 = pyglet.graphics.Group(order=2)  # ring: gray background circle
        g3 = pyglet.graphics.Group(order=3)  # ring: progress sector
        g4 = pyglet.graphics.Group(order=4)  # ring: center hole + mid elements
        g5 = pyglet.graphics.Group(order=5)  # progress bar fill
        g6 = pyglet.graphics.Group(order=6)  # all text

        self.activities = list(ACTIVITIES)
        self.current_idx = 0
        self.elapsed = 0.0
        self.prep_remaining = PREP_DURATION
        self.detected = None
        self.is_correct = False
        self.pulse_t = 0.0
        self.session_done = False

        n = len(self.activities)

        ring_cx, ring_cy = WINDOW_W // 2, 480
        r_out, r_in = 131, 109

        # --- background ---
        self._bg = pyglet.shapes.Rectangle(
            0, 0, WINDOW_W, WINDOW_H,
            color=OFF_WHITE, batch=self.batch, group=g0)

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
            "0:30",
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

        # --- detection chip ---
        chip_w, chip_h = 220, 40
        chip_y = 300
        self.chip_bg = pyglet.shapes.RoundedRectangle(
            ring_cx - chip_w // 2, chip_y - chip_h // 2, chip_w, chip_h, radius=20,
            color=MID_GRAY, batch=self.batch, group=g4)
        self.chip_lbl = pyglet.text.Label(
            "Waiting for sensor...",
            font_name=FONT, font_size=11,
            x=ring_cx, y=chip_y,
            anchor_x="center", anchor_y="center",
            color=(255, 255, 255, 255),
            batch=self.batch, group=g6)

        # --- exercise list ---
        list_spacing = 36
        self.list_lbls = [
            pyglet.text.Label(
                ACTIVITY_LABELS[act],
                font_name=FONT, font_size=16,
                x=WINDOW_W // 2, y=230 - i * list_spacing,
                anchor_x="center", anchor_y="center",
                color=_rgba(TEXT_GRAY),
                batch=self.batch, group=g6)
            for i, act in enumerate(self.activities)
        ]

        # --- session progress bar ---
        bar_x = (WINDOW_W - 340) // 2
        self._bar_bg = pyglet.shapes.RoundedRectangle(
            bar_x, 42, 340, 8, radius=4,
            color=LIGHT_GRAY, batch=self.batch, group=g4)
        self.prog_fill = pyglet.shapes.RoundedRectangle(
            bar_x, 42, 2, 8, radius=4,
            color=APPLE_BLUE, batch=self.batch, group=g5)
        self.prog_lbl = pyglet.text.Label(
            f"1 / {n}",
            font_name=FONT, font_size=10,
            x=WINDOW_W // 2, y=30,
            anchor_x="center", anchor_y="center",
            color=_rgba(TEXT_GRAY),
            batch=self.batch, group=g6)

        self._refresh()

    # ------------------------------------------------------------------

    def _update_list(self, idx):
        for i, lbl in enumerate(self.list_lbls):
            lbl.text = ACTIVITY_LABELS[self.activities[i]]
            if i < idx:
                lbl.color = _rgba(APPLE_GREEN)
                lbl.bold = False
            elif i == idx:
                lbl.color = _rgba(TEXT_DARK)
                lbl.bold = True
            else:
                lbl.color = _rgba(TEXT_GRAY)
                lbl.bold = False

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
        n = len(self.activities)

        self.ring_sector.color = RING_COLOR
        self.ring_sector.angle = prog * 360
        self.ring_sector.start_angle = 90 - prog * 360

        if self.is_correct:
            pulse = 0.5 + 0.5 * math.sin(self.pulse_t * math.pi * 2)
            self._glow.opacity = int(40 + 40 * pulse)
        else:
            self._glow.opacity = 0

        rem = max(0.0, ACTIVITY_DURATION - self.elapsed)
        self.timer_lbl.text = f"{int(rem // 60)}:{int(rem % 60):02d}"
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

        session_prog = (idx + prog) / n
        self.prog_fill.width = max(2, int(340 * session_prog))
        self.prog_lbl.text = f"{idx + 1} / {n}"

    def _refresh_prep(self):
        idx = self.current_idx
        n = len(self.activities)
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
        self.chip_lbl.text = "Get ready"

        self._update_list(idx)

        session_prog = idx / n
        self.prog_fill.width = max(2, int(340 * session_prog))
        self.prog_lbl.text = f"{idx + 1} / {n}"

    def _show_complete(self):
        self.timer_lbl.text = "Done!"
        self.act_lbl.text = "Great workout!"
        self.act_lbl.color = _rgba(APPLE_GREEN)
        self.chip_bg.color = APPLE_GREEN
        self.chip_lbl.text = "Session complete"
        self.prog_fill.width = 340
        self.ring_sector.color = APPLE_GREEN
        self.ring_sector.start_angle = 90
        self.ring_sector.angle = 360
        self._glow.opacity = 0
        for i, lbl in enumerate(self.list_lbls):
            lbl.text = ACTIVITY_LABELS[self.activities[i]]
            lbl.color = _rgba(APPLE_GREEN)
            lbl.bold = False

    # ------------------------------------------------------------------

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