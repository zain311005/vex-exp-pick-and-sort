# mission.py
#
# RUN_MODE "sort": search along SELECTED_PATH, and whenever a ball turns up,
# fetch it, read its colour and drop it in that colour's box.
#
# The states, in the order they normally run:
#   FOLLOW_PATH  drive the path, watching the Distance Sensor while driving
#   APPROACH     drive slowly up to the ball, then creep until the Optical
#                Sensor in the claw sees it
#   GRAB         close the claw and check that it holds something
#   CLASSIFY     read the colour with the rule in colour.py
#   GO_TO_BOX    drive to a point in line with the box, raise the arm, and
#                move in until the ball is over the box
#   RELEASE      open the claw and check that the ball has gone
#   RETURN       back out to where it lined up, lower the arm, go back to
#                where the path was left and carry on along it
#
# Failure paths. Every state has a time limit, and:
#   - object not found (lost from view, too far, never in the claw): give up
#     on that spot, go back to the path, and ignore anything near the spot
#   - grip failed: open, back off and try again, GRAB_TRIES times in all,
#     then give up on the spot as above
#   - colour unknown: take it to REJECT_POSITION, or stop with a message
#     when UNKNOWN_COLOUR_ACTION is "stop"
#   - something in the way (nearer than OBSTACLE_STOP_MM and not a ball to
#     fetch): stop and ask for the way to be cleared, carry on after CHECK
#   - anything else, such as a turn that times out or a ball stuck in the
#     claw: stop every motor and say why on the screen
# The Brain's Left and Right buttons stop everything at any time.
#
# A detection only counts as a ball if the point where the Distance Sensor
# says the object is lies on the board. That is what stops the robot from
# driving at the boxes, which sit off the board. That point, like every
# position here, comes from dead reckoning (robot.py), which drifts: the
# further the robot has driven, the less exact the drops and the return to
# the path become.

from settings import *
from geometry import bearing, compass_vector, distance_between
from paths import get_path
from distance import DistanceFilter
from colour import NONE, UNKNOWN, read_colour
from arm import close_claw, holding_ball, home, move_arm, open_claw

STOPPED = "STOPPED"
DONE = "DONE"


def point_ahead(x, y, heading, distance):
    """The point distance mm from (x, y) along a compass heading."""
    dx, dy = compass_vector(heading)
    return x + distance * dx, y + distance * dy


def on_board(x, y, margin):
    """True if (x, y) is on the board, at least margin mm inside its edges."""
    return (BOARD_MIN_X + margin <= x <= BOARD_MAX_X - margin
            and BOARD_MIN_Y + margin <= y <= BOARD_MAX_Y - margin)


def box_heading(cx, cy):
    """Compass heading pointing from the board towards a box beside it."""
    sides = [(cx - BOARD_MAX_X, 90.0), (BOARD_MIN_X - cx, 270.0),
             (cy - BOARD_MAX_Y, 0.0), (BOARD_MIN_Y - cy, 180.0)]
    best = sides[0]
    for side in sides:
        if side[0] > best[0]:
            best = side
    return best[1]


def box_poses(cx, cy):
    """Where to line up, and where to stop, to drop a ball in the box at (cx, cy).

    Returns (line-up x, line-up y, drop x, drop y, heading). At the drop
    point, with the arm at ARM_DROP_DEG, the held ball's centre is
    DROP_INSET_MM inside the box's near edge.
    """
    heading = box_heading(cx, cy)
    back = BOX_SIZE_MM / 2.0 - DROP_INSET_MM + DROP_REACH_MM
    drop_x, drop_y = point_ahead(cx, cy, heading, -back)
    line_x, line_y = point_ahead(drop_x, drop_y, heading, -BOX_STAGING_MM)
    return line_x, line_y, drop_x, drop_y, heading


