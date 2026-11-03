from vex import *
import math

brain = Brain()
imu = Inertial()
left_motor = Motor(Ports.PORT6, GearSetting.RATIO_18_1, False)
right_motor = Motor(Ports.PORT10, GearSetting.RATIO_18_1, True)
catapult = Motor(Ports.PORT9, GearSetting.RATIO_18_1, False)
intake_left = Motor(Ports.PORT3, GearSetting.RATIO_18_1, False)
intake_right = Motor(Ports.PORT4, GearSetting.RATIO_18_1, True)
distance = Distance(Ports.PORT5)

WHEEL_TRAVEL = 260
FRONT = 170
SENSOR = 150
STOP_GAP = 100
SIDE_STEP = 420
OBSTACLE_DEPTH = 250
TAIL_SWING = 250
MIN_X, MIN_Y, MAX_X, MAX_Y = -300, -300, 1200, 1500
SENSOR_MAX = 2000
LOOP_MS = 10
START_DELAY = 1000

TURN_KP = 1.0
TURN_KD = 3.0
TURN_MAX = 45
TURN_MIN = 7
TURN_TOLERANCE = 1
TURN_SETTLE = 4
TURN_TIMEOUT = 4000

DRIVE_MAX = 60
DRIVE_MIN = 7
DRIVE_KP = 0.45
DRIVE_RAMP = 3
DRIVE_TOLERANCE = 4
DRIVE_TIMEOUT = 2000
DRIVE_TIMEOUT_PER_MM = 8
STEER_KP = 1.0
STEER_MAX = 15
STOP_STEPS = 15

SLOW_RANGE = 350
SLOW_MIN = 0.3
DETECT_COUNT = 3
PASS_MARGIN = 60
WIDEN_STEP = 100
WIDEN_TRIES = 3
CREEP_STEP = 100
CREEP_TRIES = 4
WAYPOINT_TOLERANCE = 40
GOTO_TRIES = 6

START = (0, -150)
ROUTE = [(0, 300), (600, 300), (600, 0), (900, 0), (900, 600), (300, 600),
         (300, 900), (0, 900), (0, 1200), (900, 1200),
         (900, 1350), (-150, 1350), (-150, -150), (0, -150)]

x, y = START
last_enc = 0
obstacles = 0


def heading():
    return imu.heading(DEGREES)


def wrap(angle):
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle


def encoder_mm():
    turns = (left_motor.position(DEGREES) + right_motor.position(DEGREES)) / 2
    return turns * WHEEL_TRAVEL / 360


def step():
    global x, y, last_enc
    enc = encoder_mm()
    moved = enc - last_enc
    last_enc = enc
    h = math.radians(heading())
    x += moved * math.sin(h)
    y += moved * math.cos(h)
    wait(LOOP_MS, MSEC)


def drive(left, right):
    left_motor.spin(FORWARD, left, PERCENT)
    right_motor.spin(FORWARD, right, PERCENT)


def stop():
    left_motor.stop()
    right_motor.stop()
    for i in range(STOP_STEPS):
        step()


def turn_to(target):
    last = wrap(target - heading())
    settled = 0
    start = brain.timer.time(MSEC)
    while settled < TURN_SETTLE and brain.timer.time(MSEC) - start < TURN_TIMEOUT:
        error = wrap(target - heading())
        if abs(error) < TURN_TOLERANCE:
            settled += 1
            power = 0
        else:
            settled = 0
            power = TURN_KP * error + TURN_KD * (error - last)
            power = max(-TURN_MAX, min(TURN_MAX, power))
            if abs(power) < TURN_MIN:
                power = TURN_MIN if error > 0 else -TURN_MIN
        last = error
        drive(power, -power)
        step()
    stop()


def read_distance():
    if not distance.is_object_detected():
        return None
    d = distance.object_distance(MM)
    if d <= 0 or d > SENSOR_MAX:
        return None
    return d


def drive_straight(dist, target, check=False):
    start_enc = encoder_mm()
    start = brain.timer.time(MSEC)
    speed = 0
    seen = 0
    while brain.timer.time(MSEC) - start < DRIVE_TIMEOUT + dist * DRIVE_TIMEOUT_PER_MM:
        remaining = dist - (encoder_mm() - start_enc)
        if remaining <= DRIVE_TOLERANCE:
            break
        slow = 1
        if check:
            d = read_distance()
            if d is not None and d + SENSOR < remaining + FRONT + STOP_GAP:
                gap = d - (FRONT - SENSOR)
                seen = seen + 1 if gap <= STOP_GAP else 0
                if seen >= DETECT_COUNT:
                    stop()
                    return d
                slow = max(SLOW_MIN, min(1, (gap - STOP_GAP) / SLOW_RANGE))
            else:
                seen = 0
        want = max(DRIVE_MIN, min(DRIVE_MAX, DRIVE_MIN + DRIVE_KP * remaining) * slow)
        speed = want if want < speed else min(want, speed + DRIVE_RAMP)
        steer = max(-STEER_MAX, min(STEER_MAX, STEER_KP * wrap(target - heading())))
        drive(speed + steer, speed - steer)
        step()
    stop()
    return None


