# clawbot_compact.py
#
# GENERATED FILE - do not edit by hand. The same program as clawbot.py with
# the comments and docstrings taken out, in case the full file is too big
# for the Brain. Built by tools/build_brain.py. UNTESTED ON HARDWARE.

from vex import *
import math
LEFT_DRIVE_PORT = 6
RIGHT_DRIVE_PORT = 10
ARM_PORT = 3
CLAW_PORT = 4
DISTANCE_PORT = 5
OPTICAL_PORT = 1
LEFT_DRIVE_REVERSED = False
RIGHT_DRIVE_REVERSED = True
ARM_REVERSED = False
CLAW_REVERSED = False
WHEEL_TRAVEL_MM = 260.0
DRIVE_GEAR_RATIO = 1.0
TRACK_WIDTH_MM = 240.0
FRONT_MM = 330.0
REAR_MM = 80.0
ROBOT_WIDTH_MM = 290.0
SENSOR_OFFSET_MM = 200.0
CHASSIS_FRONT_MM = 200.0
CLAW_PALM_MM = 230.0
GRID_MM = 300.0
BOARD_MIN_X = -300.0
BOARD_MAX_X = 1200.0
BOARD_MIN_Y = -300.0
BOARD_MAX_Y = 1500.0
BALL_DIAMETER_MM = 150.0
BOX_SIZE_MM = 254.0
COLOURS = ['red', 'green', 'blue']
BOX_POSITIONS = {'red': (1550.0, 1200.0), 'green': (1550.0, 600.0), 'blue': (1550.0, 0.0)}
REJECT_POSITION = (450.0, -650.0)
BOX_CLEARANCE_MM = 100.0
START_X = 0.0
START_Y = -150.0
START_HEADING = 0.0
ORIGINAL_WAYPOINTS = [(0, 300), (600, 300), (600, 0), (900, 0), (900, 600), (300, 600), (300, 900), (0, 900), (0, 1200), (900, 1200), (900, 1350), (-150, 1350), (-150, -150), (0, -150)]
ORIGINAL_FINAL_HEADING = 0.0
SEGMENT_PATHS = {'bringup_line': [('drive', 300), ('turn', 180), ('drive', 300), ('turn', 0)], 'sort_loop': [('drive', 1500), ('turn', 90), ('drive', 900), ('turn', 180), ('drive', 1500), ('turn', 270), ('drive', 900), ('turn', 0)]}
SELECTED_PATH = 'original'
SORT_PATH = 'sort_loop'
RUN_MODE = 'sensor_check'
START_DELAY_MS = 1000
LOOP_MS = 10
DRIVE_MAX_PCT = 30.0
DRIVE_MIN_PCT = 7.0
DRIVE_RAMP_PCT = 2.0
DRIVE_KP = 0.3
DRIVE_TOLERANCE_MM = 5.0
STEER_KP = 1.0
STEER_MAX_PCT = 10.0
TURN_MAX_PCT = 25.0
TURN_MIN_PCT = 6.0
TURN_KP = 0.8
TURN_KD = 2.0
TURN_TOLERANCE_DEG = 1.5
TURN_SETTLE_LOOPS = 4
STOP_SETTLE_MS = 150
DRIVE_STALL_MM = 5.0
DRIVE_STALL_MS = 500
MOTOR_CHECK_PCT = 20.0
MOTOR_CHECK_MS = 1000
MOTOR_CHECK_GAP_MS = 500
IMU_CALIBRATION_TIMEOUT_MS = 5000
START_WAIT_TIMEOUT_MS = 120000
TURN_TIMEOUT_MS = 6000
DRIVE_TIMEOUT_BASE_MS = 2000
DRIVE_TIMEOUT_MS_PER_MM = 15
SENSOR_CHECK_TIMEOUT_MS = 300000
HOME_TIMEOUT_MS = 4000
ARM_TIMEOUT_MS = 4000
CLAW_TIMEOUT_MS = 2500
APPROACH_TIMEOUT_MS = 10000
CREEP_TIMEOUT_MS = 6000
BLOCKED_TIMEOUT_MS = 120000
MISSION_TIMEOUT_MS = 900000
DISTANCE_MIN_MM = 20.0
DISTANCE_MAX_MM = 2000.0
DISTANCE_SAMPLE_MS = 50
DISTANCE_WINDOW = 5
DISTANCE_MIN_VALID = 3
OBJECT_RANGE_MM = 400.0
OPTICAL_LIGHT_PCT = 50
COLOUR_READS = 7
COLOUR_MIN_VOTES = 5
COLOUR_READ_MS = 30
COLOUR_REFERENCES = {'red': (0.0, 20.0), 'green': (110.0, 30.0), 'blue': (220.0, 20.0)}
COLOUR_GATE_BRIGHTNESS = 10.0
COLOUR_CAL_SAMPLES = 20
COLOUR_CAL_MIN_GOOD = 15
COLOUR_CAL_READ_MS = 50
COLOUR_MIN_BRIGHTNESS_GAP = 5.0
COLOUR_SPREAD_FACTOR = 3.0
COLOUR_MIN_TOLERANCE_DEG = 8.0
COLOUR_MAX_TOLERANCE_DEG = 30.0
COLOUR_FILE = 'colours.txt'
COLOUR_LOG_FILE = 'colour_log.csv'
ARM_SEARCH_DEG = 0.0
ARM_GRAB_DEG = 0.0
ARM_CARRY_DEG = 150.0
ARM_DROP_DEG = 400.0
ARM_KP = 0.5
ARM_MAX_PCT = 40.0
ARM_MIN_PCT = 8.0
ARM_TOLERANCE_DEG = 10.0
ARM_HOME_PCT = 15.0
CLAW_HOME_PCT = 15.0
CLAW_CLOSE_PCT = 25.0
CLAW_OPEN_PCT = 25.0
CLAW_EMPTY_CLOSED_DEG = 120.0
CLAW_GRIP_MARGIN_DEG = 20.0
STALL_DEG = 3.0
STALL_MS = 300
APPROACH_PCT = 15.0
APPROACH_STOP_MM = 100.0
APPROACH_MAX_MM = 700.0
OBJECT_LOST_MS = 1000
CREEP_PCT = 8.0
CREEP_MAX_MM = 150.0
IN_CLAW_READS = 3
GRAB_TRIES = 2
GRAB_RETRY_BACKUP_MM = 100.0
OBSTACLE_STOP_MM = 150.0
IGNORE_RADIUS_MM = 200.0
BOARD_MARGIN_MM = 0.0
UNKNOWN_COLOUR_ACTION = 'reject'
BOX_STAGING_MM = 400.0
DROP_REACH_MM = 310.0
DROP_INSET_MM = 90.0
RELEASE_WAIT_MS = 800
RELEASE_TRIES = 2
NAV_TRIES = 3
ARRIVE_TOLERANCE_MM = 30.0
SCREEN_PERIOD_MS = 250
SCREEN_ROWS = 5