class Mission:
    def __init__(self, robot, references, gate, path_name):
        self.robot = robot
        self.hw = robot.hw
        self.references = references
        self.gate = gate
        self.segments = get_path(path_name)
        self.index = 0             # path segment being driven
        self.remaining = None      # mm left of that segment after a stop
        self.state = "HOME"
        self.colour = "-"
        self.message = ""
        self.resume = None         # (x, y, heading) where the path was left
        self.spot = None           # where the object being fetched seems to be
        self.target = None         # centre of the box being driven to
        self.line_up = None        # where the robot lined up for that box
        self.tries = 0
        self.bright_reads = 0
        self.last_seen_ms = 0
        self.reverse_to_path = False
        self.ignored = []          # spots given up on
        self.sorted = {}
        for name in COLOURS:
            self.sorted[name] = 0
        self.rejected = 0
        self.given_up = 0
        self.distance = DistanceFilter()
        self.start_ms = 0

    # ------------------------------------------------------------------ run
    def run(self):
        """Sort until the path is finished or something stops it.

        Returns "done", or "failed" with the reason in self.message.
        """
        robot = self.robot
        hw = self.hw
        self.start_ms = hw.time_ms()
        robot.screen_source = self.screen_lines
        robot.refresh_screen(True)
        problem = home(robot)
        if problem is not None:
            return self.result(self.stop_with(problem))
        if not move_arm(robot, ARM_SEARCH_DEG):
            return self.result(self.stop_with("arm timed out"))
        steps = {
            "FOLLOW_PATH": self.follow_path,
            "APPROACH": self.approach,
            "GRAB": self.grab,
            "CLASSIFY": self.classify,
            "GO_TO_BOX": self.go_to_box,
            "RELEASE": self.release,
            "RETURN": self.go_back,
        }
        self.state = "FOLLOW_PATH"
        while self.state in steps:
            if hw.time_ms() - self.start_ms > MISSION_TIMEOUT_MS:
                self.state = self.stop_with("took too long")
                break
            hw.log("state " + self.state)
            robot.refresh_screen(True)
            self.state = steps[self.state]()
        return self.result(self.state)

    def result(self, state):
        if state == DONE:
            self.finish()
            return "done"
        return "failed"

    # --------------------------------------------------------------- screen
    def screen_lines(self):
        return [self.state,
                "Colour " + self.colour,
                "Sorted %d Rej %d" % (self.sorted_total(), self.rejected),
                "X %.0f Y %.0f" % (self.robot.x, self.robot.y),
                "L/R = stop"]

    def sorted_total(self):
        total = 0
        for name in COLOURS:
            total += self.sorted[name]
        return total

    def stop_with(self, message):
        """Stop every motor and say why on the screen. Returns STOPPED."""
        self.hw.stop_all()
        self.message = message
        self.robot.screen_source = None
        self.hw.log("sort stopped in %s: %s" % (self.state, message))
        self.robot.set_lines(["SORT STOPPED", message, self.state, "Colour " + self.colour])
        return STOPPED

    def finish(self):
        hw = self.hw
        seconds = (hw.time_ms() - self.start_ms) / 1000.0
        counts = ""
        for name in COLOURS:
            counts += "%s%d " % (name[0].upper(), self.sorted[name])
        hw.log("sort done in %.0f s: %srejected %d, gave up on %d"
               % (seconds, counts, self.rejected, self.given_up))
        hw.log("Positions are dead reckoning estimates from the wheels and the "
               "gyro. They drift over a run.")
        self.robot.screen_source = None
        self.robot.set_lines(["SORT DONE", counts + "Rej %d" % self.rejected,
                              "Gave up %d" % self.given_up, "Time %.0f s" % seconds,
                              "Position drifts"])
        hw.beep()

    # ------------------------------------------------------------- watching
    def read_distance(self):
        self.distance.update(self.hw)
        return self.distance.distance()

    def near_ignored(self, spot):
        for old in self.ignored:
            if distance_between(spot[0], spot[1], old[0], old[1]) <= IGNORE_RADIUS_MM:
                return True
        return False

    def watch_path(self, remaining):
        """While following the path: ("ball", (x, y)) for something on the
        board worth fetching, ("blocked", mm) for anything else too near,
        otherwise None."""
        found = self.read_distance()
        if found is None or found > OBJECT_RANGE_MM:
            return None
        spot = point_ahead(self.robot.x, self.robot.y, self.hw.heading(),
                           SENSOR_OFFSET_MM + found)
        if on_board(spot[0], spot[1], BOARD_MARGIN_MM) and not self.near_ignored(spot):
            return ("ball", spot)
        if found <= OBSTACLE_STOP_MM:
            return ("blocked", found)
        return None

    def watch_blocked(self, remaining):
        """While driving anywhere else: ("blocked", mm) if anything is too near."""
        found = self.read_distance()
        if found is not None and found <= OBSTACLE_STOP_MM:
            return ("blocked", found)
        return None

    def wait_until_clear(self):
        """Ask for the way to be cleared. True once CHECK is pressed."""
        robot = self.robot
        robot.screen_source = None
        robot.set_lines(["BLOCKED", "Clear the way,", "then press CHECK", "L/R = stop"])
        self.hw.log("blocked in " + self.state)
        pressed = robot.wait_for_check(BLOCKED_TIMEOUT_MS)
        robot.screen_source = self.screen_lines
        if pressed:
            robot.pause(START_DELAY_MS)
        return pressed

    def navigate(self, x, y):
        """Turn to face (x, y) and drive straight to it, asking for the way to
        be cleared when something is in it. Returns None when there, or
        STOPPED. Nothing watches the sides while it turns on the spot."""
        robot = self.robot
        tries = 0
        while True:
            if distance_between(robot.x, robot.y, x, y) <= ARRIVE_TOLERANCE_MM:
                return None
            if robot.turn_to(bearing(robot.x, robot.y, x, y)) == "timeout":
                return self.stop_with("turn timed out")
            self.distance.reset()
            length = distance_between(robot.x, robot.y, x, y)
            result, found = robot.drive(length, robot.target_heading, self.watch_blocked)
            if result == "done":
                return None
            if result == "timeout":
                return self.stop_with("drive timed out")
            if result == "stuck":
                return self.stop_with("drive blocked")
            tries += 1
            if tries >= NAV_TRIES or not self.wait_until_clear():
                return self.stop_with("way blocked")

    # --------------------------------------------------------------- states
    def follow_path(self):
        robot = self.robot
        while self.index < len(self.segments):
            kind, value = self.segments[self.index]
            if kind == "turn":
                if robot.turn_to(value) == "timeout":
                    return self.stop_with("turn timed out")
                self.index += 1
                continue
            if self.remaining is None:
                length = value
            else:
                length = self.remaining
            self.distance.reset()
            result, found = robot.drive(length, robot.target_heading, self.watch_path)
            if result == "timeout":
                return self.stop_with("drive timed out")
            if result == "stuck":
                return self.stop_with("drive blocked")
            if result == "object":
                self.remaining = length - robot.last_driven_mm
                if found[0] == "ball":
                    self.resume = (robot.x, robot.y, robot.target_heading)
                    self.spot = found[1]
                    self.tries = 0
                    self.hw.log("object ahead at %.0f, %.0f" % self.spot)
                    return "APPROACH"
                if not self.wait_until_clear():
                    return self.stop_with("path blocked")
                continue
            self.remaining = None
            self.index += 1
        return DONE

    def approach(self):
        robot = self.robot
        heading = robot.target_heading
        self.distance.reset()
        self.last_seen_ms = self.hw.time_ms()
        outcome = robot.drive_until(APPROACH_PCT, heading, self.close_enough,
                                    APPROACH_MAX_MM, APPROACH_TIMEOUT_MS)
        if outcome != "close":
            return self.give_up("approach " + outcome)
        self.bright_reads = 0
        outcome = robot.drive_until(CREEP_PCT, heading, self.ball_in_claw,
                                    CREEP_MAX_MM, CREEP_TIMEOUT_MS)
        if outcome != "in claw":
            return self.give_up("not in claw: " + outcome)
        return "GRAB"

    def close_enough(self):
        found = self.read_distance()
        now = self.hw.time_ms()
        if found is not None:
            self.last_seen_ms = now
            if found <= APPROACH_STOP_MM:
                return "close"
        elif now - self.last_seen_ms > OBJECT_LOST_MS:
            return "lost"
        return None

    def ball_in_claw(self):
        if self.hw.optical_brightness() >= self.gate:
            self.bright_reads += 1
        else:
            self.bright_reads = 0
        if self.bright_reads >= IN_CLAW_READS:
            return "in claw"
        return None

    def grab(self):
        robot = self.robot
        if not move_arm(robot, ARM_GRAB_DEG):
            return self.stop_with("arm timed out")
        stopped_at = close_claw(robot)
        holding = holding_ball(stopped_at, self.hw.optical_brightness(), self.gate)
        if holding:
            self.hw.log("grab: claw stopped at %.0f degrees, holding a ball" % stopped_at)
        else:
            self.hw.log("grab: no ball in the claw")
            return self.grab_failed()
        if not move_arm(robot, ARM_CARRY_DEG):
            return self.stop_with("arm timed out")
        return "CLASSIFY"

    def grab_failed(self):
        """Open up and try again, or give up on the spot after GRAB_TRIES."""
        robot = self.robot
        if not open_claw(robot):
            return self.stop_with("claw timed out")
        if not move_arm(robot, ARM_SEARCH_DEG):
            return self.stop_with("arm timed out")
        self.tries += 1
        if self.tries >= GRAB_TRIES:
            return self.give_up("grip failed")
        if robot.drive(-GRAB_RETRY_BACKUP_MM, robot.target_heading)[0] != "done":
            return self.stop_with("backup timed out")
        return "APPROACH"

    def give_up(self, reason):
        """Leave this object alone from now on and go back to the path."""
        self.hw.log("giving up on the object at %.0f, %.0f: %s"
                    % (self.spot[0], self.spot[1], reason))
        self.ignored.append(self.spot)
        self.given_up += 1
        self.colour = "-"
        self.reverse_to_path = True
        return "RETURN"

    def classify(self):
        answer, labels = read_colour(self.robot, self.references, self.gate)
        self.hw.log("colour %s from %s" % (answer, " ".join(labels)))
        if answer == NONE:
            return self.grab_failed()   # the ball slipped out
        self.colour = answer
        if answer != UNKNOWN:
            self.target = BOX_POSITIONS[answer]
        elif UNKNOWN_COLOUR_ACTION == "stop":
            return self.stop_with("unknown colour")
        else:
            self.target = REJECT_POSITION
        return "GO_TO_BOX"

    def go_to_box(self):
        robot = self.robot
        line_x, line_y, drop_x, drop_y, heading = box_poses(self.target[0], self.target[1])
        self.line_up = (line_x, line_y)
        stopped = self.navigate(line_x, line_y)
        if stopped is not None:
            return stopped
        if robot.turn_to(heading) == "timeout":
            return self.stop_with("turn timed out")
        if not move_arm(robot, ARM_DROP_DEG):
            return self.stop_with("arm timed out")
        if robot.drive(distance_between(robot.x, robot.y, drop_x, drop_y), heading)[0] != "done":
            return self.stop_with("box not reached")
        return "RELEASE"

    def release(self):
        robot = self.robot
        for attempt in range(RELEASE_TRIES):
            if not open_claw(robot):
                return self.stop_with("claw timed out")
            robot.pause(RELEASE_WAIT_MS)
            if self.hw.optical_brightness() < self.gate:
                if self.target == REJECT_POSITION:
                    self.rejected += 1
                else:
                    self.sorted[self.colour] += 1
                # the claw is empty, but nothing can tell whether the ball
                # landed in the box or next to it
                self.hw.log("let go of the %s ball" % self.colour)
                self.reverse_to_path = False
                return "RETURN"
            close_claw(robot)
        return self.stop_with("ball stuck")

    def go_back(self):
        robot = self.robot
        x, y, heading = self.resume
        if self.reverse_to_path:
            # straight back along the line the approach came in on
            back = distance_between(robot.x, robot.y, x, y)
            result = robot.drive(-back, heading)[0]
        else:
            # straight back out from the box to where it lined up, so the
            # claw is clear of the box before the arm comes down
            back = distance_between(robot.x, robot.y, self.line_up[0], self.line_up[1])
            result = robot.drive(-back, robot.target_heading)[0]
        if result != "done":
            return self.stop_with("backup timed out")
        if not move_arm(robot, ARM_SEARCH_DEG):
            return self.stop_with("arm timed out")
        stopped = self.navigate(x, y)
        if stopped is not None:
            return stopped
        if robot.turn_to(heading) == "timeout":
            return self.stop_with("turn timed out")
        self.colour = "-"
        return "FOLLOW_PATH"
