# sim_hardware.py
#
# A laptop stand-in for src/hardware.py. SimHardware has the same methods as
# VexHardware, so the robot code in src/ runs here unchanged. Laptop only:
# none of this goes onto the Brain.
#
# The physics are deliberately simple:
#   - each motor follows its power command with a first-order lag
#   - the two driven wheels set the speed and turn rate (differential drive)
#   - wheel slip makes the real distance a little shorter than the encoders say
#   - the gyro has a slow drift and a little noise
#   - the Distance Sensor is a single ray from the front of the robot; it
#     can be made to miss readings or give wild ones, to test the filter
#   - the Optical Sensor sees the colour of a ball in the claw, or of one
#     right at the claw's palm, with some noise
#   - closing the claw on a ball in its opening grips it; opening the claw
#     lets it go, into a box if the arm is high and the ball is over one
#   - boxes, balls and extra obstacles are solid; driving into them stalls
#     the wheels, which is how a real bump looks to the encoders
#
# Passing the simulator does not mean the robot works. It means the logic is
# sound under these simplified physics. Anything not run on the real robot is
# untested on hardware.

import math
import random

from settings import *

# Simulator settings. These describe the model, not the robot, so they live
# here rather than in config/settings.py.
SIM_STEP_MS = 2.0               # physics time step
SIM_MAX_RPM = 127.0             # assumed motor speed at 100 % power (not verified)
SIM_MOTOR_LAG_S = 0.06          # time constant of the motor speed response
SIM_IMU_CALIBRATION_MS = 2000.0
SIM_BUTTON_HOLD_MS = 200.0      # how long a scripted button press lasts
SIM_TRACE_PERIOD_MS = 50.0      # how often the robot's position is recorded
SIM_ARM_MAX_DEG = 600.0         # arm motor travel limit, motor degrees
SIM_CLAW_MAX_DEG = 120.0        # claw motor travel limit, motor degrees
SIM_STALL_CURRENT_A = 1.2       # current drawn by a stalled 5.5 W motor (API max)
SIM_FREE_CURRENT_A = 0.1
SIM_EMPTY_BRIGHTNESS = 4.0      # optical brightness with the claw empty
SIM_HUE_NOISE_DEG = 4.0
SIM_BRIGHTNESS_NOISE_PCT = 2.0
SIM_LIGHT_REFERENCE_PCT = 50.0  # LED power the brightness values here are for
DEFAULT_MAX_TIME_MS = 600000.0  # a run longer than this is treated as stuck
SIM_CLAW_BALL_DEG = 60.0        # where the claw stops when it closes on a ball
SIM_MOUTH_HALF_MM = 60.0        # a ball centre this near the claw's centre line can be gripped
SIM_OPTICAL_RANGE_MM = 10.0     # the Optical Sensor sees a ball this close to the palm
SIM_ARM_CLEARS_SENSOR_DEG = 100.0  # above this a held ball is out of the Distance Sensor's view
SIM_ARM_ABOVE_BOX_DEG = 300.0   # above this the claw passes over the top of a box
SIM_CLAW_RELEASE_DEG = 30.0     # opening the claw past this lets the ball go

# One ball of each colour and one that was never calibrated, placed on the
# west and north sides of "sort_loop" as its comment in settings.py says.
DEMO_BALLS = [
    {"x": 0.0, "y": 300.0, "colour": "red"},
    {"x": 0.0, "y": 600.0, "colour": "orange"},
    {"x": 0.0, "y": 900.0, "colour": "blue"},
    {"x": 450.0, "y": 1350.0, "colour": "green"},
]

# How a ball held in the claw looks to the Optical Sensor in the simulator,
# as (hue, brightness). These are guesses for the model, not measurements.
# A hue of None means the ball has no clear hue (white), so each reading
# gets a random one.
SIM_BALL_LOOKS = {
    "red": (3.0, 42.0),
    "green": (118.0, 35.0),
    "blue": (215.0, 28.0),
    "orange": (32.0, 45.0),
    "white": (None, 70.0),
}