def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value

def wrap_180(angle):
    return (angle + 180.0) % 360.0 - 180.0

def wrap_360(angle):
    return angle % 360.0

def compass_vector(heading):
    rad = math.radians(heading)
    return (math.sin(rad), math.cos(rad))

def bearing(x0, y0, x1, y1):
    return wrap_360(math.degrees(math.atan2(x1 - x0, y1 - y0)))

def distance_between(x0, y0, x1, y1):
    dx = x1 - x0
    dy = y1 - y0
    return math.sqrt(dx * dx + dy * dy)

def waypoints_to_segments(start_x, start_y, waypoints, final_heading):
    segments = []
    x = start_x
    y = start_y
    for point in waypoints:
        px = float(point[0])
        py = float(point[1])
        length = distance_between(x, y, px, py)
        if length > 0.0:
            segments.append(('turn', bearing(x, y, px, py)))
            segments.append(('drive', length))
        x = px
        y = py
    segments.append(('turn', wrap_360(final_heading)))
    return segments

def trace_segments(start_x, start_y, start_heading, segments):
    x = start_x
    y = start_y
    heading = start_heading
    points = []
    for kind, value in segments:
        if kind == 'turn':
            heading = wrap_360(value)
        elif kind == 'drive':
            dx, dy = compass_vector(heading)
            x += value * dx
            y += value * dy
            points.append((x, y))
        else:
            raise ValueError('unknown segment type: %s' % kind)
    return points

def path_names():
    names = ['original']
    for name in sorted(SEGMENT_PATHS):
        names.append(name)
    return names

def get_path(name):
    if name == 'original':
        return waypoints_to_segments(START_X, START_Y, ORIGINAL_WAYPOINTS, ORIGINAL_FINAL_HEADING)
    if name in SEGMENT_PATHS:
        segments = []
        for kind, value in SEGMENT_PATHS[name]:
            if kind not in ('turn', 'drive'):
                raise ValueError('path %s has an unknown segment: %s' % (name, kind))
            segments.append((kind, float(value)))
        return segments
    raise ValueError('unknown path: %s' % name)

def smart_port(number):
    return getattr(Ports, 'PORT%d' % number)

class VexHardware:

    def __init__(self):
        self.brain = Brain()
        self.imu = Inertial()
        self.left = Motor(smart_port(LEFT_DRIVE_PORT), GearSetting.RATIO_18_1, LEFT_DRIVE_REVERSED)
        self.right = Motor(smart_port(RIGHT_DRIVE_PORT), GearSetting.RATIO_18_1, RIGHT_DRIVE_REVERSED)
        self.arm = Motor(smart_port(ARM_PORT), GearSetting.RATIO_18_1, ARM_REVERSED)
        self.claw = Motor(smart_port(CLAW_PORT), GearSetting.RATIO_18_1, CLAW_REVERSED)
        self.distance = Distance(smart_port(DISTANCE_PORT))
        self.optical = Optical(smart_port(OPTICAL_PORT))
        self.left.set_stopping(BRAKE)
        self.right.set_stopping(BRAKE)
        self.arm.set_stopping(HOLD)
        self.claw.set_stopping(HOLD)

    def time_ms(self):
        return self.brain.timer.time(MSEC)

    def sleep_ms(self, ms):
        wait(ms, MSEC)

    def drive(self, left_pct, right_pct):
        self.left.spin(FORWARD, left_pct, PERCENT)
        self.right.spin(FORWARD, right_pct, PERCENT)

    def stop_drive(self):
        self.left.stop()
        self.right.stop()

    def drive_degrees(self):
        return (self.left.position(DEGREES), self.right.position(DEGREES))

    def reset_drive_degrees(self):
        self.left.set_position(0, DEGREES)
        self.right.set_position(0, DEGREES)

    def start_imu_calibration(self):
        self.imu.calibrate()

    def imu_calibrating(self):
        return self.imu.is_calibrating()

    def heading(self):
        return self.imu.heading(DEGREES)

    def set_heading(self, heading):
        self.imu.set_heading(heading, DEGREES)

    def arm_spin(self, pct):
        self.arm.spin(FORWARD, pct, PERCENT)

    def arm_stop(self):
        self.arm.stop()

    def arm_degrees(self):
        return self.arm.position(DEGREES)

    def reset_arm_degrees(self):
        self.arm.set_position(0, DEGREES)

    def claw_spin(self, pct):
        self.claw.spin(FORWARD, pct, PERCENT)

    def claw_stop(self):
        self.claw.stop()

    def claw_degrees(self):
        return self.claw.position(DEGREES)

    def reset_claw_degrees(self):
        self.claw.set_position(0, DEGREES)

    def claw_current(self):
        return self.claw.current()

    def stop_all(self):
        self.left.stop()
        self.right.stop()
        self.arm.stop()
        self.claw.stop()

    def distance_raw(self):
        if not self.distance.is_object_detected():
            return None
        return self.distance.object_distance(MM)

    def optical_hue(self):
        return self.optical.hue()

    def optical_brightness(self):
        return self.optical.brightness()

    def optical_near(self):
        return self.optical.is_near_object()

    def optical_light(self, pct):
        self.optical.set_light_power(int(pct), PERCENT)

    def check_pressed(self):
        return self.brain.buttonCheck.pressing()

    def stop_pressed(self):
        return self.brain.buttonLeft.pressing() or self.brain.buttonRight.pressing()

    def show(self, lines):
        self.brain.screen.clear_screen()
        row = 1
        for text in lines:
            self.brain.screen.set_cursor(row, 1)
            self.brain.screen.print(text)
            row += 1

    def log(self, text):
        print(text)

    def beep(self):
        self.brain.play_sound(SoundType.TADA)

    def sd_load(self, name):
        if not self.brain.sdcard.is_inserted():
            return None
        try:
            return self.brain.sdcard.loadfile(name).decode('utf-8')
        except Exception:
            return None

    def sd_save(self, name, text):
        if not self.brain.sdcard.is_inserted():
            return False
        try:
            self.brain.sdcard.savefile(name, bytearray(text, 'utf-8'))
        except Exception:
            return False
        return True

