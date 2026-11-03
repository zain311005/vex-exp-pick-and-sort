import pytest

import bringup
import robot as robot_module
from settings import *
from geometry import distance_between, wrap_180
from main import run
from robot import Robot
from sim_hardware import SimHardware


def ready_robot(**options):
    """A simulated robot that has calibrated and sits at the start pose."""
    hw = SimHardware(**options)
    robot = Robot(hw)
    assert robot.calibrate()
    robot.reset_pose(START_X, START_Y, START_HEADING)
    return hw, robot


def motors_stopped(hw):
    return all(motor.command == 0 for motor in (hw.left, hw.right, hw.arm, hw.claw))


# ------------------------------------------------------------- motion
@pytest.mark.parametrize("target", [90.0, 180.0, 270.0, 45.0, 359.0, 0.0])
def test_turn_reaches_the_heading_on_the_spot(target):
    hw, robot = ready_robot()
    assert robot.turn_to(target) == "done"
    assert abs(wrap_180(hw.theta - target)) <= TURN_TOLERANCE_DEG + 1.0
    assert distance_between(hw.x, hw.y, START_X, START_Y) < 2.0


@pytest.mark.parametrize("distance", [300.0, 600.0, -300.0])
def test_drive_goes_the_distance_in_a_straight_line(distance):
    hw, robot = ready_robot()
    result, found = robot.drive(distance, START_HEADING)
    assert result == "done" and found is None
    assert hw.y - START_Y == pytest.approx(distance, abs=DRIVE_TOLERANCE_MM + 5.0)
    assert abs(hw.x - START_X) < 5.0
    assert robot.y == pytest.approx(hw.y, abs=1.0)


def test_original_path_comes_back_to_the_start(original_run):
    result, hw = original_run
    assert result == "done"
    assert distance_between(hw.x, hw.y, START_X, START_Y) <= 30.0
    assert abs(wrap_180(hw.theta - ORIGINAL_FINAL_HEADING)) <= 3.0
    assert hw.screen[0] == "PATH COMPLETE"
    assert hw.beeps == 1


# ------------------------------------------- known limits of dead reckoning
def test_wheel_slip_is_not_noticed_by_the_robot():
    """With 3 % wheel slip the robot believes it drove the full distance.

    It really falls short, and nothing on the robot can tell. This is the
    dead reckoning drift the README warns about.
    """
    hw, robot = ready_robot(slip_left=0.97, slip_right=0.97)
    assert robot.drive(1200.0, START_HEADING)[0] == "done"
    believed = robot.y - START_Y
    really = hw.y - START_Y
    assert believed == pytest.approx(1200.0, abs=DRIVE_TOLERANCE_MM + 5.0)
    assert believed - really > 25.0


def test_gyro_drift_makes_the_original_path_miss_the_start():
    """A gyro that drifts 3 degrees a minute turns every later segment.

    The boxes are left out so the run measures drift alone.
    """
    hw = SimHardware(imu_drift_dps=0.05, include_boxes=False)
    assert run(hw, "path", "original") == "done"
    assert distance_between(hw.x, hw.y, START_X, START_Y) > 30.0


# ------------------------------------------------------- failure paths
def test_drive_into_a_wall_times_out_and_stops():
    wall = (-300.0, 400.0, 300.0, 460.0)
    hw = SimHardware(obstacles=[wall])
    assert run(hw, "path", "original") == "timeout"
    assert hw.collisions >= 1
    assert hw.y + FRONT_MM <= wall[1] + 1.0
    assert motors_stopped(hw)
    assert hw.screen[0] == "PATH STOPPED"


@pytest.mark.parametrize("press_ms", [1000.0, 2500.0, 9000.0])
def test_stop_button_stops_everything(press_ms):
    # 1000 ms: gyro calibrating, 2500 ms: waiting for CHECK, 9000 ms: driving
    hw = SimHardware(stop_press_ms=press_ms)
    assert run(hw, "path", "original") == "stopped"
    assert motors_stopped(hw)
    assert hw.screen[0] == "STOPPED"
    x, y = hw.x, hw.y
    hw.sleep_ms(500)
    assert distance_between(x, y, hw.x, hw.y) < 20.0


def test_gyro_that_never_calibrates_ends_the_program():
    hw = SimHardware(imu_calibrates=False)
    assert run(hw, "path", "original") == "calibration_timeout"
    assert hw.time_ms() >= IMU_CALIBRATION_TIMEOUT_MS
    assert hw.left.degrees == 0 and hw.right.degrees == 0


def test_program_ends_if_check_is_never_pressed(monkeypatch):
    # a shorter wait than the real two minutes keeps the test quick
    monkeypatch.setattr(robot_module, "START_WAIT_TIMEOUT_MS", 5000)
    hw = SimHardware(start_press_ms=None)
    assert run(hw, "path", "original") == "no_start"
    assert hw.left.degrees == 0 and hw.right.degrees == 0


def test_bad_settings_end_the_program_before_anything_moves():
    hw = SimHardware()
    assert run(hw, "dance", "original") == "bad_setting"
    assert run(hw, "path", "nowhere") == "bad_setting"
    assert hw.time_ms() == 0


# ------------------------------------------------------ bring-up modes
def test_sensor_check_never_moves_a_motor():
    hw = SimHardware(stop_press_ms=20000.0)
    assert run(hw, "sensor_check") == "stopped"
    for motor in (hw.left, hw.right, hw.arm, hw.claw):
        assert motor.degrees == 0
    assert hw.light_pct == OPTICAL_LIGHT_PCT
    assert hw.screen_updates > 50


def test_sensor_check_ends_by_itself(monkeypatch):
    monkeypatch.setattr(bringup, "SENSOR_CHECK_TIMEOUT_MS", 3000)
    hw = SimHardware()
    assert run(hw, "sensor_check") == "timeout"
    assert hw.light_pct == 0


def test_motor_check_spins_each_motor_forward_one_at_a_time():
    hw = SimHardware()
    busy = []
    sleep = hw.sleep_ms

    def sleep_and_count(ms):
        busy.append(sum(1 for motor in (hw.left, hw.right, hw.arm, hw.claw)
                        if motor.command != 0))
        sleep(ms)

    hw.sleep_ms = sleep_and_count
    assert run(hw, "motor_check") == "done"
    assert max(busy) == 1
    assert hw.left.degrees > 0 and hw.right.degrees > 0
    assert hw.arm.degrees > 0 and hw.claw.degrees > 0
    assert motors_stopped(hw)
    assert hw.screen[0] == "MOTOR CHECK DONE"
    assert len(hw.console) == 4