class SimTimeout(Exception):
    """The simulated run went on longer than max_time_ms."""
    pass


class SimMotor:
    def __init__(self):
        self.command = 0.0    # percent the code asked for
        self.velocity = 0.0   # percent the motor is actually doing
        self.degrees = 0.0    # encoder position
        self.blocked = False  # set by the world when something stops it

    def step(self, dt_s, low=None, high=None):
        target = 0.0 if self.blocked else self.command
        blend = min(1.0, dt_s / SIM_MOTOR_LAG_S)
        self.velocity += (target - self.velocity) * blend
        self.degrees += self.velocity / 100.0 * SIM_MAX_RPM * 6.0 * dt_s
        if low is not None and self.degrees < low:
            self.degrees = low
            self.velocity = 0.0
        if high is not None and self.degrees > high:
            self.degrees = high
            self.velocity = 0.0


# ------------------------------------------------------------------ shapes
def robot_outline(x, y, heading, front=FRONT_MM):
    """Corners of the robot's rectangle in world coordinates, from the back
    of the robot to front mm ahead of the turning centre."""
    rad = math.radians(heading)
    fx, fy = math.sin(rad), math.cos(rad)
    rx, ry = fy, -fx
    half = ROBOT_WIDTH_MM / 2.0
    corners = []
    for along, side in ((front, half), (front, -half), (-REAR_MM, -half), (-REAR_MM, half)):
        corners.append((x + along * fx + side * rx, y + along * fy + side * ry))
    return corners


def rectangle(cx, cy, width, depth):
    """Axis-aligned rectangle (x0, y0, x1, y1) centred on (cx, cy)."""
    return (cx - width / 2.0, cy - depth / 2.0, cx + width / 2.0, cy + depth / 2.0)


def _polygons_overlap(a, b):
    for poly in (a, b):
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            ax, ay = y2 - y1, x1 - x2
            pa = [ax * px + ay * py for px, py in a]
            pb = [ax * px + ay * py for px, py in b]
            if max(pa) <= min(pb) or max(pb) <= min(pa):
                return False
    return True


def _rect_polygon(rect):
    x0, y0, x1, y1 = rect
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _point_in_polygon(px, py, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _circle_hits_polygon(cx, cy, radius, poly):
    if _point_in_polygon(cx, cy, poly):
        return True
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        dx, dy = x2 - x1, y2 - y1
        length_sq = dx * dx + dy * dy
        t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((cx - x1) * dx + (cy - y1) * dy) / length_sq))
        nx, ny = x1 + t * dx, y1 + t * dy
        if (cx - nx) ** 2 + (cy - ny) ** 2 < radius * radius:
            return True
    return False


def _ray_to_rect(ox, oy, dx, dy, rect):
    x0, y0, x1, y1 = rect
    t_near, t_far = -1e18, 1e18
    for origin, direction, low, high in ((ox, dx, x0, x1), (oy, dy, y0, y1)):
        if abs(direction) < 1e-12:
            if origin < low or origin > high:
                return None
        else:
            t1, t2 = (low - origin) / direction, (high - origin) / direction
            if t1 > t2:
                t1, t2 = t2, t1
            t_near, t_far = max(t_near, t1), min(t_far, t2)
            if t_near > t_far:
                return None
    if t_far < 0:
        return None
    return max(t_near, 0.0)


def _ray_to_circle(ox, oy, dx, dy, cx, cy, radius):
    fx, fy = ox - cx, oy - cy
    b = fx * dx + fy * dy
    c = fx * fx + fy * fy - radius * radius
    disc = b * b - c
    if disc < 0:
        return None
    root = math.sqrt(disc)
    for t in (-b - root, -b + root):
        if t >= 0:
            return t
    return None