class StopRequested(Exception):
    pass

class Robot:

    def __init__(self, hw):
        self.hw = hw
        self.x = START_X
        self.y = START_Y
        self.target_heading = START_HEADING
        self.last_wheel_mm = 0.0
        self.lines = []
        self.last_screen_ms = None
        self.screen_source = None
        self.last_found = None
        self.last_driven_mm = 0.0

    def wheel_mm(self):
        left, right = self.hw.drive_degrees()
        return (left + right) / 2.0 * WHEEL_TRAVEL_MM * DRIVE_GEAR_RATIO / 360.0

    def reset_pose(self, x, y, heading):
        self.hw.reset_drive_degrees()
        self.hw.set_heading(heading)
        self.x = x
        self.y = y
        self.target_heading = heading
        self.last_wheel_mm = 0.0

    def update(self):
        if self.hw.stop_pressed():
            self.hw.stop_all()
            raise StopRequested()
        travelled = self.wheel_mm()
        step = travelled - self.last_wheel_mm
        self.last_wheel_mm = travelled
        dx, dy = compass_vector(self.hw.heading())
        self.x += step * dx
        self.y += step * dy
        self.refresh_screen(False)

    def tick(self):
        self.update()
        self.hw.sleep_ms(LOOP_MS)

    def pause(self, ms):
        end = self.hw.time_ms() + ms
        while self.hw.time_ms() < end:
            self.tick()

    def set_lines(self, lines, force=True):
        self.lines = list(lines)[:SCREEN_ROWS]
        self.refresh_screen(force)

    def refresh_screen(self, force):
        now = self.hw.time_ms()
        if force or self.last_screen_ms is None or now - self.last_screen_ms >= SCREEN_PERIOD_MS:
            self.last_screen_ms = now
            if self.screen_source is not None:
                self.lines = list(self.screen_source())[:SCREEN_ROWS]
            self.hw.show(self.lines)

    def calibrate(self):
        self.hw.start_imu_calibration()
        start = self.hw.time_ms()
        while self.hw.imu_calibrating():
            if self.hw.time_ms() - start > IMU_CALIBRATION_TIMEOUT_MS:
                return False
            if self.hw.stop_pressed():
                self.hw.stop_all()
                raise StopRequested()
            self.hw.sleep_ms(LOOP_MS)
        return True

    def wait_for_check(self, timeout_ms):
        start = self.hw.time_ms()
        released = False
        while True:
            if self.hw.stop_pressed():
                self.hw.stop_all()
                raise StopRequested()
            pressing = self.hw.check_pressed()
            if pressing and released:
                return True
            if not pressing:
                released = True
            if self.hw.time_ms() - start > timeout_ms:
                return False
            self.hw.sleep_ms(LOOP_MS)

    def stop_drive(self):
        self.hw.stop_drive()
        self.pause(STOP_SETTLE_MS)

    def turn_to(self, target):
        target = wrap_360(target)
        self.target_heading = target
        start = self.hw.time_ms()
        previous = wrap_180(target - self.hw.heading())
        settled = 0
        while settled < TURN_SETTLE_LOOPS:
            if self.hw.time_ms() - start > TURN_TIMEOUT_MS:
                self.stop_drive()
                return 'timeout'
            error = wrap_180(target - self.hw.heading())
            if abs(error) <= TURN_TOLERANCE_DEG:
                settled += 1
                power = 0.0
            else:
                settled = 0
                power = TURN_KP * error + TURN_KD * (error - previous)
                power = clamp(power, -TURN_MAX_PCT, TURN_MAX_PCT)
                if abs(power) < TURN_MIN_PCT:
                    if error > 0:
                        power = TURN_MIN_PCT
                    else:
                        power = -TURN_MIN_PCT
            previous = error
            self.hw.drive(power, -power)
            self.tick()
        self.stop_drive()
        return 'done'

    def drive(self, distance_mm, heading, watch=None):
        if distance_mm >= 0:
            direction = 1.0
        else:
            direction = -1.0
        target = abs(distance_mm)
        start_mm = self.wheel_mm()
        start = self.hw.time_ms()
        limit = DRIVE_TIMEOUT_BASE_MS + target * DRIVE_TIMEOUT_MS_PER_MM
        speed = 0.0
        stall_ms = start
        stall_mm = start_mm
        while True:
            remaining = target - (self.wheel_mm() - start_mm) * direction
            if remaining <= DRIVE_TOLERANCE_MM:
                self.stop_drive()
                self.last_driven_mm = (self.wheel_mm() - start_mm) * direction
                return ('done', None)
            now = self.hw.time_ms()
            if now - start > limit:
                self.stop_drive()
                self.last_driven_mm = (self.wheel_mm() - start_mm) * direction
                return ('timeout', None)
            if now - stall_ms >= DRIVE_STALL_MS:
                if abs(self.wheel_mm() - stall_mm) < DRIVE_STALL_MM:
                    self.stop_drive()
                    self.last_driven_mm = (self.wheel_mm() - start_mm) * direction
                    return ('stuck', None)
                stall_ms = now
                stall_mm = self.wheel_mm()
            if watch is not None and direction > 0:
                found = watch(remaining)
                if found is not None:
                    self.stop_drive()
                    self.last_driven_mm = (self.wheel_mm() - start_mm) * direction
                    return ('object', found)
            want = clamp(DRIVE_MIN_PCT + DRIVE_KP * remaining, DRIVE_MIN_PCT, DRIVE_MAX_PCT)
            if want < speed:
                speed = want
            else:
                speed = min(want, speed + DRIVE_RAMP_PCT)
            steer = clamp(STEER_KP * wrap_180(heading - self.hw.heading()), -STEER_MAX_PCT, STEER_MAX_PCT)
            self.hw.drive(direction * speed + steer, direction * speed - steer)
            self.tick()

    def drive_until(self, pct, heading, check, max_mm, timeout_ms):
        start_mm = self.wheel_mm()
        start = self.hw.time_ms()
        stall_ms = start
        stall_mm = start_mm
        while True:
            outcome = check()
            if outcome is not None:
                self.stop_drive()
                return outcome
            if abs(self.wheel_mm() - start_mm) >= max_mm:
                self.stop_drive()
                return 'too_far'
            now = self.hw.time_ms()
            if now - start > timeout_ms:
                self.stop_drive()
                return 'timeout'
            if now - stall_ms >= DRIVE_STALL_MS:
                if abs(self.wheel_mm() - stall_mm) < DRIVE_STALL_MM:
                    self.stop_drive()
                    return 'stuck'
                stall_ms = now
                stall_mm = self.wheel_mm()
            steer = clamp(STEER_KP * wrap_180(heading - self.hw.heading()), -STEER_MAX_PCT, STEER_MAX_PCT)
            self.hw.drive(pct + steer, pct - steer)
            self.tick()

    def follow_segments(self, segments, watch=None, first=0):
        self.last_found = None
        index = first
        while index < len(segments):
            kind, value = segments[index]
            self.set_lines(['Segment %d/%d' % (index + 1, len(segments)), '%s %.0f' % (kind, value), 'X %.0f Y %.0f' % (self.x, self.y), 'L/R = stop'])
            if kind == 'turn':
                if self.turn_to(value) == 'timeout':
                    return ('timeout', index)
            elif kind == 'drive':
                result, found = self.drive(value, self.target_heading, watch)
                if result == 'object':
                    self.last_found = found
                    return ('object', index)
                if result != 'done':
                    return (result, index)
            else:
                raise ValueError('unknown segment type: %s' % kind)
            index += 1
        return ('done', index)

