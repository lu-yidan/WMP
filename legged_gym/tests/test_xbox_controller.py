import importlib.util
from pathlib import Path
import struct

import numpy as np


MODULE_PATH = Path(__file__).parents[1] / "utils" / "xbox_controller.py"
SPEC = importlib.util.spec_from_file_location("xbox_controller", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
XboxJoystick = MODULE.XboxJoystick


def controller_without_device(**overrides):
    controller = XboxJoystick.__new__(XboxJoystick)
    controller._fd = None
    controller.device = "/dev/null"
    controller.max_forward = overrides.get("max_forward", 0.6)
    controller.max_lateral = overrides.get("max_lateral", 0.4)
    controller.max_yaw = overrides.get("max_yaw", 1.0)
    controller.deadzone = overrides.get("deadzone", 0.08)
    controller.require_deadman = overrides.get("require_deadman", True)
    controller.left_x_axis = 0
    controller.left_y_axis = 1
    controller.right_x_axis = 3
    controller.deadman_button = 5
    controller.quit_button = 6
    controller.axes = {}
    controller.buttons = {}
    controller._closed = True
    return controller


def event(value, event_type, number):
    return struct.pack("IhBB", 0, value, event_type, number)


def test_decode_strips_initialization_bit():
    value, event_type, number = XboxJoystick.decode_event(event(-32767, 0x82, 1))
    assert (value, event_type, number) == (-32767, 0x02, 1)


def test_deadman_and_axis_mapping():
    controller = controller_without_device()
    controller._consume(event(-32767, 0x02, 1))
    controller._consume(event(-16384, 0x02, 0))
    controller._consume(event(16384, 0x02, 3))

    command, _ = controller.poll()
    np.testing.assert_array_equal(command, np.zeros(3, dtype=np.float32))

    controller._consume(event(1, 0x01, 5))
    command, _ = controller.poll()
    np.testing.assert_allclose(
        command, [0.6, 0.2000061, -0.50001526], rtol=1e-5, atol=1e-6
    )


def test_deadzone_outputs_exact_zero():
    controller = controller_without_device(require_deadman=False)
    controller._consume(event(1000, 0x02, 1))
    command, _ = controller.poll()
    np.testing.assert_array_equal(command, np.zeros(3, dtype=np.float32))
