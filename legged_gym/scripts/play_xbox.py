#!/usr/bin/env python3
"""Play a WMP checkpoint in Isaac Gym with a Linux Xbox controller."""

import inspect
import os

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(os.path.dirname(currentdir))
os.sys.path.insert(0, parentdir)

import isaacgym  # noqa: F401  # must be imported before torch

from legged_gym.scripts import play as play_module
from legged_gym.utils import get_args
from legged_gym.utils.xbox_controller import XboxJoystick


def main():
    args = get_args(
        [
            {"name": "--xbox_device", "type": str, "default": "/dev/input/js0"},
            {"name": "--max_forward", "type": float, "default": 0.6},
            {"name": "--max_lateral", "type": float, "default": 0.0},
            {"name": "--max_yaw", "type": float, "default": 1.0},
            {"name": "--deadzone", "type": float, "default": 0.08},
            {"name": "--no_deadman", "action": "store_true", "default": False},
            {
                "name": "--play_duration",
                "type": float,
                "default": 0.0,
                "help": "Seconds to run; 0 runs until Back/viewer close",
            },
        ]
    )
    args.rl_device = args.sim_device
    if args.num_envs is None:
        args.num_envs = 1
    joystick = XboxJoystick(
        args.xbox_device,
        max_forward=args.max_forward,
        max_lateral=args.max_lateral,
        max_yaw=args.max_yaw,
        deadzone=args.deadzone,
        require_deadman=not args.no_deadman,
    )
    play_module.EXPORT_POLICY = False
    play_module.RECORD_FRAMES = False
    play_module.MOVE_CAMERA = not args.headless
    play_module.play(args, command_source=joystick, duration_s=args.play_duration)


if __name__ == "__main__":
    main()