def valid_distance(raw):
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value:
        return None
    if value < DISTANCE_MIN_MM or value > DISTANCE_MAX_MM:
        return None
    return value

def median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0

class DistanceFilter:

    def __init__(self):
        self.readings = []
        self.last_ms = None

    def reset(self):
        self.readings = []
        self.last_ms = None

    def add(self, raw):
        self.readings.append(valid_distance(raw))
        if len(self.readings) > DISTANCE_WINDOW:
            self.readings.pop(0)

    def update(self, hw):
        now = hw.time_ms()
        if self.last_ms is None or now - self.last_ms >= DISTANCE_SAMPLE_MS:
            self.last_ms = now
            self.add(hw.distance_raw())

    def distance(self):
        valid = [reading for reading in self.readings if reading is not None]
        if len(valid) < DISTANCE_MIN_VALID:
            return None
        return median(valid)

    def in_range(self):
        found = self.distance()
        return found is not None and found <= OBJECT_RANGE_MM

    def fill(self, robot):
        self.reset()
        while len(self.readings) < DISTANCE_WINDOW:
            self.update(robot.hw)
            robot.tick()
        return self.distance()
NONE = 'none'
UNKNOWN = 'unknown'

def average(values):
    return sum(values) / float(len(values))

def circular_mean(angles):
    s = 0.0
    c = 0.0
    for angle in angles:
        s += math.sin(math.radians(angle))
        c += math.cos(math.radians(angle))
    return wrap_360(math.degrees(math.atan2(s, c)))

def circular_spread(angles, centre):
    total = 0.0
    for angle in angles:
        error = wrap_180(angle - centre)
        total += error * error
    return math.sqrt(total / len(angles))

def fit_reference(hues):
    centre = circular_mean(hues)
    tolerance = clamp(COLOUR_SPREAD_FACTOR * circular_spread(hues, centre), COLOUR_MIN_TOLERANCE_DEG, COLOUR_MAX_TOLERANCE_DEG)
    return (centre, tolerance)

def fit_calibration(empty, balls):
    empty_brightness = average([b for h, b in empty])
    floor = empty_brightness + COLOUR_MIN_BRIGHTNESS_GAP
    references = {}
    darkest = None
    for name in COLOURS:
        good = [(h, b) for h, b in balls.get(name, []) if b >= floor]
        if len(good) < COLOUR_CAL_MIN_GOOD:
            return (None, None, name + ' too dark')
        references[name] = fit_reference([h for h, b in good])
        brightness = average([b for h, b in good])
        if darkest is None or brightness < darkest:
            darkest = brightness
    return (references, (empty_brightness + darkest) / 2.0, None)

def overlaps(references):
    found = []
    for i in range(len(COLOURS)):
        for j in range(i + 1, len(COLOURS)):
            a = references[COLOURS[i]]
            b = references[COLOURS[j]]
            if abs(wrap_180(a[0] - b[0])) < a[1] + b[1]:
                found.append(COLOURS[i] + '/' + COLOURS[j])
    return found

def nearest_colour(hue, references):
    best = None
    best_error = None
    for name in COLOURS:
        if name in references:
            error = abs(wrap_180(hue - references[name][0]))
            if best_error is None or error < best_error:
                best = name
                best_error = error
    return (best, best_error)

def classify(hue, brightness, references, gate):
    if brightness < gate:
        return NONE
    name, error = nearest_colour(hue, references)
    if name is None or error > references[name][1]:
        return UNKNOWN
    return name

def vote(labels):
    best = UNKNOWN
    best_count = 0
    for label in labels:
        count = labels.count(label)
        if count > best_count:
            best = label
            best_count = count
    if best_count >= COLOUR_MIN_VOTES:
        return best
    return UNKNOWN

def read_colour(robot, references, gate):
    hw = robot.hw
    labels = []
    while len(labels) < COLOUR_READS:
        labels.append(classify(hw.optical_hue(), hw.optical_brightness(), references, gate))
        robot.pause(COLOUR_READ_MS)
    return (vote(labels), labels)

def calibration_text(references, gate):
    lines = ['# colour calibration: name hue tolerance', 'gate %.1f' % gate]
    for name in COLOURS:
        lines.append('%s %.1f %.1f' % (name, references[name][0], references[name][1]))
    return '\n'.join(lines) + '\n'

def settings_text(references, gate):
    lines = ['COLOUR_REFERENCES = {']
    for name in COLOURS:
        lines.append('    "%s": (%.1f, %.1f),' % (name, references[name][0], references[name][1]))
    lines.append('}')
    lines.append('COLOUR_GATE_BRIGHTNESS = %.1f' % gate)
    return '\n'.join(lines)