def bearing(px, py):
    return math.degrees(math.atan2(px - x, py - y)) % 360


def dist_to(px, py):
    return math.sqrt((px - x) ** 2 + (py - y) ** 2)


def ahead(px, py, h):
    r = math.radians(h)
    return (px - x) * math.sin(r) + (py - y) * math.cos(r)


def room(h):
    dx = math.sin(math.radians(h))
    dy = math.cos(math.radians(h))
    r = 9999
    if dx > 0.01:
        r = min(r, (MAX_X - x) / dx)
    if dx < -0.01:
        r = min(r, (MIN_X - x) / dx)
    if dy > 0.01:
        r = min(r, (MAX_Y - y) / dy)
    if dy < -0.01:
        r = min(r, (MIN_Y - y) / dy)
    return r


def avoid(h, reading, px, py):
    global obstacles
    obstacles += 1
    side = 90 if room(h + 90) > room(h - 90) else -90
    side_h = (h + side) % 360
    back_h = (h - side) % 360

    turn_to(side_h)
    drive_straight(SIDE_STEP, side_h)
    moved = SIDE_STEP
    turn_to(h)
    for i in range(WIDEN_TRIES):
        d = read_distance()
        if d is None or d > reading + OBSTACLE_DEPTH:
            break
        turn_to(side_h)
        drive_straight(WIDEN_STEP, side_h)
        moved += WIDEN_STEP
        turn_to(h)

    pass_by = reading + SENSOR + OBSTACLE_DEPTH + TAIL_SWING + PASS_MARGIN
    to_go = ahead(px, py, h)
    if pass_by > to_go + WAYPOINT_TOLERANCE:
        drive_straight(to_go, h)
        return True

    drive_straight(pass_by, h)
    for i in range(CREEP_TRIES):
        turn_to(back_h)
        d = read_distance()
        if d is None or d > moved + FRONT:
            drive_straight(moved, back_h)
            break
        turn_to(h)
        drive_straight(CREEP_STEP, h)
    return False


def go_to(px, py):
    for i in range(GOTO_TRIES):
        if dist_to(px, py) < WAYPOINT_TOLERANCE:
            return
        h = bearing(px, py)
        turn_to(h)
        reading = drive_straight(dist_to(px, py), h, True)
        if reading is not None and avoid(h, reading, px, py):
            return


def main():
    for m in (left_motor, right_motor, intake_left, intake_right):
        m.set_stopping(BRAKE)
    catapult.set_stopping(HOLD)
    catapult.stop()

    brain.screen.print("Calibrating...")
    wait(200, MSEC)
    imu.calibrate()
    while imu.is_calibrating():
        wait(50, MSEC)
    imu.set_heading(0, DEGREES)
    left_motor.set_position(0, DEGREES)
    right_motor.set_position(0, DEGREES)

    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("CatapultBot NAV")
    brain.screen.set_cursor(2, 1)
    brain.screen.print("Press CHECK")
    brain.screen.set_cursor(3, 1)
    brain.screen.print("to start")
    while not brain.buttonCheck.pressing():
        wait(20, MSEC)
    wait(START_DELAY, MSEC)

    start = brain.timer.time(MSEC)
    for i in range(len(ROUTE)):
        go_to(ROUTE[i][0], ROUTE[i][1])
        print("waypoint", i + 1, round(x), round(y))
    turn_to(0)

    seconds = (brain.timer.time(MSEC) - start) / 1000
    print("done", round(seconds, 1), "s", obstacles, "obstacles")
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("MISSION COMPLETE")
    brain.screen.set_cursor(2, 1)
    brain.screen.print("Time %.1f s" % seconds)
    brain.screen.set_cursor(3, 1)
    brain.screen.print("Obstacles %d" % obstacles)
    brain.screen.set_cursor(4, 1)
    brain.screen.print("Odo err %.0f mm" % dist_to(START[0], START[1]))
    brain.screen.set_cursor(5, 1)
    brain.screen.print("Head err %.1f" % wrap(heading()))
    brain.play_sound(SoundType.TADA)


main()
