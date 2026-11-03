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
#   - the Distance Sensor is a single ray from the front of the robot
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
SIM_NO_OBJECT_BRIGHTNESS = 2.0  # optical brightness with nothing in front
DEFAULT_MAX_TIME_MS = 600000.0  # a run longer than this is treated as stuck


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
def robot_outline(x, y, heading):
    """Corners of the robot's rectangle in world coordinates."""
    rad = math.radians(heading)
    fx, fy = math.sin(rad), math.cos(rad)
    rx, ry = fy, -fx
    half = ROBOT_WIDTH_MM / 2.0
    corners = []
    for along, side in ((FRONT_MM, half), (FRONT_MM, -half), (-REAR_MM, -half), (-REAR_MM, half)):
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
                 start_press_ms=3000.0, stop_press_ms=None, imu_calibrates=True,
                 obstacles=None, balls=None, include_boxes=True,
                 max_time_ms=DEFAULT_MAX_TIME_MS):
        self.rng = random.Random(seed)
        if start is None:
            start = (START_X, START_Y, START_HEADING)
        self.x, self.y, self.theta = float(start[0]), float(start[1]), float(start[2])
        self.slip_left = slip_left
        self.slip_right = slip_right
        self.imu_drift_dps = imu_drift_dps
        self.imu_noise_deg = imu_noise_deg
        self.sensor_noise_mm = sensor_noise_mm
        self.start_press_ms = start_press_ms
        self.stop_press_ms = stop_press_ms
        self.imu_calibrates = imu_calibrates
        self.max_time_ms = max_time_ms

        self.obstacles = list(obstacles or [])
        if include_boxes:
            for cx, cy in list(BOX_POSITIONS.values()) + [REJECT_POSITION]:
                self.obstacles.append(rectangle(cx, cy, BOX_SIZE_MM, BOX_SIZE_MM))
        self.balls = [dict(b) for b in (balls or [])]

        self.t_ms = 0.0
        self.left = SimMotor()
        self.right = SimMotor()
        self.arm = SimMotor()
        self.claw = SimMotor()
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
        outline = robot_outline(x, y, heading)
        for rect in self.obstacles:
            if _polygons_overlap(outline, _rect_polygon(rect)):
                return True
        for ball in self.balls:
            if _circle_hits_polygon(ball["x"], ball["y"], BALL_DIAMETER_MM / 2.0, outline):
                return True
        return False

    def _step(self, dt_ms):
        dt_s = dt_ms / 1000.0
        for motor in (self.left, self.right):
            motor.step(dt_s)
        self.arm.step(dt_s, 0.0, SIM_ARM_MAX_DEG)
        self.claw.step(dt_s, 0.0, SIM_CLAW_MAX_DEG)

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
        if best is None or best > DISTANCE_MAX_MM:
            return None
        if self.sensor_noise_mm:
            best += self.rng.gauss(0.0, self.sensor_noise_mm)
        return max(DISTANCE_MIN_MM, best)

    # STUB until milestone 2: the simulator has no ball colours yet, so the
    # Optical Sensor always reports nothing in front of it.
    def optical_hue(self):
        return 0.0

    def optical_brightness(self):
        return SIM_NO_OBJECT_BRIGHTNESS

    def optical_near(self):
        return False

    def optical_light(self, pct):
        self.light_pct = float(pct)

    # ---- buttons, screen, console
    def _pressed(self, press_ms):
        return press_ms is not None and press_ms <= self.t_ms < press_ms + SIM_BUTTON_HOLD_MS

    def start_pressed(self):
        return self._pressed(self.start_press_ms)

    def stop_pressed(self):
        return self._pressed(self.stop_press_ms)

    def show(self, lines):
        self.screen = list(lines)
        self.screen_updates += 1

    def log(self, text):
        self.console.append(text)

    def beep(self):
        self.beeps += 1