def parse_calibration(text):
    references = {}
    gate = None
    for line in text.split('\n'):
        parts = line.split()
        if not parts or parts[0].startswith('#'):
            continue
        try:
            if parts[0] == 'gate':
                key, value = parts
                gate = float(value)
            elif parts[0] in COLOURS:
                name, hue, tolerance = parts
                references[name] = (wrap_360(float(hue)), float(tolerance))
            else:
                return None
        except ValueError:
            return None
    if gate is None or gate < 0:
        return None
    for name in COLOURS:
        if name not in references:
            return None
        tolerance = references[name][1]
        if tolerance < COLOUR_MIN_TOLERANCE_DEG or tolerance > COLOUR_MAX_TOLERANCE_DEG:
            return None
    return (references, gate)

def load_colour_calibration(hw):
    text = hw.sd_load(COLOUR_FILE)
    if text is not None:
        parsed = parse_calibration(text)
        if parsed is not None:
            return (parsed[0], parsed[1], 'SD card')
        hw.log('%s on the SD card is not usable, so settings.py is used' % COLOUR_FILE)
    return (COLOUR_REFERENCES, COLOUR_GATE_BRIGHTNESS, 'settings')

def _collect(robot, prompt):
    robot.set_lines(['COLOUR CALIBRATE', prompt, 'then press CHECK', 'L/R = stop'])
    if not robot.wait_for_check(START_WAIT_TIMEOUT_MS):
        return None
    robot.set_lines(['COLOUR CALIBRATE', prompt, 'Reading...', 'Keep it still'])
    samples = []
    while len(samples) < COLOUR_CAL_SAMPLES:
        samples.append((robot.hw.optical_hue(), robot.hw.optical_brightness()))
        robot.pause(COLOUR_CAL_READ_MS)
    return samples

def colour_calibrate(robot):
    hw = robot.hw
    hw.optical_light(OPTICAL_LIGHT_PCT)
    empty = _collect(robot, 'Claw empty')
    if empty is None:
        hw.optical_light(0)
        robot.set_lines(['Not started.', 'Program ended.'])
        return 'no_start'
    balls = {}
    for name in COLOURS:
        samples = _collect(robot, name + ' in claw')
        if samples is None:
            hw.optical_light(0)
            robot.set_lines(['Not finished.', 'Program ended.'])
            return 'no_start'
        balls[name] = samples
    lines = ['label,hue,brightness']
    for hue, brightness in empty:
        lines.append('empty,%.1f,%.1f' % (hue, brightness))
    for name in COLOURS:
        for hue, brightness in balls[name]:
            lines.append('%s,%.1f,%.1f' % (name, hue, brightness))
    for line in lines:
        hw.log(line)
    hw.sd_save(COLOUR_LOG_FILE, '\n'.join(lines) + '\n')
    references, gate, problem = fit_calibration(empty, balls)
    if problem is not None:
        hw.log('colour calibration failed: ' + problem)
        robot.set_lines(['CALIBRATE FAILED', problem, 'Ball in claw?', 'LED on?'])
        hw.optical_light(0)
        return 'failed'
    saved = hw.sd_save(COLOUR_FILE, calibration_text(references, gate))
    hw.log('colour calibration for config/settings.py:')
    hw.log(settings_text(references, gate))
    close = overlaps(references)
    if close:
        hw.log('these colours look alike: ' + ', '.join(close))
    result = ['Saved to SD' if saved else 'No SD: console']
    for name in COLOURS:
        result.append('%s %.0f +-%.0f' % (name, references[name][0], references[name][1]))
    result.append('Gate %.0f%s' % (gate, ' CLOSE!' if close else ''))
    robot.set_lines(result)
    hw.optical_light(0)
    return 'done'

def run_until_stalled(robot, spin, stop, degrees, pct, timeout_ms):
    hw = robot.hw
    start = hw.time_ms()
    window_start = start
    window_degrees = degrees()
    spin(pct)
    while True:
        robot.tick()
        now = hw.time_ms()
        if now - window_start >= STALL_MS:
            if abs(degrees() - window_degrees) < STALL_DEG:
                stop()
                return True
            window_start = now
            window_degrees = degrees()
        if now - start > timeout_ms:
            stop()
            return False

def home(robot):
    hw = robot.hw
    if not run_until_stalled(robot, hw.arm_spin, hw.arm_stop, hw.arm_degrees, -ARM_HOME_PCT, HOME_TIMEOUT_MS):
        return 'arm not homed'
    hw.reset_arm_degrees()
    if not run_until_stalled(robot, hw.claw_spin, hw.claw_stop, hw.claw_degrees, -CLAW_HOME_PCT, HOME_TIMEOUT_MS):
        return 'claw not homed'
    hw.reset_claw_degrees()
    return None

def move_arm(robot, target):
    hw = robot.hw
    start = hw.time_ms()
    while True:
        error = target - hw.arm_degrees()
        if abs(error) <= ARM_TOLERANCE_DEG:
            hw.arm_stop()
            return True
        if hw.time_ms() - start > ARM_TIMEOUT_MS:
            hw.arm_stop()
            return False
        power = clamp(ARM_KP * error, -ARM_MAX_PCT, ARM_MAX_PCT)
        if abs(power) < ARM_MIN_PCT:
            if error > 0:
                power = ARM_MIN_PCT
            else:
                power = -ARM_MIN_PCT
        hw.arm_spin(power)
        robot.tick()

def close_claw(robot):
    hw = robot.hw
    if not run_until_stalled(robot, hw.claw_spin, hw.claw_stop, hw.claw_degrees, CLAW_CLOSE_PCT, CLAW_TIMEOUT_MS):
        return None
    return hw.claw_degrees()

def open_claw(robot):
    hw = robot.hw
    return run_until_stalled(robot, hw.claw_spin, hw.claw_stop, hw.claw_degrees, -CLAW_OPEN_PCT, CLAW_TIMEOUT_MS)

def holding_ball(claw_stopped_at, brightness, gate):
    if claw_stopped_at is None:
        return False
    return claw_stopped_at < CLAW_EMPTY_CLOSED_DEG - CLAW_GRIP_MARGIN_DEG and brightness >= gate
STOPPED = 'STOPPED'
DONE = 'DONE'

def point_ahead(x, y, heading, distance):
    dx, dy = compass_vector(heading)
    return (x + distance * dx, y + distance * dy)