# ------------------------------------------------------------- the hardware
class SimHardware:
    """Simulated robot with the same methods as VexHardware."""

    def __init__(self, start=None, seed=1, slip_left=1.0, slip_right=1.0,
                 imu_drift_dps=0.0, imu_noise_deg=0.0, sensor_noise_mm=0.0,
                 check_presses=(3000.0,), stop_press_ms=None, imu_calibrates=True,
                 obstacles=None, balls=None, include_boxes=True, held=None,
                 sd_card=True, sd_files=None, distance_dropout=0.0, distance_spike=0.0,
                 events=None, arm_start_deg=0.0, claw_start_deg=0.0, arm_stops=True,
                 max_time_ms=DEFAULT_MAX_TIME_MS):
        """Options:

        check_presses  times in ms at which CHECK is pressed (or one time, or None)
        balls          balls on the floor: dicts with x, y and colour, and
                       optionally grabbable=False (it slips out of the claw)
                       or sticky=True (it will not drop out)
        held           colour the Optical Sensor sees as if a ball were held:
                       None, a name from SIM_BALL_LOOKS, or a list of
                       (from_ms, name or None)
        sd_card        whether an SD card is inserted; sd_files preloads it
        distance_dropout, distance_spike
                       chance per reading that the Distance Sensor sees
                       nothing, or gives a random wrong distance
        events         list of (time_ms, function(hw)) to run at those times
        arm_start_deg, claw_start_deg
                       where the arm and claw start, from their stops
        arm_stops      False makes the arm's lower stop disappear, so homing
                       never finds it
        """
        self.rng = random.Random(seed)
        if start is None:
            start = (START_X, START_Y, START_HEADING)
        self.x, self.y, self.theta = float(start[0]), float(start[1]), float(start[2])
        self.slip_left = slip_left
        self.slip_right = slip_right
        self.imu_drift_dps = imu_drift_dps
        self.imu_noise_deg = imu_noise_deg
        self.sensor_noise_mm = sensor_noise_mm
        if check_presses is None:
            check_presses = ()
        elif isinstance(check_presses, (int, float)):
            check_presses = (check_presses,)
        self.check_presses = [float(t) for t in check_presses]
        self.stop_press_ms = stop_press_ms
        self.held = held
        self.sd_card = sd_card
        self.sd_files = dict(sd_files or {})
        self.distance_dropout = distance_dropout
        self.distance_spike = distance_spike
        self.imu_calibrates = imu_calibrates
        self.max_time_ms = max_time_ms

        self.obstacles = list(obstacles or [])
        if include_boxes:
            for cx, cy in list(BOX_POSITIONS.values()) + [REJECT_POSITION]:
                self.obstacles.append(rectangle(cx, cy, BOX_SIZE_MM, BOX_SIZE_MM))
        self.balls = [dict(b) for b in (balls or [])]
        self.box_spots = []
        if include_boxes:
            self.box_spots = list(BOX_POSITIONS.items()) + [("reject", REJECT_POSITION)]
        self.box_contents = dict((name, []) for name, spot in self.box_spots)
        self.dropped = []
        self.held_ball = None
        self.events = sorted(events or [], key=lambda event: event[0])
        self.arm_stops = arm_stops

        self.t_ms = 0.0
        self.left = SimMotor()
        self.right = SimMotor()
        self.arm = SimMotor()
        self.claw = SimMotor()
        self.arm.degrees = float(arm_start_deg)
        self.claw.degrees = float(claw_start_deg)
        self.imu_offset = 0.0
        self.calibration_ends_ms = None
        self.light_pct = 0.0

        self.screen = []
        self.screen_updates = 0
        self.console = []
        self.beeps = 0
        self.collisions = 0
        self.trace = []
        self._next_trace_ms = 0.0
        self._was_blocked = False

    # ---- physics
    def _true_heading(self):
        return self.theta % 360.0

    def _wheel_speed(self, motor, slip):
        return (motor.velocity / 100.0 * SIM_MAX_RPM / 60.0
                * WHEEL_TRAVEL_MM * DRIVE_GEAR_RATIO * slip)

    def _hits_something(self, x, y, heading):
        # with the arm up, the claw passes over the boxes and only the
        # chassis can hit them
        if self.arm.degrees >= SIM_ARM_ABOVE_BOX_DEG:
            body = robot_outline(x, y, heading, CHASSIS_FRONT_MM)
        else:
            body = robot_outline(x, y, heading)
        for rect in self.obstacles:
            if _polygons_overlap(body, _rect_polygon(rect)):
                return True
        # a ball can go into the claw's opening, as far back as the palm
        chassis = robot_outline(x, y, heading, CLAW_PALM_MM)
        for ball in self.balls:
            if _circle_hits_polygon(ball["x"], ball["y"], BALL_DIAMETER_MM / 2.0, chassis):
                return True
        return False

    def _robot_frame(self, px, py):
        """(ahead, to the right) of a point, in mm from the turning centre."""
        rad = math.radians(self.theta)
        fx, fy = math.sin(rad), math.cos(rad)
        dx, dy = px - self.x, py - self.y
        return dx * fx + dy * fy, dx * fy - dy * fx

    def _ball_in_mouth(self):
        for ball in self.balls:
            ahead, side = self._robot_frame(ball["x"], ball["y"])
            if CLAW_PALM_MM <= ahead <= FRONT_MM and abs(side) <= SIM_MOUTH_HALF_MM:
                return ball
        return None

    def _ball_at_palm(self):
        if self.arm.degrees >= SIM_ARM_CLEARS_SENSOR_DEG:
            return None    # the claw is up off the floor
        radius = BALL_DIAMETER_MM / 2.0
        for ball in self.balls:
            ahead, side = self._robot_frame(ball["x"], ball["y"])
            gap = ahead - radius - CLAW_PALM_MM
            if -1.0 <= gap <= SIM_OPTICAL_RANGE_MM and abs(side) <= SIM_MOUTH_HALF_MM:
                return ball
        return None

    def _update_grip(self, claw_before):
        if self.held_ball is None:
            # the claw has just closed as far as a ball's width
            if claw_before < SIM_CLAW_BALL_DEG <= self.claw.degrees:
                ball = self._ball_in_mouth()
                if ball is not None and ball.get("grabbable", True):
                    self.balls.remove(ball)
                    self.held_ball = ball
                    self.claw.degrees = SIM_CLAW_BALL_DEG
                    self.claw.velocity = 0.0
        elif self.claw.degrees < SIM_CLAW_RELEASE_DEG and not self.held_ball.get("sticky", False):
            self._drop_held_ball()

    def _drop_held_ball(self):
        ball = self.held_ball
        self.held_ball = None
        radius = BALL_DIAMETER_MM / 2.0
        high = self.arm.degrees >= SIM_ARM_ABOVE_BOX_DEG
        if high:
            reach = DROP_REACH_MM
        else:
            reach = CLAW_PALM_MM + radius
        rad = math.radians(self.theta)
        bx = self.x + reach * math.sin(rad)
        by = self.y + reach * math.cos(rad)
        if high:
            half = BOX_SIZE_MM / 2.0
            for name, (cx, cy) in self.box_spots:
                if abs(bx - cx) <= half - radius and abs(by - cy) <= half - radius:
                    self.box_contents[name].append(ball["colour"])
                    return
        ball = dict(ball)
        ball["x"] = bx
        ball["y"] = by
        self.balls.append(ball)
        self.dropped.append(ball)

    def _step(self, dt_ms):
        dt_s = dt_ms / 1000.0
        for motor in (self.left, self.right):
            motor.step(dt_s)
        self.arm.step(dt_s, 0.0 if self.arm_stops else None, SIM_ARM_MAX_DEG)
        claw_before = self.claw.degrees
        claw_shut = SIM_CLAW_MAX_DEG
        if self.held_ball is not None:
            claw_shut = SIM_CLAW_BALL_DEG
        self.claw.step(dt_s, 0.0, claw_shut)
        self._update_grip(claw_before)

        v_left = self._wheel_speed(self.left, self.slip_left)
        v_right = self._wheel_speed(self.right, self.slip_right)
        speed = (v_left + v_right) / 2.0
        turn_rate = math.degrees((v_left - v_right) / TRACK_WIDTH_MM)
        mid = math.radians(self.theta + turn_rate * dt_s / 2.0)
        nx = self.x + speed * math.sin(mid) * dt_s
        ny = self.y + speed * math.cos(mid) * dt_s
        ntheta = self.theta + turn_rate * dt_s

        blocked = self._hits_something(nx, ny, ntheta)
        if blocked:
            if not self._was_blocked:
                self.collisions += 1
        else:
            self.x, self.y, self.theta = nx, ny, ntheta
        self._was_blocked = blocked
        self.left.blocked = blocked
        self.right.blocked = blocked

        self.t_ms += dt_ms
        while self.events and self.events[0][0] <= self.t_ms:
            when, action = self.events.pop(0)
            action(self)
        if self.t_ms >= self._next_trace_ms:
            self.trace.append((self.t_ms, self.x, self.y, self._true_heading()))
            self._next_trace_ms += SIM_TRACE_PERIOD_MS
        if self.t_ms > self.max_time_ms:
            raise SimTimeout("simulated run passed %.0f ms" % self.max_time_ms)

    # ---- time
    def time_ms(self):
        return self.t_ms

    def sleep_ms(self, ms):
        steps = max(1, int(round(ms / SIM_STEP_MS)))
        for _ in range(steps):
            self._step(ms / steps)

    # ---- drive
    def drive(self, left_pct, right_pct):
        self.left.command = max(-100.0, min(100.0, float(left_pct)))
        self.right.command = max(-100.0, min(100.0, float(right_pct)))

    def stop_drive(self):
        self.left.command = 0.0
        self.right.command = 0.0

    def drive_degrees(self):
        return self.left.degrees, self.right.degrees

    def reset_drive_degrees(self):
        self.left.degrees = 0.0
        self.right.degrees = 0.0

    # ---- inertial sensor
    def start_imu_calibration(self):
        self.calibration_ends_ms = self.t_ms + SIM_IMU_CALIBRATION_MS

    def imu_calibrating(self):
        if not self.imu_calibrates:
            return True
        return self.calibration_ends_ms is not None and self.t_ms < self.calibration_ends_ms

    def _raw_heading(self):
        noise = self.rng.gauss(0.0, self.imu_noise_deg) if self.imu_noise_deg else 0.0
        return self.theta + self.imu_drift_dps * self.t_ms / 1000.0 + noise

    def heading(self):
        return (self._raw_heading() + self.imu_offset) % 360.0

    def set_heading(self, heading):
        self.imu_offset = heading - (self.theta + self.imu_drift_dps * self.t_ms / 1000.0)

    # ---- arm and claw
    def arm_spin(self, pct):
        self.arm.command = max(-100.0, min(100.0, float(pct)))

    def arm_stop(self):
        self.arm.command = 0.0

    def arm_degrees(self):
        return self.arm.degrees

    def reset_arm_degrees(self):
        self.arm.degrees = 0.0

    def claw_spin(self, pct):
        self.claw.command = max(-100.0, min(100.0, float(pct)))

    def claw_stop(self):
        self.claw.command = 0.0

    def claw_degrees(self):
        return self.claw.degrees

    def reset_claw_degrees(self):
        self.claw.degrees = 0.0

    def claw_current(self):
        pushing = abs(self.claw.command) > 0 and abs(self.claw.velocity) < 1.0
        return SIM_STALL_CURRENT_A if pushing else SIM_FREE_CURRENT_A

    def stop_all(self):
        for motor in (self.left, self.right, self.arm, self.claw):
            motor.command = 0.0

    # ---- sensors
    def _sensor_origin(self):
        rad = math.radians(self.theta)
        return (self.x + SENSOR_OFFSET_MM * math.sin(rad),
                self.y + SENSOR_OFFSET_MM * math.cos(rad), rad)

    def distance_raw(self):
        if self.distance_dropout and self.rng.random() < self.distance_dropout:
            return None
        if self.distance_spike and self.rng.random() < self.distance_spike:
            return self.rng.uniform(DISTANCE_MIN_MM, DISTANCE_MAX_MM)
        ox, oy, rad = self._sensor_origin()
        dx, dy = math.sin(rad), math.cos(rad)
        best = None
        for rect in self.obstacles:
            hit = _ray_to_rect(ox, oy, dx, dy, rect)
            if hit is not None and (best is None or hit < best):
                best = hit
        for ball in self.balls:
            hit = _ray_to_circle(ox, oy, dx, dy, ball["x"], ball["y"], BALL_DIAMETER_MM / 2.0)
            if hit is not None and (best is None or hit < best):
                best = hit
        if self.held_ball is not None and self.arm.degrees < SIM_ARM_CLEARS_SENSOR_DEG:
            hit = CLAW_PALM_MM - SENSOR_OFFSET_MM
            if best is None or hit < best:
                best = hit
        if best is None or best > DISTANCE_MAX_MM:
            return None
        if self.sensor_noise_mm:
            best += self.rng.gauss(0.0, self.sensor_noise_mm)
        return max(DISTANCE_MIN_MM, best)

    def _held_colour(self):
        if self.held_ball is not None:
            return self.held_ball["colour"]
        if self.held is None or isinstance(self.held, str):
            return self.held
        colour = None
        for from_ms, name in self.held:
            if self.t_ms >= from_ms:
                colour = name
        return colour

    def _optical_reading(self):
        colour = self._held_colour()
        if colour is None:
            ball = self._ball_at_palm()
            if ball is not None:
                colour = ball["colour"]
        light = min(1.0, self.light_pct / SIM_LIGHT_REFERENCE_PCT)
        if colour is None:
            hue = None
            brightness = SIM_EMPTY_BRIGHTNESS * light
        else:
            hue, lit = SIM_BALL_LOOKS[colour]
            brightness = SIM_EMPTY_BRIGHTNESS + (lit - SIM_EMPTY_BRIGHTNESS) * light
        if hue is None:
            hue = self.rng.uniform(0.0, 360.0)
        else:
            hue += self.rng.gauss(0.0, SIM_HUE_NOISE_DEG)
        brightness += self.rng.gauss(0.0, SIM_BRIGHTNESS_NOISE_PCT)
        return hue % 360.0, max(0.0, min(100.0, brightness))

    def optical_hue(self):
        return self._optical_reading()[0]

    def optical_brightness(self):
        return self._optical_reading()[1]

    def optical_near(self):
        return self._held_colour() is not None or self._ball_at_palm() is not None

    def optical_light(self, pct):
        self.light_pct = float(pct)

    # ---- buttons, screen, console
    def _pressed(self, press_ms):
        return press_ms is not None and press_ms <= self.t_ms < press_ms + SIM_BUTTON_HOLD_MS

    def check_pressed(self):
        for press_ms in self.check_presses:
            if self._pressed(press_ms):
                return True
        return False

    def stop_pressed(self):
        return self._pressed(self.stop_press_ms)

    def show(self, lines):
        self.screen = list(lines)
        self.screen_updates += 1

    def log(self, text):
        self.console.append(text)

    def beep(self):
        self.beeps += 1

    # ---- SD card (kept in memory)
    def sd_load(self, name):
        if not self.sd_card:
            return None
        return self.sd_files.get(name)

    def sd_save(self, name, text):
        if not self.sd_card:
            return False
        self.sd_files[name] = text
        return True