def on_board(x, y, margin):
    return BOARD_MIN_X + margin <= x <= BOARD_MAX_X - margin and BOARD_MIN_Y + margin <= y <= BOARD_MAX_Y - margin

def box_heading(cx, cy):
    sides = [(cx - BOARD_MAX_X, 90.0), (BOARD_MIN_X - cx, 270.0), (cy - BOARD_MAX_Y, 0.0), (BOARD_MIN_Y - cy, 180.0)]
    best = sides[0]
    for side in sides:
        if side[0] > best[0]:
            best = side
    return best[1]

def box_poses(cx, cy):
    heading = box_heading(cx, cy)
    back = BOX_SIZE_MM / 2.0 - DROP_INSET_MM + DROP_REACH_MM
    drop_x, drop_y = point_ahead(cx, cy, heading, -back)
    line_x, line_y = point_ahead(drop_x, drop_y, heading, -BOX_STAGING_MM)
    return (line_x, line_y, drop_x, drop_y, heading)

class Mission:

    def __init__(self, robot, references, gate, path_name):
        self.robot = robot
        self.hw = robot.hw
        self.references = references
        self.gate = gate
        self.segments = get_path(path_name)
        self.index = 0
        self.remaining = None
        self.state = 'HOME'
        self.colour = '-'
        self.message = ''
        self.resume = None
        self.spot = None
        self.target = None
        self.line_up = None
        self.tries = 0
        self.bright_reads = 0
        self.last_seen_ms = 0
        self.reverse_to_path = False
        self.ignored = []
        self.sorted = {}
        for name in COLOURS:
            self.sorted[name] = 0
        self.rejected = 0
        self.given_up = 0
        self.distance = DistanceFilter()
        self.start_ms = 0

    def run(self):
        robot = self.robot
        hw = self.hw
        self.start_ms = hw.time_ms()
        robot.screen_source = self.screen_lines
        robot.refresh_screen(True)
        problem = home(robot)
        if problem is not None:
            return self.result(self.stop_with(problem))
        if not move_arm(robot, ARM_SEARCH_DEG):
            return self.result(self.stop_with('arm timed out'))
        steps = {'FOLLOW_PATH': self.follow_path, 'APPROACH': self.approach, 'GRAB': self.grab, 'CLASSIFY': self.classify, 'GO_TO_BOX': self.go_to_box, 'RELEASE': self.release, 'RETURN': self.go_back}
        self.state = 'FOLLOW_PATH'
        while self.state in steps:
            if hw.time_ms() - self.start_ms > MISSION_TIMEOUT_MS:
                self.state = self.stop_with('took too long')
                break
            hw.log('state ' + self.state)
            robot.refresh_screen(True)
            self.state = steps[self.state]()
        return self.result(self.state)

    def result(self, state):
        if state == DONE:
            self.finish()
            return 'done'
        return 'failed'

    def screen_lines(self):
        return [self.state, 'Colour ' + self.colour, 'Sorted %d Rej %d' % (self.sorted_total(), self.rejected), 'X %.0f Y %.0f' % (self.robot.x, self.robot.y), 'L/R = stop']

    def sorted_total(self):
        total = 0
        for name in COLOURS:
            total += self.sorted[name]
        return total

    def stop_with(self, message):
        self.hw.stop_all()
        self.message = message
        self.robot.screen_source = None
        self.hw.log('sort stopped in %s: %s' % (self.state, message))
        self.robot.set_lines(['SORT STOPPED', message, self.state, 'Colour ' + self.colour])
        return STOPPED

    def finish(self):
        hw = self.hw
        seconds = (hw.time_ms() - self.start_ms) / 1000.0
        counts = ''
        for name in COLOURS:
            counts += '%s%d ' % (name[0].upper(), self.sorted[name])
        hw.log('sort done in %.0f s: %srejected %d, gave up on %d' % (seconds, counts, self.rejected, self.given_up))
        hw.log('Positions are dead reckoning estimates from the wheels and the gyro. They drift over a run.')
        self.robot.screen_source = None
        self.robot.set_lines(['SORT DONE', counts + 'Rej %d' % self.rejected, 'Gave up %d' % self.given_up, 'Time %.0f s' % seconds, 'Position drifts'])
        hw.beep()

    def read_distance(self):
        self.distance.update(self.hw)
        return self.distance.distance()

    def near_ignored(self, spot):
        for old in self.ignored:
            if distance_between(spot[0], spot[1], old[0], old[1]) <= IGNORE_RADIUS_MM:
                return True
        return False

    def watch_path(self, remaining):
        found = self.read_distance()
        if found is None or found > OBJECT_RANGE_MM:
            return None
        spot = point_ahead(self.robot.x, self.robot.y, self.hw.heading(), SENSOR_OFFSET_MM + found)
        if on_board(spot[0], spot[1], BOARD_MARGIN_MM) and (not self.near_ignored(spot)):
            return ('ball', spot)
        if found <= OBSTACLE_STOP_MM:
            return ('blocked', found)
        return None

    def watch_blocked(self, remaining):
        found = self.read_distance()
        if found is not None and found <= OBSTACLE_STOP_MM:
            return ('blocked', found)
        return None

    def wait_until_clear(self):
        robot = self.robot
        robot.screen_source = None
        robot.set_lines(['BLOCKED', 'Clear the way,', 'then press CHECK', 'L/R = stop'])
        self.hw.log('blocked in ' + self.state)
        pressed = robot.wait_for_check(BLOCKED_TIMEOUT_MS)
        robot.screen_source = self.screen_lines
        if pressed:
            robot.pause(START_DELAY_MS)
        return pressed

    def navigate(self, x, y):
        robot = self.robot
        tries = 0
        while True:
            if distance_between(robot.x, robot.y, x, y) <= ARRIVE_TOLERANCE_MM:
                return None
            if robot.turn_to(bearing(robot.x, robot.y, x, y)) == 'timeout':
                return self.stop_with('turn timed out')
            self.distance.reset()
            length = distance_between(robot.x, robot.y, x, y)
            result, found = robot.drive(length, robot.target_heading, self.watch_blocked)
            if result == 'done':
                return None
            if result == 'timeout':
                return self.stop_with('drive timed out')
            if result == 'stuck':
                return self.stop_with('drive blocked')
            tries += 1
            if tries >= NAV_TRIES or not self.wait_until_clear():
                return self.stop_with('way blocked')

    def follow_path(self):
        robot = self.robot
        while self.index < len(self.segments):
            kind, value = self.segments[self.index]
            if kind == 'turn':
                if robot.turn_to(value) == 'timeout':
                    return self.stop_with('turn timed out')
                self.index += 1
                continue
            if self.remaining is None:
                length = value
            else:
                length = self.remaining
            self.distance.reset()
            result, found = robot.drive(length, robot.target_heading, self.watch_path)
            if result == 'timeout':
                return self.stop_with('drive timed out')
            if result == 'stuck':
                return self.stop_with('drive blocked')
            if result == 'object':
                self.remaining = length - robot.last_driven_mm
                if found[0] == 'ball':
                    self.resume = (robot.x, robot.y, robot.target_heading)
                    self.spot = found[1]
                    self.tries = 0
                    self.hw.log('object ahead at %.0f, %.0f' % self.spot)
                    return 'APPROACH'
                if not self.wait_until_clear():
                    return self.stop_with('path blocked')
                continue
            self.remaining = None
            self.index += 1
        return DONE

    def approach(self):
        robot = self.robot
        heading = robot.target_heading
        self.distance.reset()
        self.last_seen_ms = self.hw.time_ms()
        outcome = robot.drive_until(APPROACH_PCT, heading, self.close_enough, APPROACH_MAX_MM, APPROACH_TIMEOUT_MS)
        if outcome != 'close':
            return self.give_up('approach ' + outcome)
        self.bright_reads = 0
        outcome = robot.drive_until(CREEP_PCT, heading, self.ball_in_claw, CREEP_MAX_MM, CREEP_TIMEOUT_MS)
        if outcome != 'in claw':
            return self.give_up('not in claw: ' + outcome)
        return 'GRAB'

    def close_enough(self):
        found = self.read_distance()
        now = self.hw.time_ms()
        if found is not None:
            self.last_seen_ms = now
            if found <= APPROACH_STOP_MM:
                return 'close'
        elif now - self.last_seen_ms > OBJECT_LOST_MS:
            return 'lost'
        return None

    def ball_in_claw(self):
        if self.hw.optical_brightness() >= self.gate:
            self.bright_reads += 1
        else:
            self.bright_reads = 0
        if self.bright_reads >= IN_CLAW_READS:
            return 'in claw'
        return None

    def grab(self):
        robot = self.robot
        if not move_arm(robot, ARM_GRAB_DEG):
            return self.stop_with('arm timed out')
        stopped_at = close_claw(robot)
        holding = holding_ball(stopped_at, self.hw.optical_brightness(), self.gate)
        if holding:
            self.hw.log('grab: claw stopped at %.0f degrees, holding a ball' % stopped_at)
        else:
            self.hw.log('grab: no ball in the claw')
            return self.grab_failed()
        if not move_arm(robot, ARM_CARRY_DEG):
            return self.stop_with('arm timed out')
        return 'CLASSIFY'

    def grab_failed(self):
        robot = self.robot
        if not open_claw(robot):
            return self.stop_with('claw timed out')
        if not move_arm(robot, ARM_SEARCH_DEG):
            return self.stop_with('arm timed out')
        self.tries += 1
        if self.tries >= GRAB_TRIES:
            return self.give_up('grip failed')
        if robot.drive(-GRAB_RETRY_BACKUP_MM, robot.target_heading)[0] != 'done':
            return self.stop_with('backup timed out')
        return 'APPROACH'

    def give_up(self, reason):
        self.hw.log('giving up on the object at %.0f, %.0f: %s' % (self.spot[0], self.spot[1], reason))
        self.ignored.append(self.spot)
        self.given_up += 1
        self.colour = '-'
        self.reverse_to_path = True
        return 'RETURN'

    def classify(self):
        answer, labels = read_colour(self.robot, self.references, self.gate)
        self.hw.log('colour %s from %s' % (answer, ' '.join(labels)))
        if answer == NONE:
            return self.grab_failed()
        self.colour = answer
        if answer != UNKNOWN:
            self.target = BOX_POSITIONS[answer]
        elif UNKNOWN_COLOUR_ACTION == 'stop':
            return self.stop_with('unknown colour')
        else:
            self.target = REJECT_POSITION
        return 'GO_TO_BOX'

    def go_to_box(self):
        robot = self.robot
        line_x, line_y, drop_x, drop_y, heading = box_poses(self.target[0], self.target[1])
        self.line_up = (line_x, line_y)
        stopped = self.navigate(line_x, line_y)
        if stopped is not None:
            return stopped
        if robot.turn_to(heading) == 'timeout':
            return self.stop_with('turn timed out')
        if not move_arm(robot, ARM_DROP_DEG):
            return self.stop_with('arm timed out')
        if robot.drive(distance_between(robot.x, robot.y, drop_x, drop_y), heading)[0] != 'done':
            return self.stop_with('box not reached')
        return 'RELEASE'

    def release(self):
        robot = self.robot
        for attempt in range(RELEASE_TRIES):
            if not open_claw(robot):
                return self.stop_with('claw timed out')
            robot.pause(RELEASE_WAIT_MS)
            if self.hw.optical_brightness() < self.gate:
                if self.target == REJECT_POSITION:
                    self.rejected += 1
                else:
                    self.sorted[self.colour] += 1
                self.hw.log('let go of the %s ball' % self.colour)
                self.reverse_to_path = False
                return 'RETURN'
            close_claw(robot)
        return self.stop_with('ball stuck')

    def go_back(self):
        robot = self.robot
        x, y, heading = self.resume
        if self.reverse_to_path:
            back = distance_between(robot.x, robot.y, x, y)
            result = robot.drive(-back, heading)[0]
        else:
            back = distance_between(robot.x, robot.y, self.line_up[0], self.line_up[1])
            result = robot.drive(-back, robot.target_heading)[0]
        if result != 'done':
            return self.stop_with('backup timed out')
        if not move_arm(robot, ARM_SEARCH_DEG):
            return self.stop_with('arm timed out')
        stopped = self.navigate(x, y)
        if stopped is not None:
            return stopped
        if robot.turn_to(heading) == 'timeout':
            return self.stop_with('turn timed out')
        self.colour = '-'
        return 'FOLLOW_PATH'

def sensor_check(robot):
    hw = robot.hw
    hw.reset_arm_degrees()
    hw.reset_claw_degrees()
    references, gate, source = load_colour_calibration(hw)
    hw.log('sensor check: colour references from ' + source)
    hw.optical_light(OPTICAL_LIGHT_PCT)
    distance = DistanceFilter()
    labels = []
    start = hw.time_ms()
    while hw.time_ms() - start < SENSOR_CHECK_TIMEOUT_MS:
        distance.update(hw)
        found = distance.distance()
        if found is None:
            distance_text = 'Dist none'
        elif distance.in_range():
            distance_text = 'Dist %.0f IN' % found
        else:
            distance_text = 'Dist %.0f mm' % found
        hue = hw.optical_hue()
        brightness = hw.optical_brightness()
        labels.append(classify(hue, brightness, references, gate))
        if len(labels) > COLOUR_READS:
            labels.pop(0)
        robot.set_lines(['Arm %.0f Claw %.0f' % (hw.arm_degrees(), hw.claw_degrees()), 'Head %.1f' % hw.heading(), distance_text, 'Hue %.0f Br %.0f' % (hue, brightness), 'Colour ' + vote(labels)], False)
        robot.tick()
    hw.optical_light(0)
    robot.set_lines(['SENSOR CHECK', 'Timed out.', 'Program ended.'])
    return 'timeout'

def _spin_one(robot, name, want, spin, stop, degrees):
    robot.set_lines(['MOTOR CHECK', name, 'Want: ' + want, 'L/R = stop'])
    before = degrees()
    spin(MOTOR_CHECK_PCT)
    robot.pause(MOTOR_CHECK_MS)
    stop()
    robot.pause(MOTOR_CHECK_GAP_MS)
    turned = degrees() - before
    robot.hw.log('motor check: %s turned %.0f degrees' % (name, turned))
    return turned

def motor_check(robot):
    hw = robot.hw
    left = _spin_one(robot, 'Left wheel', 'forward', lambda pct: hw.drive(pct, 0), hw.stop_drive, lambda: hw.drive_degrees()[0])
    right = _spin_one(robot, 'Right wheel', 'forward', lambda pct: hw.drive(0, pct), hw.stop_drive, lambda: hw.drive_degrees()[1])
    arm = _spin_one(robot, 'Arm', 'up', hw.arm_spin, hw.arm_stop, hw.arm_degrees)
    claw = _spin_one(robot, 'Claw', 'close', hw.claw_spin, hw.claw_stop, hw.claw_degrees)
    robot.set_lines(['MOTOR CHECK DONE', 'L %.0f R %.0f' % (left, right), 'Arm %.0f Claw %.0f' % (arm, claw), '0 = check cable'])
    return 'done'
MODES = ['sensor_check', 'colour_calibrate', 'motor_check', 'path', 'sort']

def settings_problem(mode, path_name):
    if mode not in MODES:
        return 'Bad RUN_MODE'
    if mode == 'path' or mode == 'sort':
        try:
            get_path(path_name)
        except ValueError:
            return 'Bad path setting'
    if mode == 'sort':
        if UNKNOWN_COLOUR_ACTION != 'reject' and UNKNOWN_COLOUR_ACTION != 'stop':
            return 'Bad unknown rule'
        for spot in list(BOX_POSITIONS.values()) + [REJECT_POSITION]:
            if on_board(spot[0], spot[1], -BOX_SIZE_MM / 2.0):
                return 'Box on the board'
    return None

def run_path(robot, path_name):
    hw = robot.hw
    robot.reset_pose(START_X, START_Y, START_HEADING)
    start_ms = hw.time_ms()
    result, index = robot.follow_segments(get_path(path_name))
    seconds = (hw.time_ms() - start_ms) / 1000.0
    hw.log('path %s %s segment %d time %.1f s x %.0f y %.0f' % (path_name, result, index, seconds, robot.x, robot.y))
    if result == 'done':
        robot.set_lines(['PATH COMPLETE', 'Time %.1f s' % seconds, 'X %.0f Y %.0f' % (robot.x, robot.y), 'Heading %.1f' % hw.heading()])
        hw.beep()
    else:
        robot.set_lines(['PATH STOPPED', 'Reason: ' + result, 'At segment %d' % (index + 1)])
    return result

def run_sort(robot, path_name, references, gate):
    hw = robot.hw
    hw.optical_light(OPTICAL_LIGHT_PCT)
    robot.reset_pose(START_X, START_Y, START_HEADING)
    result = Mission(robot, references, gate, path_name).run()
    hw.optical_light(0)
    return result

def run(hw, mode=RUN_MODE, path_name=None):
    if path_name is None:
        if mode == 'sort':
            path_name = SORT_PATH
        else:
            path_name = SELECTED_PATH
    robot = Robot(hw)
    problem = settings_problem(mode, path_name)
    if problem is not None:
        hw.log('settings problem: %s (mode %s, path %s)' % (problem, mode, path_name))
        robot.set_lines([problem, 'Fix settings.py', 'Program ended.'])
        return 'bad_setting'
    try:
        robot.set_lines(['Clawbot sorter', 'Calibrating gyro', 'Keep robot still'])
        if not robot.calibrate():
            robot.set_lines(['Gyro calibration', 'timed out.', 'Restart program'])
            return 'calibration_timeout'
        if mode == 'sensor_check':
            return sensor_check(robot)
        if mode == 'colour_calibrate':
            return colour_calibrate(robot)
        lines = ['Clawbot sorter']
        if mode == 'motor_check':
            lines.append('Lift wheels!')
        elif mode == 'sort':
            references, gate, source = load_colour_calibration(hw)
            lines.append('Sort ' + path_name)
            lines.append('Colours ' + source)
        else:
            lines.append('Path ' + path_name)
        robot.set_lines(lines + ['CHECK = start', 'L/R = stop'])
        if not robot.wait_for_check(START_WAIT_TIMEOUT_MS):
            robot.set_lines(['Not started.', 'Program ended.'])
            return 'no_start'
        robot.pause(START_DELAY_MS)
        if mode == 'motor_check':
            return motor_check(robot)
        if mode == 'sort':
            return run_sort(robot, path_name, references, gate)
        return run_path(robot, path_name)
    except StopRequested:
        hw.stop_all()
        hw.show(['STOPPED', 'Stop pressed'])
        return 'stopped'
    except Exception:
        hw.stop_all()
        raise

def main():
    run(VexHardware())
main()
